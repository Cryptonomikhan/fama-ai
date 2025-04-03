#!/usr/bin/env python3
"""
Main API module for Fama AI.

This module provides the main API endpoints for the Fama AI application.
"""
import os
import logging
import uuid
import json
from typing import Dict, Any, Optional, List, Generator, AsyncGenerator
import asyncio
from datetime import datetime
import time
import random
import threading

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents.agent_coordinator import AgentCoordinator
from api.health import router as health_router
from api.logging.stream import create_log_stream, get_log_stream

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
app.include_router(health_router, prefix="")

# In-memory storage for request logs and results
# In a production environment, this would be a database
request_logs: Dict[str, Dict[str, Any]] = {}

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
        stream_updates: Whether to stream real-time updates
    """
    description: str = Field(..., description="Natural language description of the investment vehicle")
    time_horizon: int = Field(5, description="Time horizon for the investment in years", ge=1, le=30)
    risk_factors: str = Field("moderate", description="Risk factors to consider")
    output_format: str = Field("json", description="Format for the output")
    research_context: Optional[str] = Field(None, description="Additional context for the research")
    use_team_approach: bool = Field(False, description="Whether to use the team-based approach")
    model_provider: Optional[str] = Field(None, description="The model provider to use")
    model_id: Optional[str] = Field(None, description="The specific model ID to use")
    stream_updates: bool = Field(True, description="Whether to stream real-time updates")

class SubmitResponse(BaseModel):
    """
    Submit response model.
    
    Attributes:
        request_id: Unique identifier for the request
        status: Status of the request
        log_stream_url: URL for streaming logs for this request
        stream_url: URL for streaming real-time updates
        message: Additional information about the request
    """
    request_id: str = Field(..., description="Unique identifier for the request")
    status: str = Field(..., description="Status of the request")
    log_stream_url: str = Field(..., description="URL for streaming logs for this request")
    stream_url: Optional[str] = Field(None, description="URL for streaming real-time updates")
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

def add_log(request_id: str, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Add a log entry for a specific request.
    
    Args:
        request_id: The unique identifier for the request
        level: The log level (DEBUG, INFO, WARNING, ERROR)
        message: The log message
        data: Optional additional data for the log
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    
    if data:
        log_entry["data"] = data
    
    if request_id not in request_logs:
        request_logs[request_id] = {
            "logs": [],
            "status": "processing",
            "results": None,
            "updates": []
        }
    
    request_logs[request_id]["logs"].append(log_entry)
    
    # If we have a log stream for this request, add to it
    log_stream = get_log_stream(request_id)
    if log_stream:
        log_stream.add_log(level, message, data)

def add_stream_update(request_id: str, update_type: str, content: Dict[str, Any]) -> None:
    """
    Add a streaming update for a specific request.
    
    Args:
        request_id: The unique identifier for the request
        update_type: The type of update (e.g., research, assumptions, model)
        content: The update content
    """
    update = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": update_type,
        "content": content
    }
    
    if request_id not in request_logs:
        request_logs[request_id] = {
            "logs": [],
            "status": "processing",
            "results": None,
            "updates": []
        }
    
    request_logs[request_id]["updates"].append(update)
    
    # Add a log entry for the update
    add_log(request_id, "INFO", f"Generated {update_type}", {"update_type": update_type})

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
        
        # Create a callback function for real-time updates if streaming is enabled
        if submit_request.stream_updates:
            def update_callback(update_type: str, content: Dict[str, Any]) -> None:
                add_stream_update(request_id, update_type, content)
            
            kwargs["update_callback"] = update_callback
        
        # Process the investment vehicle step by step with streaming updates
        if submit_request.use_team_approach:
            results = coordinator.process_investment_vehicle(
                description=submit_request.description,
                time_horizon=submit_request.time_horizon,
                risk_factors=submit_request.risk_factors,
                output_format=submit_request.output_format,
                **kwargs,
            )
        else:
            # Using step by step process with streaming updates
            add_log(request_id, "INFO", "Starting research phase")
            research_results = coordinator.research_agent.research_investment_vehicle(
                description=submit_request.description,
                time_horizon=submit_request.time_horizon,
                additional_context=kwargs.get("research_context")
            )
            add_stream_update(request_id, "research", research_results)
            
            # Get additional market conditions
            add_log(request_id, "INFO", "Getting market conditions")
            market_conditions = coordinator.research_agent.get_market_conditions()
            add_stream_update(request_id, "market_conditions", market_conditions)
            
            # Get yield data for similar investments
            add_log(request_id, "INFO", "Getting yield data")
            yield_data = coordinator.research_agent.get_yield_data(
                vehicle_type=kwargs.get("vehicle_type", "yield-generating investment"),
                time_period=f"last {submit_request.time_horizon} years"
            )
            add_stream_update(request_id, "yield_data", yield_data)
            
            # Step 2: Assumption Generation Phase
            add_log(request_id, "INFO", "Starting assumption generation phase")
            assumptions = coordinator.assumption_generator.generate_assumptions(
                description=submit_request.description,
                research_data=research_results,
                market_conditions=market_conditions,
                yield_data=yield_data,
                time_horizon=submit_request.time_horizon,
                risk_factors=submit_request.risk_factors
            )
            add_stream_update(request_id, "assumptions", assumptions)
            
            # Step 3: Modeling Phase
            add_log(request_id, "INFO", "Starting modeling phase")
            financial_model = coordinator.modeling_agent.create_financial_model(
                description=submit_request.description,
                research_data=research_results,
                market_conditions=market_conditions,
                yield_data=yield_data,
                time_horizon=submit_request.time_horizon,
                risk_factors=submit_request.risk_factors
            )
            add_stream_update(request_id, "financial_model", financial_model)
            
            # Generate financial metrics
            add_log(request_id, "INFO", "Generating financial metrics")
            metrics = coordinator.modeling_agent.generate_metrics(
                financial_model=financial_model,
                time_horizon=submit_request.time_horizon
            )
            add_stream_update(request_id, "metrics", metrics)
            
            # Step 4: Scenario Planning Phase
            add_log(request_id, "INFO", "Starting scenario planning phase")
            scenarios = coordinator.scenario_planner.generate_scenarios(
                description=submit_request.description,
                financial_model=financial_model,
                research_data=research_results,
                market_conditions=market_conditions,
                risk_factors=submit_request.risk_factors,
                time_horizon=submit_request.time_horizon
            )
            add_stream_update(request_id, "scenarios", scenarios)
            
            # Generate scenario impact analysis
            add_log(request_id, "INFO", "Generating scenario impact analysis")
            impact_analysis = coordinator.scenario_planner.analyze_scenario_impact(
                scenarios=scenarios,
                financial_metrics=metrics
            )
            add_stream_update(request_id, "impact_analysis", impact_analysis)
            
            # Step 5: Validation Phase
            add_log(request_id, "INFO", "Starting validation phase")
            validation_results = coordinator.validator.validate_financial_model(
                description=submit_request.description,
                financial_model=financial_model,
                research_data=research_results,
                market_conditions=market_conditions
            )
            add_stream_update(request_id, "validation", validation_results)
            
            # Validate metrics
            add_log(request_id, "INFO", "Validating financial metrics")
            metric_validation_results = coordinator.validator.validate_metrics(
                metrics=metrics,
                financial_model=financial_model,
                risk_factors=submit_request.risk_factors
            )
            add_stream_update(request_id, "metric_validation", metric_validation_results)
            
            # Validate scenarios
            add_log(request_id, "INFO", "Validating scenarios")
            scenario_validation_results = coordinator.validator.validate_scenarios(
                scenarios=scenarios,
                financial_model=financial_model,
                impact_analysis=impact_analysis
            )
            add_stream_update(request_id, "scenario_validation", scenario_validation_results)
            
            # Compile all results
            from tools.report_tools import generate_report
            
            results = {
                "request_id": request_id,
                "description": submit_request.description,
                "time_horizon": submit_request.time_horizon,
                "risk_factors": submit_request.risk_factors,
                "research": research_results,
                "market_conditions": market_conditions,
                "yield_data": yield_data,
                "assumptions": assumptions,
                "financial_model": financial_model,
                "metrics": metrics,
                "scenarios": scenarios,
                "impact_analysis": impact_analysis,
                "validation": validation_results,
                "metric_validation": metric_validation_results,
                "scenario_validation": scenario_validation_results,
                "status": "complete"
            }
            
            # Generate report
            add_log(request_id, "INFO", f"Generating {submit_request.output_format} report")
            report_path = generate_report(
                results=results,
                format=submit_request.output_format,
                filename=f"report_{request_id[:8]}",
                output_dir="reports"
            )
            
            # Add the report path to the results
            results["report_path"] = report_path
            add_stream_update(request_id, "report", {"path": report_path})
        
        # Store the results
        add_log(request_id, "INFO", "Investment vehicle processing completed")
        request_logs[request_id]["status"] = "complete"
        request_logs[request_id]["results"] = results
        
    except Exception as e:
        logger.error(f"Error processing investment vehicle: {str(e)}")
        add_log(request_id, "ERROR", f"Error processing investment vehicle: {str(e)}")
        request_logs[request_id]["status"] = "error"
        request_logs[request_id]["error"] = str(e)

def process_investment_vehicle_sync(submit_request: SubmitRequest, request_id: str) -> None:
    """
    Process an investment vehicle description synchronously for use with run_in_executor.
    """
    try:
        logger.info(f"Starting synchronous processing for request {request_id}")
        
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
        
        # Add update callback
        def update_callback(update_type: str, content: Dict[str, Any]) -> None:
            add_stream_update(request_id, update_type, content)
        
        kwargs["update_callback"] = update_callback
        
        # Process the investment vehicle
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
        "updates": []
    }
    
    # Create a log stream for this request
    create_log_stream(request_id)
    
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
            
            stream_url = f"/api/stream/{request_id}" if submit_request.stream_updates else None
            
            return SubmitResponse(
                request_id=request_id,
                status="complete",
                log_stream_url=f"/api/logs/{request_id}",
                stream_url=stream_url,
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
                stream_url=None,
                message=f"Error: {str(e)}",
            )
    
    # Normal async processing
    background_tasks.add_task(
        process_investment_vehicle,
        submit_request=submit_request,
        request_id=request_id,
    )
    
    stream_url = f"/api/stream/{request_id}" if submit_request.stream_updates else None
    
    return SubmitResponse(
        request_id=request_id,
        status="processing",
        log_stream_url=f"/api/logs/{request_id}",
        stream_url=stream_url,
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

async def generate_stream_content_forever(request_id: str) -> AsyncGenerator[str, None]:
    """
    Generate streaming content for a request and never close the connection until complete.
    
    Args:
        request_id: The unique identifier for the request
        
    Yields:
        JSON string of each update as it happens
    """
    logger.info(f"Starting stream for request {request_id}")
    
    if request_id not in request_logs:
        logger.error(f"Request ID {request_id} not found for streaming")
        yield json.dumps({"error": f"Request ID {request_id} not found"}) + "\n"
        return
    
    # First yield all existing updates
    logger.info(f"Sending {len(request_logs[request_id]['updates'])} existing updates for request {request_id}")
    for update in request_logs[request_id]["updates"]:
        logger.info(f"Streaming update: {update['type']}")
        yield json.dumps(update) + "\n"
    
    # Store the current update count
    current_count = len(request_logs[request_id]["updates"])
    logger.info(f"Starting streaming loop for request {request_id}, current count: {current_count}")
    
    # Track last heartbeat time to send heartbeats every 5 seconds
    last_heartbeat_time = time.time()
    heartbeat_interval = 5  # seconds
    
    # Keep streaming while the request is still processing
    try:
        while request_logs[request_id]["status"] == "processing":
            # Check if new updates have been added
            if len(request_logs[request_id]["updates"]) > current_count:
                logger.info(f"Found {len(request_logs[request_id]['updates']) - current_count} new updates for request {request_id}")
                # Yield all new updates
                for i in range(current_count, len(request_logs[request_id]["updates"])):
                    logger.info(f"Streaming update: {request_logs[request_id]['updates'][i]['type']}")
                    yield json.dumps(request_logs[request_id]["updates"][i]) + "\n"
                
                # Update the current count
                current_count = len(request_logs[request_id]["updates"])
                # Reset heartbeat timer whenever we send real updates
                last_heartbeat_time = time.time()
            
            # Yield a heartbeat message to keep the connection alive if needed
            current_time = time.time()
            if current_time - last_heartbeat_time >= heartbeat_interval:
                heartbeat = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "heartbeat",
                    "content": None
                }
                logger.debug(f"Sending heartbeat for request {request_id}")
                yield json.dumps(heartbeat) + "\n"
                last_heartbeat_time = current_time
            
            # Sleep to avoid busy waiting
            await asyncio.sleep(0.1)
        
        # Send final status when complete
        logger.info(f"Request {request_id} status: {request_logs[request_id]['status']}, sending final status")
        final_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "status",
            "content": {
                "status": request_logs[request_id]["status"],
                "error": request_logs[request_id].get("error"),
                "report_path": request_logs[request_id].get("results", {}).get("report_path")
            }
        }
        yield json.dumps(final_status) + "\n"
        logger.info(f"Stream for request {request_id} completed")
    except Exception as e:
        logger.error(f"Error in stream generator for request {request_id}: {str(e)}")
        error_msg = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "content": {
                "message": f"Stream error: {str(e)}"
            }
        }
        yield json.dumps(error_msg) + "\n"

@app.post("/api/submit/stream")
async def handle_submit_and_stream(
    submit_request: SubmitRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(validate_api_key),
) -> StreamingResponse:
    """
    Submit an investment vehicle description for analysis and stream the results in real-time.
    
    Args:
        submit_request: The submit request model
        background_tasks: The FastAPI background tasks object
        api_key: The validated API key
    
    Returns:
        A streaming response with real-time updates
    """
    logger.info("Received submit and stream request")
    
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    
    # Initialize the request log
    request_logs[request_id] = {
        "logs": [],
        "status": "processing",
        "results": None,
        "updates": []
    }
    
    # Create a log stream for this request
    create_log_stream(request_id)
    
    # Add initial log entry
    add_log(request_id, "INFO", "Request received")
    add_stream_update(request_id, "initialization", {"request_id": request_id, "message": "Request received and processing started"})
    
    # Define the processing async task
    async def process_async():
        # Small delay to ensure streaming connection is established first
        await asyncio.sleep(0.5)
        logger.info(f"Starting async task for request {request_id}")
        
        try:
            # Run the actual processing in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: process_investment_vehicle_sync(
                submit_request=submit_request,
                request_id=request_id
            ))
            logger.info(f"Async task completed for request {request_id}")
        except Exception as e:
            logger.error(f"Error in async task for request {request_id}: {str(e)}")
    
    # Create and start the async task
    asyncio.create_task(process_async())
    logger.info(f"Created async task for request {request_id}")
    
    # Return the streaming response
    return StreamingResponse(
        generate_stream_content_forever(request_id),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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

@app.get("/api/stream/{request_id}")
async def handle_stream_updates(
    request_id: str,
    api_key: str = Depends(validate_api_key),
) -> StreamingResponse:
    """
    Stream real-time updates for a specific request.
    
    Args:
        request_id: The unique identifier for the request
        api_key: The validated API key
    
    Returns:
        A streaming response with real-time updates
    
    Raises:
        HTTPException: If the request ID is not found
    """
    logger.info(f"Stream endpoint accessed for request {request_id}")
    if request_id not in request_logs:
        logger.error(f"Request ID {request_id} not found for streaming endpoint")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request ID {request_id} not found",
        )
    
    # Return regular JSON format which works better with curl
    return StreamingResponse(
        generate_stream_content_forever(request_id),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # For nginx
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True) 