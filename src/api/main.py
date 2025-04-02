"""
Main API entry point for the Financial Modeling Agent.
This module handles incoming API requests and orchestrates the specialized agents.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import logging
import os
from datetime import datetime

# Import our agent modules
from agents.research import ResearchAgent
from agents.analysis import AnalysisAgent
from agents.visualization import VisualizationAgent

# Import our model helper
try:
    from src.utils.llm_models import get_llm_model, get_available_models
except ImportError:
    # Fallback if the utils module isn't found
    from utils.llm_models import get_llm_model, get_available_models

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Financial Modeling Agent API",
    description="A sophisticated financial modeling API built with Agno Framework",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models
class ModelConfiguration(BaseModel):
    """Configuration for the LLM model to use for analysis."""
    provider: Optional[str] = None  # e.g., "formation", "openai", "anthropic"
    model_id: Optional[str] = None  # e.g., "best-quality", "gpt-4o", "claude-3-sonnet"
    api_key: Optional[str] = None  # Will default to environment variable if not provided

class FinancialContext(BaseModel):
    business_name: str
    business_description: str
    industry: str
    competitors: Optional[List[str]] = []
    region: Optional[str] = None
    timeframe_years: Optional[int] = 5
    existing_revenue_model: Optional[str] = None
    financial_data_sources: Optional[Dict[str, Any]] = None

class ApiRequest(BaseModel):
    context: FinancialContext
    plaid_access_token: Optional[str] = None
    white_label_config: Optional[Dict[str, Any]] = None
    model_config: Optional[ModelConfiguration] = None
    additional_params: Optional[Dict[str, Any]] = {}

class ApiResponse(BaseModel):
    request_id: str
    timestamp: datetime
    research_summary: Dict[str, Any]
    financial_model: Dict[str, Any]
    visualizations: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    model_info: Optional[Dict[str, str]] = None

@app.get("/")
async def root():
    return {"message": "Financial Modeling Agent API is running"}

@app.get("/api/models")
async def get_available_llm_models():
    """Return information about available models and current configuration."""
    return get_available_models()

@app.post("/api/analyze", response_model=ApiResponse)
async def analyze_business(request: ApiRequest):
    """
    Main endpoint for financial modeling.
    Orchestrates the process between research, analysis, and visualization agents.
    """
    logger.info(f"Received analysis request for: {request.context.business_name}")
    
    try:
        # Configure model based on request or environment variables
        model_config = request.model_config or ModelConfiguration()
        
        # Get model instance using our helper
        model = get_llm_model(
            provider=model_config.provider,
            model_id=model_config.model_id,
            api_key=model_config.api_key
        )
        
        # Initialize the agents with the configured model
        research_agent = ResearchAgent(model=model)
        analysis_agent = AnalysisAgent(model=model)
        visualization_agent = VisualizationAgent(model=model)
        
        # Save model info for response
        model_info = {
            "provider": getattr(model, "provider", os.environ.get("LLM_PROVIDER", "unknown")),
            "model_id": getattr(model, "id", os.environ.get("LLM_MODEL_ID", "unknown"))
        }
        
        # Step 1: Perform deep research on the business and market
        research_results = await research_agent.analyze(
            business_name=request.context.business_name,
            business_description=request.context.business_description,
            industry=request.context.industry,
            competitors=request.context.competitors,
            region=request.context.region,
            existing_revenue_model=request.context.existing_revenue_model
        )
        
        # Step 2: Construct the financial model based on research
        financial_model = await analysis_agent.build_model(
            research_results=research_results,
            financial_data_sources=request.context.financial_data_sources,
            plaid_access_token=request.plaid_access_token,
            timeframe_years=request.context.timeframe_years
        )
        
        # Step 3: Generate visualizations and dashboards
        visualizations = await visualization_agent.create_visualizations(
            financial_model=financial_model,
            white_label_config=request.white_label_config
        )
        
        # Prepare recommendations based on the analysis
        recommendations = analysis_agent.generate_recommendations(
            research_results=research_results,
            financial_model=financial_model
        )
        
        # Generate a unique request ID
        request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Construct the response
        response = ApiResponse(
            request_id=request_id,
            timestamp=datetime.now(),
            research_summary=research_results,
            financial_model=financial_model,
            visualizations=visualizations,
            recommendations=recommendations,
            model_info=model_info
        )
        
        logger.info(f"Successfully completed analysis for request: {request_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 