#!/usr/bin/env python3
"""
Main API module for Fama AI.

This module provides the main API endpoints for the Fama AI application.
"""
import os
import logging
import uuid
import json
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents.agent_coordinator import AgentCoordinator
from api.health import router as health_router

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fama AI API",
    description="API for Fama AI, providing agentic financial modeling for yield-generating investment vehicles.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the health router
app.include_router(health_router)

# In-memory storage for request logs (in a production environment, use a database)
request_logs = {}

class SubmitRequest(BaseModel):
    """
    Submit request model.
    
    Attributes:
        description: Natural language description of the investment vehicle
        time_horizon: Time horizon for the investment in years
        risk_factors: Risk factors to consider (conservative, moderate, aggressive)
        output_format: Format for the output (json, csv, pdf)
        research_context: Additional context for the research
        use_team_approach: Whether to use the team-based approach
        model_provider: The model provider to use
        model_id: The specific model ID to use (optional)
    """
    description: str = Field(..., description="Natural language description of the investment vehicle")
    time_horizon: int = Field(5, description="Time horizon for the investment in years", ge=1, le=30)
    risk_factors: str = Field("moderate", description="Risk factors to consider")
    output_format: str = Field("json", description="Format for the output")
    research_context: Optional[str] = Field(None, description="Additional context for the research")
    use_team_approach: bool = Field(False, description="Whether to use the team-based approach")
    model_provider: Optional[str] = Field(None, description="The model provider to use")
    model_id: Optional[str] = Field(None, description="The specific model ID to use")

class SubmitResponse(BaseModel):
    """
    Submit response model.
    
    Attributes:
        request_id: Unique identifier for the request
        status: Status of the request
        log_stream_url: URL for streaming logs for this request
        message: Additional information about the request
    """
    request_id: str = Field(..., description="Unique identifier for the request")
    status: str = Field(..., description="Status of the request")
    log_stream_url: str = Field(..., description="URL for streaming logs for this request")
    message: Optional[str] = Field(None, description="Additional information about the request")

def validate_api_key(request: Request) -> str:
    """
    Validate the API key provided in the request headers.
    
    Args:
        request: The FastAPI request object
    
    Returns:
        The API key if valid
    
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    api_key = request.headers.get("X-API-Key")
    expected_api_key = os.getenv("API_KEY")
    
    # Skip API key validation if no API key is set in the environment
    if not expected_api_key:
        logger.warning("No API_KEY set in environment, skipping validation")
        return "no_api_key_set"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key (X-API-Key header)",
        )
    
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key

def add_log(request_id: str, level: str, message: str) -> None:
    """
    Add a log entry for a specific request.
    
    Args:
        request_id: The unique identifier for the request
        level: The log level (DEBUG, INFO, WARNING, ERROR)
        message: The log message
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    
    if request_id not in request_logs:
        request_logs[request_id] = {
            "logs": [],
            "status": "processing",
            "results": None,
        }
    
    request_logs[request_id]["logs"].append(log_entry)

async def process_investment_vehicle(submit_request: SubmitRequest, request_id: str) -> None:
    """
    Process an investment vehicle description asynchronously.
    
    Args:
        submit_request: The submit request model
        request_id: The unique identifier for the request
    """
    try:
        add_log(request_id, "INFO", "Starting investment vehicle processing")
        
        # Initialize the AgentCoordinator
        model_provider = submit_request.model_provider or os.getenv("MODEL_PROVIDER", "formation")
        add_log(request_id, "INFO", f"Using model provider: {model_provider}")
        
        coordinator = AgentCoordinator(
            provider=model_provider,
            model_id=submit_request.model_id,
        )
        
        # Process the investment vehicle
        add_log(request_id, "INFO", "Processing investment vehicle with AgentCoordinator")
        
        # Set additional parameters
        kwargs = {}
        if submit_request.research_context:
            kwargs["research_context"] = submit_request.research_context
        
        # Use the team-based approach if specified
        kwargs["use_team_approach"] = submit_request.use_team_approach
        
        # Process the investment vehicle using the appropriate approach
        results = coordinator.process_investment_vehicle(
            description=submit_request.description,
            time_horizon=submit_request.time_horizon,
            risk_factors=submit_request.risk_factors,
            output_format=submit_request.output_format,
            **kwargs,
        )
        
        # Store the results
        add_log(request_id, "INFO", "Investment vehicle processing completed")
        request_logs[request_id]["status"] = "complete"
        request_logs[request_id]["results"] = results
        
    except Exception as e:
        logger.error(f"Error processing investment vehicle: {str(e)}")
        add_log(request_id, "ERROR", f"Error processing investment vehicle: {str(e)}")
        request_logs[request_id]["status"] = "error"
        request_logs[request_id]["error"] = str(e)

