#!/usr/bin/env python3
"""
Storage connection utilities for Fama AI.

This module provides utilities for testing storage connections and monitoring
connection health for various storage backends.
"""
import logging
import time
import traceback
from typing import Dict, Any, Optional, Callable, Union, List
from functools import wraps

from src.storage.factory import StorageError, AgentStorage
from agno.utils.log import logger

from src.storage.factory import StorageConnectionError

# Set up logging
logger = logging.getLogger(__name__)

def with_connection_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exponential_backoff: bool = True,
    error_types: List[type] = None
):
    """
    Decorator for retrying operations on connection errors.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Base delay between retries in seconds (default: 1.0)
        exponential_backoff: Whether to use exponential backoff for retries (default: True)
        error_types: List of exception types to catch and retry (default: connection-related errors)
        
    Returns:
        Decorated function with connection retry logic
    """
    if error_types is None:
        # Default to common connection error types
        error_types = [StorageConnectionError, ConnectionError, TimeoutError]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for retry in range(max_retries + 1):  # +1 because first attempt is not a retry
                try:
                    if retry > 0:
                        delay = retry_delay
                        if exponential_backoff:
                            delay = retry_delay * (2 ** (retry - 1))  # Exponential backoff
                        
                        logger.info(f"Retry {retry}/{max_retries} for {func.__name__} after {delay:.2f}s delay")
                        time.sleep(delay)
                    
                    return func(*args, **kwargs)
                    
                except tuple(error_types) as e:
                    last_error = e
                    logger.warning(
                        f"Connection error in {func.__name__} (attempt {retry+1}/{max_retries+1}): {str(e)}",
                        extra={"traceback": traceback.format_exc()}
                    )
                    
                    if retry == max_retries:
                        # This was the last attempt
                        break
            
            # If we got here, all attempts failed
            error_message = f"All {max_retries+1} attempts failed for {func.__name__}"
            logger.error(error_message)
            
            if last_error:
                error_details = {
                    "function": func.__name__,
                    "attempts": max_retries + 1,
                    "original_error": str(last_error)
                }
                
                if isinstance(last_error, StorageConnectionError):
                    raise last_error  # Re-raise with original details
                else:
                    # Wrap in our storage connection error
                    raise StorageConnectionError(
                        f"{error_message}: {str(last_error)}",
                        error_details
                    ) from last_error
            
            # This should never happen, but just in case
            raise StorageConnectionError(
                f"{error_message} for unknown reasons",
                {"function": func.__name__}
            )
            
        return wrapper
    return decorator


