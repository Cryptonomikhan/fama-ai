#!/usr/bin/env python3
"""
SQLite storage connector for Fama AI.

This module provides a specialized connector for SQLite storage
using the Agno framework's storage capabilities.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from agno.storage.agent.sqlite import SqliteAgentStorage

logger = logging.getLogger(__name__)

def create_sqlite_storage(
    table_name: str,
    db_file: Optional[str] = None,
    db_url: Optional[str] = None,
    schema: str = "ai",
    auto_upgrade_schema: bool = False,
    **kwargs
) -> SqliteAgentStorage:
    """
    Create a SQLite storage backend for agents.
    
    Based on Agno documentation, the SqliteAgentStorage accepts either a db_file path
    or a db_url connection string.
    
    Args:
        table_name: Name of the table to store agent sessions
        db_file: Path to SQLite database file (e.g., "data.db" or "tmp/data.db")
        db_url: SQLite connection URL (e.g., "sqlite:///data.db")
        schema: Database schema name (default: "ai")
        auto_upgrade_schema: Whether to automatically upgrade schema (default: False)
        **kwargs: Additional keyword arguments for SqliteAgentStorage
        
    Returns:
        Configured SqliteAgentStorage instance
        
    Raises:
        ValueError: If neither db_file nor db_url is provided
    """
    if not db_file and not db_url:
        raise ValueError("Either db_file or db_url must be provided for SQLite storage")
    
    logger.info(f"Initializing SQLite storage with table_name: {table_name}")
    
    # Create the parent directory if using db_file and it doesn't exist
    if db_file:
        db_path = Path(db_file)
        if not db_path.parent.exists():
            logger.info(f"Creating directory for SQLite database: {db_path.parent}")
            os.makedirs(db_path.parent, exist_ok=True)
        
        logger.info(f"Using SQLite database file: {db_file}")
        return SqliteAgentStorage(
            table_name=table_name,
            db_file=db_file,
            schema=schema,
            auto_upgrade_schema=auto_upgrade_schema,
            **kwargs
        )
    
    # Using db_url
    logger.info(f"Using SQLite database URL: {db_url}")
    return SqliteAgentStorage(
        table_name=table_name,
        db_url=db_url,
        schema=schema,
        auto_upgrade_schema=auto_upgrade_schema,
        **kwargs
    ) 