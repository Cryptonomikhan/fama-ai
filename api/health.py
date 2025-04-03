#!/usr/bin/env python3
"""
Health check endpoint for the Fama AI API.

This module provides a health check endpoint that verifies the availability
of model providers and system status.
"""
import os
import logging
from typing import Dict, Any, List
import requests
from fastapi import APIRouter, HTTPException

# Create router
router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

def check_formation_api() -> Dict[str, Any]:
    """
    Check if the Formation AI API is available.
    
    Returns:
        Dict containing status and message
    """
    api_key = os.getenv("FORMATION_API_KEY")
    if not api_key:
        return {"status": "unavailable", "message": "API key not configured"}
    
    try:
        # Simple health check request to Formation API
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            "https://api.formation.ai/v1/health",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return {"status": "healthy", "message": "Formation API is available"}
        else:
            return {
                "status": "degraded",
                "message": f"Formation API returned status code {response.status_code}"
            }
    except Exception as e:
        logger.warning(f"Error checking Formation API: {str(e)}")
        return {"status": "unavailable", "message": f"Error: {str(e)}"}

def check_openai_api() -> Dict[str, Any]:
    """
    Check if the OpenAI API is available.
    
    Returns:
        Dict containing status and message
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"status": "unavailable", "message": "API key not configured"}
    
    try:
        # Simple health check request to OpenAI API
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return {"status": "healthy", "message": "OpenAI API is available"}
        else:
            return {
                "status": "degraded",
                "message": f"OpenAI API returned status code {response.status_code}"
            }
    except Exception as e:
        logger.warning(f"Error checking OpenAI API: {str(e)}")
        return {"status": "unavailable", "message": f"Error: {str(e)}"}

def check_anthropic_api() -> Dict[str, Any]:
    """
    Check if the Anthropic API is available.
    
    Returns:
        Dict containing status and message
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "unavailable", "message": "API key not configured"}
    
    try:
        # Simple health check request to Anthropic API
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json"
        }
        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return {"status": "healthy", "message": "Anthropic API is available"}
        else:
            return {
                "status": "degraded",
                "message": f"Anthropic API returned status code {response.status_code}"
            }
    except Exception as e:
        logger.warning(f"Error checking Anthropic API: {str(e)}")
        return {"status": "unavailable", "message": f"Error: {str(e)}"}

@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """
    Perform a health check of the API and model providers.
    
    Returns:
        Dict containing health check results
    """
    logger.info("Performing health check")
    
    # Check each model provider
    formation_status = check_formation_api()
    openai_status = check_openai_api()
    anthropic_status = check_anthropic_api()
    
    # Build list of provider results
    providers = [
        {"name": "formation", **formation_status},
        {"name": "openai", **openai_status},
        {"name": "anthropic", **anthropic_status}
    ]
    
    # Determine overall model status
    healthy_providers = [p for p in providers if p["status"] == "healthy"]
    if len(healthy_providers) == 0:
        models_status = "unavailable"
        models_message = "No model providers available"
    elif len(healthy_providers) < len(providers):
        models_status = "degraded"
        models_message = f"{len(healthy_providers)}/{len(providers)} model providers available"
    else:
        models_status = "healthy"
        models_message = "All model providers available"
    
    # Determine overall API status
    if models_status == "unavailable":
        overall_status = "degraded"
        overall_message = "API operational but no model providers available"
    else:
        overall_status = "healthy"
        overall_message = "All systems operational"
    
    # Return the health check results
    return {
        "status": overall_status,
        "message": overall_message,
        "components": {
            "api": {
                "status": "healthy",
                "message": "API is operational"
            },
            "models": {
                "status": models_status,
                "message": models_message,
                "providers": providers
            }
        }
    } 