@app.post("/api/submit", response_model=SubmitResponse)
async def handle_post_submit(
    submit_request: SubmitRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(validate_api_key),
) -> SubmitResponse:
    """
    Submit an investment vehicle description for analysis.
    
    Args:
        submit_request: The submit request model
        background_tasks: The FastAPI background tasks object
        api_key: The validated API key
    
    Returns:
        The submit response model
    """
    logger.info("Received submit request")
    
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    
    # Initialize the request log
    request_logs[request_id] = {
        "logs": [],
        "status": "processing",
        "results": None,
    }
    
    # Add initial log entry
    add_log(request_id, "INFO", "Request received")
    
    # Add a demonstration mode for synchronous processing
    if os.getenv("DEMO_MODE") == "1":
        logger.info("Running in demonstration mode - synchronous processing")
        add_log(request_id, "INFO", "Running in demonstration mode - synchronous processing")
        
        # Initialize the AgentCoordinator
        coordinator = AgentCoordinator(
            provider=submit_request.model_provider or os.getenv("MODEL_PROVIDER", "formation"),
            model_id=submit_request.model_id,
        )
        
        # Set additional parameters
        kwargs = {}
        if submit_request.research_context:
            kwargs["research_context"] = submit_request.research_context
        
        # Use the team-based approach if specified
        kwargs["use_team_approach"] = submit_request.use_team_approach
        
        try:
            # Process the investment vehicle
            results = coordinator.process_investment_vehicle(
                description=submit_request.description,
                time_horizon=submit_request.time_horizon,
                risk_factors=submit_request.risk_factors,
                output_format=submit_request.output_format,
                **kwargs,
            )
            
            # Store the results
            request_logs[request_id]["status"] = "complete"
            request_logs[request_id]["results"] = results
            
            return SubmitResponse(
                request_id=request_id,
                status="complete",
                log_stream_url=f"/api/logs/{request_id}",
                message="Request processed successfully (demonstration mode)",
            )
            
        except Exception as e:
            logger.error(f"Error processing investment vehicle: {str(e)}")
            request_logs[request_id]["status"] = "error"
            request_logs[request_id]["error"] = str(e)
            
            return SubmitResponse(
                request_id=request_id,
                status="error",
                log_stream_url=f"/api/logs/{request_id}",
                message=f"Error: {str(e)}",
            )
    
    # Normal async processing
    background_tasks.add_task(
        process_investment_vehicle,
        submit_request=submit_request,
        request_id=request_id,
    )
    
    return SubmitResponse(
        request_id=request_id,
        status="processing",
        log_stream_url=f"/api/logs/{request_id}",
        message="Request received and processing started",
    )

@app.get("/api/logs/{request_id}")
async def handle_get_logs(
    request_id: str,
    api_key: str = Depends(validate_api_key),
) -> Dict[str, Any]:
    """
    Get the logs and results for a specific request.
    
    Args:
        request_id: The unique identifier for the request
        api_key: The validated API key
    
    Returns:
        The logs and results for the request
    
    Raises:
        HTTPException: If the request ID is not found
    """
    if request_id not in request_logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request ID {request_id} not found",
        )
    
    return {
        "request_id": request_id,
        "status": request_logs[request_id]["status"],
        "logs": request_logs[request_id]["logs"],
        "results": request_logs[request_id]["results"],
        "error": request_logs[request_id].get("error"),
    }

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that redirects to the API documentation.
    
    Returns:
        A message with a link to the API documentation
    """
    return {
        "message": "Welcome to the Fama AI API. Visit /docs for the API documentation.",
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True) 