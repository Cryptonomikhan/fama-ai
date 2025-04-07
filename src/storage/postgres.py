#!/usr/bin/env python3
"""
PostgreSQL storage connector for Fama AI.

This module provides a specialized connector for PostgreSQL storage
using the Agno framework's storage capabilities.
"""
import logging
from typing import Optional, Dict, Any

from agno.storage.agent.postgres import PostgresAgentStorage

logger = logging.getLogger(__name__)

def create_postgres_storage(
    table_name: str,
    db_url: str,
    schema: str = "ai",
    schema_version: int = 1,
    auto_upgrade_schema: bool = False,
    **kwargs
) -> PostgresAgentStorage:
    """
    Create a PostgreSQL storage backend for agents.
    
    Based on Agno documentation, the PostgresAgentStorage requires a db_url
    connection string in the format: "postgresql+psycopg://user:pass@host:port/db"
    
    Args:
        table_name: Name of the table to store agent sessions
        db_url: PostgreSQL connection URL (e.g., "postgresql+psycopg://ai:ai@localhost:5532/ai")
        schema: Database schema name (default: "ai")
        schema_version: Version of the schema to use (default: 1)
        auto_upgrade_schema: Whether to automatically upgrade schema (default: False)
        **kwargs: Additional keyword arguments for PostgresAgentStorage
        
    Returns:
        Configured PostgresAgentStorage instance
        
    Raises:
        ValueError: If db_url is not provided or in invalid format
    """
    if not db_url:
        raise ValueError("db_url must be provided for PostgreSQL storage")
    
    # Validate PostgreSQL connection string format
    if not (db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg://")):
        raise ValueError(
            "PostgreSQL connection string must start with 'postgresql://' or 'postgresql+psycopg://'"
        )
    
    logger.info(f"Initializing PostgreSQL storage with table_name: {table_name}, schema: {schema}")
    
    # Create PostgreSQL storage backend
    return PostgresAgentStorage(
        table_name=table_name,
        db_url=db_url,
        schema=schema,
        schema_version=schema_version,
        auto_upgrade_schema=auto_upgrade_schema,
        **kwargs
    ) 