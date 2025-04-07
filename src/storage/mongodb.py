#!/usr/bin/env python3
"""
MongoDB storage connector for Fama AI.

This module provides a specialized connector for MongoDB storage
using the Agno framework's storage capabilities.
"""
import logging
from typing import Optional, Dict, Any

from agno.storage.agent.mongodb import MongoDbAgentStorage

logger = logging.getLogger(__name__)

def create_mongodb_storage(
    collection_name: str,
    db_url: str,
    db_name: str = "agno",
    **kwargs
) -> MongoDbAgentStorage:
    """
    Create a MongoDB storage backend for agents.
    
    Based on Agno documentation, the MongoDbAgentStorage requires a db_url
    connection string in the format: "mongodb://user:pass@host:port/db"
    
    Args:
        collection_name: Name of the collection to store agent sessions
        db_url: MongoDB connection URL (e.g., "mongodb://ai:ai@localhost:27017/agno")
        db_name: Database name (default: "agno")
        **kwargs: Additional keyword arguments for MongoDbAgentStorage
        
    Returns:
        Configured MongoDbAgentStorage instance
        
    Raises:
        ValueError: If db_url is not provided or in invalid format
    """
    if not db_url:
        raise ValueError("db_url must be provided for MongoDB storage")
    
    # Validate MongoDB connection string format
    if not db_url.startswith("mongodb://"):
        raise ValueError(
            "MongoDB connection string must start with 'mongodb://'"
        )
    
    logger.info(f"Initializing MongoDB storage with collection_name: {collection_name}, db_name: {db_name}")
    
    # Create MongoDB storage backend
    return MongoDbAgentStorage(
        collection_name=collection_name,
        db_url=db_url,
        db_name=db_name,
        **kwargs
    ) 