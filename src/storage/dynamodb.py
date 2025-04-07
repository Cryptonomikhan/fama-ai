#!/usr/bin/env python3
"""
DynamoDB storage connector for Fama AI.

This module provides a specialized connector for DynamoDB storage
using the Agno framework's storage capabilities.
"""
import logging
import json
from typing import Optional, Dict, Any

from agno.storage.dynamodb import DynamoDbStorage

logger = logging.getLogger(__name__)

def create_dynamodb_storage(
    table_name: str,
    region_name: str,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    create_table_if_not_exists: bool = True,
    **kwargs
) -> DynamoDbStorage:
    """
    Create a DynamoDB storage backend for agents.
    
    Based on Agno documentation, the DynamoDbAgentStorage requires AWS credentials
    and region information to connect to DynamoDB.
    
    Args:
        table_name: Name of the DynamoDB table to store agent sessions
        region_name: AWS region where the DynamoDB table is located
        aws_access_key_id: Optional AWS access key ID
        aws_secret_access_key: Optional AWS secret access key
        endpoint_url: Optional endpoint URL for DynamoDB (useful for local development)
        create_table_if_not_exists: Whether to create the table if it doesn't exist (default: True)
        **kwargs: Additional keyword arguments for DynamoDbAgentStorage
        
    Returns:
        Configured DynamoDbAgentStorage instance
        
    Raises:
        ValueError: If required parameters are missing
    """
    if not region_name:
        raise ValueError("region_name must be provided for DynamoDB storage")
    
    # Log initialization with sensitive info redacted
    log_params = {
        "table_name": table_name,
        "region_name": region_name,
        "endpoint_url": endpoint_url,
        "create_table_if_not_exists": create_table_if_not_exists,
        "has_aws_access_key_id": aws_access_key_id is not None,
        "has_aws_secret_access_key": aws_secret_access_key is not None
    }
    
    logger.info(f"Initializing DynamoDB storage with parameters: {json.dumps(log_params)}")
    
    # Create DynamoDB storage backend
    return DynamoDbStorage(
        table_name=table_name,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        endpoint_url=endpoint_url,
        create_table_if_not_exists=create_table_if_not_exists,
        **kwargs
    ) 