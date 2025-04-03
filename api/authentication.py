#!/usr/bin/env python3
"""
API authentication module for Fama AI.

This module handles API key validation for requests.
"""
import os
import logging
import time
from typing import Dict, Optional, Tuple, Any

# Set up logging
logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    pass

class RateLimitError(Exception):
    """Exception raised for rate limit exceeded errors."""
    pass

def validate_api_key(api_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate the provided API key.
    
    In a production environment, this would check against a database.
    For development, it validates against environment variables.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        Tuple containing:
            - Boolean indicating if the key is valid
            - User information dict if valid, None otherwise
    """
    if not api_key:
        logger.warning("Empty API key provided")
        return False, None
        
    # In development, check against environment variable
    # In production, this would check against a database
    valid_keys = os.environ.get("VALID_API_KEYS", "test_key").split(",")
    
    if api_key in valid_keys:
        # In production, we would fetch user details from a database
        user_info = {
            "user_id": "dev_user_1",
            "credits_remaining": 1000,
            "tier": "development"
        }
        logger.info(f"Valid API key used: user_id={user_info['user_id']}")
        return True, user_info
    
    logger.warning(f"Invalid API key attempted: {api_key[:4]}...")
    return False, None

def check_rate_limit(user_id: str) -> bool:
    """
    Check if the user has exceeded their rate limit.
    
    Args:
        user_id: The ID of the user to check
        
    Returns:
        Boolean indicating if the user can proceed (not rate limited)
        
    Raises:
        RateLimitError: If the user has exceeded their rate limit
    """
    # In production, this would check a database or cache for request counts
    # For development, we'll always return True (not rate limited)
    
    # Example implementation:
    # current_time = int(time.time())
    # window_start = current_time - 60  # 1 minute window
    # 
    # recent_requests = get_requests_count(user_id, window_start, current_time)
    # max_requests = get_user_rate_limit(user_id)
    # 
    # if recent_requests >= max_requests:
    #     logger.warning(f"Rate limit exceeded for user {user_id}")
    #     raise RateLimitError(f"Rate limit of {max_requests} requests per minute exceeded")
    
    return True

def verify_request_auth(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Verify authentication for an incoming request.
    
    Args:
        headers: The request headers containing the authorization
        
    Returns:
        Dict containing user information
        
    Raises:
        AuthenticationError: If authentication fails
        RateLimitError: If the user has exceeded their rate limit
    """
    # Extract API key from Authorization header
    auth_header = headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header format")
        raise AuthenticationError("Authorization header must be in format: Bearer API_KEY")
    
    api_key = auth_header.replace("Bearer ", "")
    
    # Validate API key
    is_valid, user_info = validate_api_key(api_key)
    
    if not is_valid or user_info is None:
        raise AuthenticationError("Invalid API key")
    
    # Check rate limits
    if not check_rate_limit(user_info["user_id"]):
        raise RateLimitError("Rate limit exceeded")
    
    # Check if user has sufficient credits
    if user_info.get("credits_remaining", 0) <= 0:
        logger.warning(f"User {user_info['user_id']} has insufficient credits")
        raise AuthenticationError("Insufficient credits")
    
    return user_info 