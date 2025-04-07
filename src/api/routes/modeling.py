from typing import AsyncGenerator, List, Optional
import uuid
import logging
import os
import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse

from src.api.models.model_request import ModelRequest, ModelResponse, Provider
from src.api.settings import api_settings
from src.agents.init_agents import initialize_financial_modeling_team

# Configure logging
logger = logging.getLogger(__name__)

# Create uploads directory
UPLOADS_DIR = Path(api_settings.uploads_dir)
UPLOADS_DIR.mkdir(exist_ok=True)

# API key authentication
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Create router
modeling_router = APIRouter(prefix="/model", tags=["Financial Modeling"])

# API key dependency
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == api_settings.api_key:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

@modeling_router.post("/upload", status_code=status.HTTP_200_OK, dependencies=[Depends(get_api_key)])
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to use as a knowledge source"""
    file_path = UPLOADS_DIR / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}",
        )

async def model_response_streamer(
    team_dict: dict, 
    description: str,
    request_id: str,
    knowledge_files: List[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream financial model generation response chunk by chunk
    
    This follows the Agno API pattern for streaming responses
    
    Args:
        team_dict: Dictionary containing agent team members
        description: Investment description to model
        request_id: Unique request ID
        knowledge_files: Optional list of knowledge files to use
    
    Yields:
        JSON-formatted text chunks with progress information
    """
    try:
        # Yield start event
        yield json.dumps({
            "event": "start",
            "request_id": request_id,
            "message": "Starting financial modeling process"
        }) + "\n\n"
        
        # Step 1: Run the search agent
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "searcher",
            "message": "Running search agent",
            "progress": 10
        }) + "\n\n"
        
        searcher = team_dict["searcher"]
        search_prompt = f"Gather information necessary to build a financial model for {description}"
        
        # Use the agent's streaming capability
        search_response = await searcher.arun(search_prompt, stream=True)
        
        # Stream intermediate progress from search agent
        current_progress = 10
        target_progress = 30
        progress_chunks = 5
        progress_step = (target_progress - current_progress) / progress_chunks
        
        search_content = ""
        async for chunk in search_response:
            search_content += chunk.content or ""
            current_progress += progress_step
            
            if chunk.content:
                yield json.dumps({
                    "event": "chunk",
                    "request_id": request_id,
                    "agent": "searcher",
                    "chunk": chunk.content,
                    "progress": current_progress
                }) + "\n\n"
        
        # Yield search completion event
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "searcher",
            "message": "Search completed",
            "progress": 30
        }) + "\n\n"
        
        # Step 2: Run the assumption generator
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "assumption_generator",
            "message": "Running assumption generator",
            "progress": 35
        }) + "\n\n"
        
        assumption_generator = team_dict["assumption_generator"]
        assumption_prompt = f"Build assumptions based on the provided data relevant to building a financial model for {description}"
        
        # Use the agent's streaming capability
        assumption_response = await assumption_generator.arun(
            assumption_prompt,
            stream=True,
            data=search_content
        )
        
        # Stream intermediate progress from assumption agent
        current_progress = 35
        target_progress = 55
        progress_chunks = 5
        progress_step = (target_progress - current_progress) / progress_chunks
        
        assumption_content = ""
        async for chunk in assumption_response:
            assumption_content += chunk.content or ""
            current_progress += progress_step
            
            if chunk.content:
                yield json.dumps({
                    "event": "chunk",
                    "request_id": request_id,
                    "agent": "assumption_generator",
                    "chunk": chunk.content,
                    "progress": current_progress
                }) + "\n\n"
        
        # Yield assumption completion event
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "assumption_generator",
            "message": "Assumptions generated",
            "progress": 55
        }) + "\n\n"
        
        # Step 3: Run the metrics deriver
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "metrics_deriver",
            "message": "Running metrics deriver",
            "progress": 60
        }) + "\n\n"
        
        metrics_deriver = team_dict["metrics_deriver"]
        metrics_prompt = f"Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for {description}"
        
        # Use the agent's streaming capability
        metrics_response = await metrics_deriver.arun(
            metrics_prompt,
            stream=True,
            searcher_data=search_content,
            assumption_data=assumption_content
        )
        
        # Stream intermediate progress from metrics agent
        current_progress = 60
        target_progress = 75
        progress_chunks = 5
        progress_step = (target_progress - current_progress) / progress_chunks
        
        metrics_content = ""
        async for chunk in metrics_response:
            metrics_content += chunk.content or ""
            current_progress += progress_step
            
            if chunk.content:
                yield json.dumps({
                    "event": "chunk",
                    "request_id": request_id,
                    "agent": "metrics_deriver",
                    "chunk": chunk.content,
                    "progress": current_progress
                }) + "\n\n"
        
        # Yield metrics completion event
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "metrics_deriver",
            "message": "Metrics derived",
            "progress": 75
        }) + "\n\n"
        
        # Step 4: Run the financial modeler
        yield json.dumps({
            "event": "progress",
            "request_id": request_id,
            "agent": "financial_modeler",
            "message": "Building financial model",
            "progress": 80
        }) + "\n\n"
        
        financial_modeler = team_dict["financial_modeler"]
        model_prompt = f"""
        Based on the provided search data, assumptions, and metrics, build a comprehensive financial model for {description}.
        
        Your financial model should include:
        1. Income statements
        2. Cash flow statements
        3. Scenario analysis (bull, bear, baseline)
        4. Key financial metrics (NPV, IRR, payback period)
        5. Gross and Net Yield calculations across scenarios
        """
        
        # Use the agent's streaming capability
        model_response = await financial_modeler.arun(
            model_prompt.strip(),
            stream=True,
            searcher_data=search_content,
            assumption_data=assumption_content,
            metrics_data=metrics_content
        )
        
        # Stream intermediate progress from financial modeler agent
        current_progress = 80
        target_progress = 95
        progress_chunks = 5
        progress_step = (target_progress - current_progress) / progress_chunks
        
        financial_model_content = ""
        async for chunk in model_response:
            financial_model_content += chunk.content or ""
            current_progress += progress_step
            
            if chunk.content:
                yield json.dumps({
                    "event": "chunk",
                    "request_id": request_id,
                    "agent": "financial_modeler",
                    "chunk": chunk.content,
                    "progress": current_progress
                }) + "\n\n"
        
        # Prepare the final response
        try:
            # Try to parse model contents as JSON if possible
            parsed_financial_model = json.loads(financial_model_content)
        except json.JSONDecodeError:
            parsed_financial_model = {"raw_content": financial_model_content}
            
        try:
            parsed_assumptions = json.loads(assumption_content)
        except json.JSONDecodeError:
            parsed_assumptions = {"raw_content": assumption_content}
            
        try:
            parsed_metrics = json.loads(metrics_content)
        except json.JSONDecodeError:
            parsed_metrics = {"raw_content": metrics_content}
        
        final_response = {
            "request_id": request_id,
            "search_results": search_content,
            "assumptions": parsed_assumptions,
            "metrics": parsed_metrics,
            "financial_model": parsed_financial_model
        }
        
        # Send complete event
        yield json.dumps({
            "event": "complete",
            "request_id": request_id,
            "message": "Financial modeling complete",
            "data": final_response,
            "progress": 100
        }) + "\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming process for request {request_id}: {str(e)}")
        yield json.dumps({
            "event": "error",
            "request_id": request_id,
            "error": str(e)
        }) + "\n\n"