def test_storage_connection(
    storage: AgentStorage,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Test a storage connection by attempting basic operations.
    
    Args:
        storage: The storage instance to test
        timeout: Timeout in seconds for the connection test
        
    Returns:
        Dictionary with connection status information
        
    Raises:
        StorageConnectionError: If the connection test fails
    """
    start_time = time.time()
    result = {
        "success": False,
        "storage_type": type(storage).__name__,
        "latency_ms": 0,
        "operations_tested": [],
    }
    
    try:
        # Try to use the test_connection method if available
        if hasattr(storage, 'test_connection'):
            logger.debug(f"Testing connection using test_connection method")
            storage.test_connection()
            result["operations_tested"].append("test_connection")
        
        # Try to list sessions as a basic read operation
        elif hasattr(storage, 'list_sessions'):
            logger.debug(f"Testing connection using list_sessions method")
            storage.list_sessions()
            result["operations_tested"].append("list_sessions")
        
        # Try to create and delete a test session
        else:
            logger.debug(f"Testing connection using create/delete session")
            test_session_id = f"connection_test_{int(time.time())}"
            test_user_id = "connection_test_user"
            
            # Create a test session
            storage.save_session(test_session_id, test_user_id, [])
            result["operations_tested"].append("save_session")
            
            # Load the test session
            storage.load_session(test_session_id)
            result["operations_tested"].append("load_session")
            
            # Clean up the test session
            storage.delete_session(test_session_id)
            result["operations_tested"].append("delete_session")
        
        # Calculate latency
        latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        result["latency_ms"] = round(latency, 2)
        result["success"] = True
        
        logger.info(
            f"Storage connection test successful",
            extra={"connection_test": result}
        )
        
        return result
        
    except Exception as e:
        # Calculate latency even for failures
        latency = (time.time() - start_time) * 1000
        result["latency_ms"] = round(latency, 2)
        result["error"] = str(e)
        
        logger.error(
            f"Storage connection test failed: {str(e)}",
            extra={"connection_test": result, "traceback": traceback.format_exc()}
        )
        
        raise StorageConnectionError(
            f"Storage connection test failed: {str(e)}",
            {"test_result": result}
        ) from e


@with_connection_retry(max_retries=3, retry_delay=1.0)
def ensure_storage_healthy(
    storage: AgentStorage,
    perform_write_test: bool = False
) -> bool:
    """
    Ensure that a storage connection is healthy, with retries.
    
    Args:
        storage: The storage instance to check
        perform_write_test: Whether to perform a write test (more thorough but slower)
        
    Returns:
        True if the connection is healthy, raises an exception otherwise
    """
    test_result = test_storage_connection(storage)
    
    # For more thorough testing, perform a write test if requested
    if perform_write_test and "save_session" not in test_result["operations_tested"]:
        logger.info("Performing additional write test for storage connection")
        
        # Create a temporary test session
        test_session_id = f"health_check_{int(time.time())}"
        test_user_id = "health_check_user"
        test_messages = [{"role": "system", "content": "Health check message"}]
        
        try:
            # Test write
            storage.save_session(test_session_id, test_user_id, test_messages)
            
            # Test read
            loaded_messages = storage.load_session(test_session_id)
            if not loaded_messages or loaded_messages != test_messages:
                raise StorageConnectionError(
                    "Storage health check failed: Data integrity issue detected",
                    {
                        "saved": test_messages,
                        "loaded": loaded_messages
                    }
                )
            
            # Clean up
            storage.delete_session(test_session_id)
            
            logger.info("Storage write test successful")
            
        except Exception as e:
            logger.error(f"Storage write test failed: {str(e)}")
            raise StorageConnectionError(
                f"Storage health check failed during write test: {str(e)}",
                {"original_error": str(e)}
            ) from e
    
    return True


def monitor_connection_health(
    storage: AgentStorage,
    interval: float = 60.0,
    max_failures: int = 3,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> None:
    """
    Start a background thread to monitor connection health periodically.
    
    Args:
        storage: The storage instance to monitor
        interval: Time between health checks in seconds
        max_failures: Maximum consecutive failures before raising an alarm
        callback: Optional callback function to call with health check results
        
    Note:
        This function starts a background thread that runs indefinitely.
        It should be called only once per storage instance.
    """
    import threading
    
    def monitor_thread():
        consecutive_failures = 0
        
        while True:
            try:
                # Perform health check
                test_result = test_storage_connection(storage)
                consecutive_failures = 0
                
                # Call callback if provided
                if callback:
                    callback(test_result)
                
            except Exception as e:
                consecutive_failures += 1
                logger.warning(
                    f"Storage health check failed ({consecutive_failures}/{max_failures}): {str(e)}",
                    extra={"error": str(e)}
                )
                
                # Call callback with error information if provided
                if callback:
                    callback({
                        "success": False,
                        "storage_type": type(storage).__name__,
                        "error": str(e),
                        "consecutive_failures": consecutive_failures
                    })
                
                # If we've reached the maximum consecutive failures, log a critical error
                if consecutive_failures >= max_failures:
                    logger.critical(
                        f"Storage connection unhealthy: {consecutive_failures} consecutive failures",
                        extra={"storage_type": type(storage).__name__, "error": str(e)}
                    )
            
            # Sleep until the next check
            time.sleep(interval)
    
    # Start the monitor thread
    thread = threading.Thread(target=monitor_thread, daemon=True)
    thread.start()
    
    logger.info(
        f"Started storage health monitoring thread",
        extra={
            "storage_type": type(storage).__name__,
            "check_interval": interval,
            "max_failures": max_failures
        }
    ) 