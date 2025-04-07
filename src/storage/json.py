#!/usr/bin/env python3
"""
JSON storage connector for Fama AI.

This module provides a specialized connector for JSON file-based storage
using the Agno framework's storage capabilities.
"""
import logging
import os
import json
from typing import Optional, Dict, Any

from agno.storage.agent.json import JsonAgentStorage
from src.storage.factory import StorageError

logger = logging.getLogger(__name__)

def create_json_storage(
    dir_path: str,
    create_dir_if_not_exists: bool = True,
    **kwargs
) -> JsonAgentStorage:
    """
    Create a JSON file-based storage for agent state.
    
    Based on Agno documentation, JsonAgentStorage stores agent sessions as 
    individual JSON files within a directory.
    
    Args:
        dir_path: Path to the directory where JSON files will be stored
        create_dir_if_not_exists: Whether to create the directory if it doesn't exist (default: True)
        **kwargs: Additional keyword arguments for JsonAgentStorage
        
    Returns:
        Configured JsonAgentStorage instance
        
    Raises:
        StorageError: If directory path is invalid or cannot be created
    """
    try:
        if not dir_path:
            raise StorageError("dir_path is required for JSON storage")
        
        # Create the directory if it doesn't exist and we're allowed to create it
        if not os.path.exists(dir_path):
            if create_dir_if_not_exists:
                logger.info(f"Creating directory for JSON storage: {dir_path}")
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    raise StorageError(f"Failed to create directory for JSON storage: {str(e)}")
            else:
                raise StorageError(f"Directory for JSON storage does not exist: {dir_path}")
        
        # Check if the path is actually a directory
        if not os.path.isdir(dir_path):
            raise StorageError(f"Path is not a directory: {dir_path}")
        
        # Log initialization
        logger.info(f"Initializing JSON storage in directory: {dir_path}")
        
        # Create JSON storage backend
        return JsonAgentStorage(dir_path=dir_path, **kwargs)
    except StorageError:
        # Re-raise StorageError instances as is
        raise
    except Exception as e:
        # Wrap other exceptions
        logger.error(f"Failed to create JSON storage: {str(e)}")
        raise StorageError(f"Failed to create JSON storage: {str(e)}") 