@modeling_router.post("", response_model=ModelResponse, dependencies=[Depends(get_api_key)])
async def create_model(request: ModelRequest, knowledge_files: List[UploadFile] = None):
    """
    Generate a financial model for an investment opportunity
    
    Args:
        request: The model request parameters
        knowledge_files: Optional list of uploaded knowledge files
    
    Returns:
        Either a streaming response or a complete model response
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")
    
    # Save uploaded knowledge files if any
    file_paths = []
    if knowledge_files:
        for file in knowledge_files:
            file_path = UPLOADS_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(str(file_path))
            logger.info(f"Saved knowledge file: {file_path}")
    
    # Get the API key based on provider
    api_key = request.api_key
    if not api_key:
        # Try to get from environment variables based on provider
        env_vars = {
            Provider.formation: "FORMATION_API_KEY",
            Provider.openai: "OPENAI_API_KEY",
            Provider.anthropic: "ANTHROPIC_API_KEY",
            Provider.openrouter: "OPENROUTER_API_KEY"
        }
        api_key = os.getenv(env_vars.get(request.provider, ""))
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key provided for {request.provider} provider",
        )
    
    try:
        # Initialize the agent team
        agent_team = initialize_financial_modeling_team(
            api_key=api_key,
            provider=request.provider.value,
            model_id=request.model_id,
            temperature=request.temperature,
            knowledge_files=file_paths,
            knowledge_urls=request.knowledge_urls,
            memory_id=request.memory_id,
            history_id=request.history_id,
            storage_id=request.storage_id,
            mcp_server_url=request.mcp_server_url
        )
        
        # If streaming is requested, return a streaming response
        if request.stream:
            return StreamingResponse(
                model_response_streamer(
                    team_dict=agent_team,
                    description=request.description,
                    request_id=request_id,
                    knowledge_files=file_paths
                ),
                media_type="text/event-stream",
            )
            
        # Non-streaming implementation
        else:
            # Step 1: Run the search agent
            logger.info(f"Running search for request {request_id}")
            searcher = agent_team["searcher"]
            search_prompt = f"Gather information necessary to build a financial model for {request.description}"
            
            search_response = await searcher.arun(search_prompt)
            search_results = search_response.content
            
            # Step 2: Run the assumption generator
            logger.info(f"Generating assumptions for request {request_id}")
            assumption_generator = agent_team["assumption_generator"]
            assumption_prompt = f"Build assumptions based on the provided data relevant to building a financial model for {request.description}"
            
            assumption_response = await assumption_generator.arun(
                assumption_prompt,
                data=search_results
            )
            assumptions = assumption_response.content
            
            # Step 3: Run the metrics deriver
            logger.info(f"Deriving metrics for request {request_id}")
            metrics_deriver = agent_team["metrics_deriver"]
            metrics_prompt = f"Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for {request.description}"
            
            metrics_response = await metrics_deriver.arun(
                metrics_prompt,
                searcher_data=search_results,
                assumption_data=assumptions
            )
            metrics = metrics_response.content
            
            # Step 4: Run the financial modeler
            logger.info(f"Building financial model for request {request_id}")
            financial_modeler = agent_team["financial_modeler"]
            model_prompt = f"""
            Based on the provided search data, assumptions, and metrics, build a comprehensive financial model for {request.description}.
            
            Your financial model should include:
            1. Income statements
            2. Cash flow statements
            3. Scenario analysis (bull, bear, baseline)
            4. Key financial metrics (NPV, IRR, payback period)
            5. Gross and Net Yield calculations across scenarios
            """
            
            model_response = await financial_modeler.arun(
                model_prompt.strip(),
                searcher_data=search_results,
                assumption_data=assumptions,
                metrics_data=metrics
            )
            financial_model = model_response.content
            
            # Try to parse JSON content
            try:
                parsed_financial_model = json.loads(financial_model)
            except json.JSONDecodeError:
                parsed_financial_model = {"raw_content": financial_model}
                
            try:
                parsed_assumptions = json.loads(assumptions)
            except json.JSONDecodeError:
                parsed_assumptions = {"raw_content": assumptions}
                
            try:
                parsed_metrics = json.loads(metrics)
            except json.JSONDecodeError:
                parsed_metrics = {"raw_content": metrics}
            
            # Prepare the response
            response = ModelResponse(
                request_id=request_id,
                search_results=search_results,
                assumptions=parsed_assumptions,
                metrics=parsed_metrics,
                financial_model=parsed_financial_model
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}",
        ) 