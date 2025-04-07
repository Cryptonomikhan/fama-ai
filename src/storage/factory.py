#!/usr/bin/env python3
"""
Storage factory for Fama AI.

This module provides a factory for creating storage backends with different 
database types for persistent agent state.
"""
import os
import logging
import time
from typing import Dict, Any, Optional, Union, List
from functools import wraps
import traceback
import inspect

# Import Agno storage backends based on documentation
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.storage.agent.mongodb import MongoDbAgentStorage
from agno.storage.agent.dynamodb import DynamoDbAgentStorage
from agno.storage.agent.json import JsonAgentStorage
from agno.storage.agent.yaml import YamlAgentStorage
from agno.utils.log import logger

from src.storage.dynamodb import create_dynamodb_storage
from src.storage.postgres import create_postgres_storage
from src.storage.mongodb import create_mongodb_storage
from src.storage.sqlite import create_sqlite_storage
from src.storage.json import create_json_storage
from src.storage.yaml import create_yaml_storage

# Set up logging
logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Base exception for storage-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class StorageConnectionError(StorageError):
    """Exception raised for storage connection errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.connection_info = details or {}


def log_storage_operation(operation_name: str):
    """
    Decorator for logging storage operations with structured error handling.
    
    Args:
        operation_name: Name of the operation being performed
        
    Returns:
        Decorated function with enhanced logging and error handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique operation ID
            operation_id = f"{operation_name}_{int(time.time()*1000)}"
            
            # Extract relevant parameters for logging (exclude sensitive information)
            log_params = {
                k: v for k, v in kwargs.items() 
                if k not in ['storage_connection'] and not isinstance(v, (dict, list))
            }
            
            # Get calling function info for better context
            caller_frame = inspect.currentframe().f_back
            caller_info = ""
            if caller_frame:
                caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            
            logger.info(f"Starting {operation_name} operation", 
                       extra={'storage_operation': operation_name, 'storage_id': operation_id, 
                              'params': str(log_params), 'caller': caller_info})
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation_name} operation successfully", 
                           extra={'storage_operation': operation_name, 'storage_id': operation_id})
                return result
            except StorageError as e:
                # Log specific storage errors with their structured details
                error_details = {'error_type': e.__class__.__name__, 'details': e.details}
                logger.error(f"{operation_name} operation failed: {e.message}", 
                            extra={'storage_operation': operation_name, 'storage_id': operation_id, 
                                   'error': error_details})
                raise
            except Exception as e:
                # Capture and structure unknown errors
                error_info = {
                    'exception_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
                logger.error(f"{operation_name} operation failed with unexpected error: {str(e)}", 
                            extra={'storage_operation': operation_name, 'storage_id': operation_id, 
                                   'error': error_info})
                
                # Convert to appropriate Storage error type for consistent handling
                raise StorageConnectionError(f"Storage operation failed: {str(e)}", 
                                           {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
        
        return wrapper
    return decorator


# Create a mapping of storage types to their implementation classes
STORAGE_BACKENDS = {
    "postgres": PostgresAgentStorage,
    "sqlite": SqliteAgentStorage,
    "mongodb": MongoDbAgentStorage,
    "dynamodb": DynamoDbAgentStorage,
    "json": JsonAgentStorage,
    "yaml": YamlAgentStorage,
}


# Type alias for storage classes
AgentStorage = Union[
    PostgresAgentStorage,
    SqliteAgentStorage,
    MongoDbAgentStorage,
    DynamoDbAgentStorage,
    JsonAgentStorage,
    YamlAgentStorage
]


@log_storage_operation("storage_initialization")
def initialize_storage(
    storage_type: str,
    storage_connection: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    table_name: str = "agent_sessions",
    **kwargs: Any
) -> Optional[AgentStorage]:
    """
    Initialize a storage backend for an agent or team based on the provided parameters.
    
    Args:
        storage_type: Type of storage backend to initialize (sqlite, postgres, mongodb, etc.)
        storage_connection: Connection string or configuration for the storage backend
        session_id: Optional session ID for resuming conversations
        user_id: Optional user ID for personalization
        table_name: Name of the table/collection to use for storage
        **kwargs: Additional keyword arguments for specific storage backends
    
    Returns:
        Initialized storage backend object or None if initialization fails
    
    Raises:
        StorageConnectionError: If connection to the storage backend fails
        StorageError: If any other error occurs during storage initialization
    """
    logger.info(f"Initializing {storage_type} storage with table '{table_name}'")
    
    if storage_type not in STORAGE_BACKENDS:
        supported_backends = ", ".join(STORAGE_BACKENDS.keys())
        raise StorageError(
            f"Unsupported storage type: {storage_type}",
            {"supported_types": supported_backends}
        )
    
    storage_class = STORAGE_BACKENDS[storage_type]
    
    # Connection timeout handling
    connection_timeout = kwargs.get("connection_timeout", 10)  # Default 10 seconds timeout
    max_retries = kwargs.get("max_retries", 3)  # Default 3 retries
    retry_delay = kwargs.get("retry_delay", 1)  # Default 1 second between retries
    
    # Connection validation flag
    validate_connection = kwargs.get("validate_connection", True)
    
    # Monitor connection health
    monitor_connection = kwargs.get("monitor_connection", False)
    health_check_interval = kwargs.get("health_check_interval", 60)
    
    last_error = None
    for retry in range(max_retries):
        try:
            if retry > 0:
                logger.info(f"Retry {retry}/{max_retries} connecting to {storage_type} storage")
                time.sleep(retry_delay)
            
            if storage_type == "sqlite":
                if storage_connection.startswith("sqlite:///"):
                    db_url = storage_connection
                    storage = create_sqlite_storage(table_name=table_name, db_url=db_url)
                else:
                    # Assume it's a file path
                    db_file = storage_connection
                    storage = create_sqlite_storage(table_name=table_name, db_file=db_file)
                    
            elif storage_type == "postgres":
                storage = create_postgres_storage(table_name=table_name, db_url=storage_connection)
                
            elif storage_type == "mongodb":
                storage = create_mongodb_storage(collection_name=table_name, db_url=storage_connection)
                
            elif storage_type == "dynamodb":
                import json
                config = json.loads(storage_connection) if isinstance(storage_connection, str) else storage_connection
                storage = create_dynamodb_storage(
                    table_name=table_name,
                    region_name=config.get("region_name"),
                    aws_access_key_id=config.get("aws_access_key_id"),
                    aws_secret_access_key=config.get("aws_secret_access_key"),
                    endpoint_url=config.get("endpoint_url"),
                    create_table_if_not_exists=config.get("create_table_if_not_exists", True)
                )
            
            elif storage_type == "json":
                storage = create_json_storage(
                    dir_path=storage_connection,
                    create_dir_if_not_exists=kwargs.get("create_dir_if_not_exists", True)
                )
                
            elif storage_type == "yaml":
                storage = create_yaml_storage(
                    dir_path=storage_connection,
                    create_dir_if_not_exists=kwargs.get("create_dir_if_not_exists", True)
                )
            
            # Validate the connection if required
            if validate_connection:
                # Import connection validation utilities
                from src.storage.connection import test_storage_connection
                
                # Test the connection by performing a simple operation
                # This will raise an exception if the connection fails
                test_result = test_storage_connection(storage, timeout=connection_timeout)
                
                # Log the test result
                logger.info(f"Connection test successful for {storage_type} storage",
                           extra={"test_result": test_result})
            
            # Start connection health monitoring if requested
            if monitor_connection:
                from src.storage.connection import monitor_connection_health
                
                # Start a background thread to monitor connection health
                monitor_connection_health(
                    storage=storage,
                    interval=health_check_interval,
                    max_failures=3,
                    callback=None  # No callback for now
                )
                
                logger.info(f"Started connection health monitoring for {storage_type} storage",
                           extra={"interval": health_check_interval})
            
            # Log storage initialization success with details
            storage_info = {
                "type": storage_type,
                "table_name": table_name,
                "session_id": session_id,
                "user_id": user_id,
                "connection_validated": validate_connection,
                "health_monitoring": monitor_connection
            }
            
            logger.info(f"Storage backend initialized successfully", 
                       extra={"storage_info": storage_info})
            return storage
            
        except (StorageConnectionError) as e:
            # Specific handling for connection errors that may be retried
            last_error = e
            logger.warning(
                f"Connection error on attempt {retry+1}/{max_retries} for {storage_type} storage: {e.message}",
                extra={"error_details": e.details if hasattr(e, 'details') else {}}
            )
            if retry == max_retries - 1:
                # This was the last retry
                break
        except Exception as e:
            # Catch and wrap any other exceptions during storage initialization
            error_message = f"Failed to initialize {storage_type} storage: {str(e)}"
            logger.error(error_message)
            
            # For non-connection errors, don't retry
            if "connection" not in str(e).lower() and "timeout" not in str(e).lower():
                raise StorageError(
                    error_message,
                    {
                        "storage_type": storage_type,
                        "original_error": str(e),
                        "traceback": traceback.format_exc()
                    }
                ) from e
            
            # For connection errors, store for retry
            last_error = e
            logger.warning(
                f"Possible connection error on attempt {retry+1}/{max_retries}: {str(e)}",
                extra={"traceback": traceback.format_exc()}
            )
            if retry == max_retries - 1:
                # This was the last retry
                break
    
    # If we got here, all retries failed
    if last_error:
        error_details = {
            "storage_type": storage_type,
            "retries": max_retries,
            "original_error": str(last_error),
            "traceback": traceback.format_exc()
        }
        logger.error(f"All {max_retries} connection attempts failed for {storage_type} storage")
        raise StorageConnectionError(
            f"Could not connect to {storage_type} storage after {max_retries} attempts: {str(last_error)}",
            error_details
        ) from last_error
    
    # This should never happen, but just in case
    raise StorageConnectionError(
        f"Failed to initialize {storage_type} storage for unknown reasons",
        {"storage_type": storage_type}
    ) 