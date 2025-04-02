"""
Financial Modeling Agent System built with Agno framework.

This system uses a multi-agent approach to perform deep research, financial analysis,
and visualization for comprehensive financial modeling across various investment types.
"""

import os
import logging
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.playground import Playground, serve_playground_app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import our custom tools
from tools.financial_data import PlaidDataTools
from tools.market_research import MarketResearchTools
from tools.revenue_modeling import RevenueModelingTools
from tools.visualization import VisualizationTools
from tools.context_analyzer import ContextAnalyzerTools

# Import our analysis agent
try:
    # Try to import from api.agents for backward compatibility
    from api.agents.analysis import AnalysisAgent
    logger.info("Imported AnalysisAgent from legacy path")
except ImportError:
    try:
        # Try the new structure
        from agents.analysis import AnalysisAgent
        logger.info("Imported AnalysisAgent from new path")
    except ImportError:
        logger.warning("Could not import AnalysisAgent - functionality may be limited")
        AnalysisAgent = None

# Create FastAPI app
app = FastAPI(
    title="Financial Modeling Agent API",
    description="A sophisticated financial modeling API built with Agno Framework that supports various investment types",
    version="1.0.0",
)

# Initialize the models
model = OpenAIChat(id="gpt-4o")  # Can be replaced with any model provider

# Create context analyzer agent
context_analyzer_agent = Agent(
    name="Context Analyzer Agent",
    role="Analyze investment opportunities and determine appropriate modeling approaches",
    model=model,
    tools=[ContextAnalyzerTools()],
    instructions=[
        "Analyze the investment opportunity to determine its type and characteristics",
        "Identify the most appropriate financial modeling approaches",
        "Determine the relevant metrics and data sources",
        "Design appropriate scenario analyses",
        "Adapt the approach based on the specific investment type (startup, REIT, tokenized asset, etc.)"
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create specialized agents
research_agent = Agent(
    name="Research Agent",
    role="Conduct deep market research and opportunity analysis",
    model=model,
    tools=[MarketResearchTools(), ContextAnalyzerTools()],
    instructions=[
        "Analyze industry trends and market dynamics relevant to the investment",
        "Identify key competitors or comparable investments",
        "Determine relevant KPIs based on the investment type",
        "Research should be thorough and include citation of sources",
        "Adapt research approach based on investment type (startup, REIT, SPV, etc.)"
    ],
    show_tool_calls=True,
    markdown=True,
)

financial_agent = Agent(
    name="Financial Analysis Agent",
    role="Build comprehensive financial models and projections",
    model=model,
    tools=[PlaidDataTools(), RevenueModelingTools(), ContextAnalyzerTools()],
    instructions=[
        "Construct financial models based on research insights",
        "Support different revenue and investment models appropriate to the opportunity",
        "Perform scenario analysis tailored to the investment type",
        "Calculate key financial metrics specific to the investment category",
        "Adapt modeling approach for different investment structures (equity, debt, real estate, etc.)"
    ],
    show_tool_calls=True,
    markdown=True,
)

visualization_agent = Agent(
    name="Visualization Agent",
    role="Generate interactive dashboards and visualizations",
    model=model,
    tools=[VisualizationTools()],
    instructions=[
        "Create clear, informative visualizations of financial data",
        "Support white-label customization for dashboards",
        "Generate executive summaries with key insights",
        "Ensure all visualizations are responsive and interactive",
        "Adapt visualization approach based on investment type and audience"
    ],
    show_tool_calls=True,
    markdown=True,
)

# Initialize the AnalysisAgent if available
analysis_agent_instance = None
if AnalysisAgent is not None:
    try:
        analysis_agent_instance = AnalysisAgent()
        logger.info("Successfully initialized AnalysisAgent")
    except Exception as e:
        logger.error(f"Error initializing AnalysisAgent: {e}")

# Create the main agent team that orchestrates the specialized agents
financial_modeling_team = Agent(
    name="Financial Modeling Team",
    team=[context_analyzer_agent, research_agent, financial_agent, visualization_agent],
    model=model,
    instructions=[
        "First analyze the investment opportunity to determine the appropriate modeling approach",
        "Coordinate the workflow between research, financial analysis, and visualization",
        "Ensure consistency and quality across the entire financial modeling process",
        "Provide detailed recommendations based on the analysis",
        "Maintain a stateless design where each request is processed independently",
        "Adapt the entire process based on investment type (startup, REIT, tokenized asset, SPV, etc.)"
    ],
    show_tool_calls=True,
    markdown=True,
)

# Create a playground for interactive use
playground = Playground(
    agents=[
        financial_modeling_team,
        context_analyzer_agent,
        research_agent,
        financial_agent,
        visualization_agent
    ],
    title="Financial Modeling Agent",
    description="A sophisticated financial modeling agent built with Agno framework, supporting various investment types",
)

# Mount the playground to the FastAPI app
serve_playground_app(app, playground)

# Define models for API requests
class InvestmentAnalysisRequest(BaseModel):
    name: str = Field(..., description="Name of the investment opportunity or business")
    description: str = Field(..., description="Detailed description of the opportunity")
    
    # Fields for various investment types
    industry: Optional[str] = Field(None, description="Industry sector for business/startup opportunities")
    investment_type: Optional[str] = Field(None, description="Type of investment (Startup, REIT, SPV, etc.)")
    asset_class: Optional[str] = Field(None, description="Asset class (Equity, Debt, Real Estate, etc.)")
    location: Optional[str] = Field(None, description="Geographic location relevant to the investment")
    revenue_model: Optional[str] = Field(None, description="Existing or proposed revenue model")
    stage: Optional[str] = Field(None, description="Stage of development (Pre-seed, Seed, Series A, Mature, etc.)")
    historical_data: Optional[Dict[str, Any]] = Field(None, description="Historical financial or performance data")
    
    # Analysis parameters
    timeframe_years: int = Field(5, description="Number of years to project")
    plaid_access_token: Optional[str] = Field(None, description="Token for Plaid API integration")
    scenario_analysis: bool = Field(True, description="Whether to include scenario analysis")
    risk_analysis: bool = Field(True, description="Whether to include risk analysis")
    comps_analysis: bool = Field(True, description="Whether to include analysis of comparable investments")
    
    # Custom analysis parameters
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters specific to this investment type")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Opportunity",
                "description": "A SaaS platform for project management targeting enterprise customers",
                "industry": "Software",
                "investment_type": "Startup",
                "asset_class": "Equity",
                "location": "United States",
                "revenue_model": "Subscription",
                "stage": "Series A",
                "timeframe_years": 5,
                "scenario_analysis": True,
                "risk_analysis": True,
                "comps_analysis": True
            }
        }

# Direct API endpoint for programmatic access
@app.post("/api/analyze")
async def analyze_investment(request: InvestmentAnalysisRequest = Body(...)):
    """
    Main endpoint for financial modeling of various investment opportunities.
    
    Accepts details about any type of investment opportunity and orchestrates
    a comprehensive financial modeling process tailored to the specific type.
    """
    logger.info(f"Received analysis request for {request.name}")
    
    # Build comprehensive description combining all provided fields
    detailed_description = f"""
    Investment/Business Name: {request.name}
    
    Description: {request.description}
    
    {f"Industry: {request.industry}" if request.industry else ""}
    {f"Investment Type: {request.investment_type}" if request.investment_type else ""}
    {f"Asset Class: {request.asset_class}" if request.asset_class else ""}
    {f"Location: {request.location}" if request.location else ""}
    {f"Revenue Model: {request.revenue_model}" if request.revenue_model else ""}
    {f"Stage: {request.stage}" if request.stage else ""}
    
    Timeframe: {request.timeframe_years} years
    
    Analysis Requests:
    - Scenario Analysis: {"Yes" if request.scenario_analysis else "No"}
    - Risk Analysis: {"Yes" if request.risk_analysis else "No"}
    - Comparable Investments Analysis: {"Yes" if request.comps_analysis else "No"}
    
    {f"Historical Data: {request.historical_data}" if request.historical_data else ""}
    {f"Custom Parameters: {request.custom_parameters}" if request.custom_parameters else ""}
    """
    
    # Use the AnalysisAgent if available for deeper financial modeling
    if analysis_agent_instance:
        logger.info("Using AnalysisAgent for detailed financial modeling")
        
        # This would be integrated with the agent workflow
        # Simplified example - in production would be fully integrated
        try:
            # Construct a research_results object (simplified)
            # In production this would come from the research agent
            research_results = {
                "business_profile": {
                    "name": request.name,
                    "description": request.description,
                    "industry": request.industry,
                    "investment_type": request.investment_type,
                    "stage": request.stage,
                    "location": request.location
                },
                "market_analysis": {
                    "growth_rate": "10% CAGR",  # Example
                    "market_size": "$10B"  # Example
                },
                "key_performance_indicators": {
                    "financial_kpis": []  # To be filled
                },
                "recommended_revenue_models": {
                    "primary_recommendation": {
                        "model": request.revenue_model or "subscription"
                    }
                }
            }
            
            # Build financial model using the analysis agent
            financial_model = await analysis_agent_instance.build_model(
                research_results=research_results,
                financial_data_sources=request.historical_data,
                plaid_access_token=request.plaid_access_token,
                timeframe_years=request.timeframe_years
            )
            
            # Generate recommendations
            recommendations = analysis_agent_instance.generate_recommendations(
                research_results=research_results,
                financial_model=financial_model
            )
            
            # Add recommendations to the financial model
            financial_model["recommendations"] = recommendations
            
            # This would be integrated with the agent response
            # For now, we'll continue with the normal agent flow but note
            # that we have the financial model available
            
            logger.info("Successfully generated financial model with AnalysisAgent")
        except Exception as e:
            logger.error(f"Error using AnalysisAgent: {e}")
            logger.info("Falling back to standard agent workflow")
    
    # Create a prompt for the agent
    prompt = f"""
    Perform a comprehensive financial analysis for the following investment opportunity:
    
    {detailed_description}
    
    I need a complete financial model with:
    1. Context analysis to determine the appropriate modeling approach
    2. Market research tailored to this investment type
    3. Financial projections using the most appropriate methodology
    4. Interactive visualizations and dashboard
    5. Risk assessment and scenario analysis
    6. Key recommendations
    
    Please adapt your entire approach based on the specific type of investment opportunity.
    """
    
    # Create a context dictionary for the agent
    context = {
        "investment_name": request.name,
        "description": request.description,
        "investment_type": request.investment_type,
        "industry": request.industry,
        "asset_class": request.asset_class,
        "location": request.location,
        "revenue_model": request.revenue_model,
        "stage": request.stage,
        "timeframe_years": request.timeframe_years,
        "plaid_access_token": request.plaid_access_token,
        "historical_data": request.historical_data,
        "custom_parameters": request.custom_parameters,
        "scenario_analysis": request.scenario_analysis,
        "risk_analysis": request.risk_analysis,
        "comps_analysis": request.comps_analysis
    }
    
    # Run the financial modeling team agent
    logger.info("Running financial modeling team")
    response = financial_modeling_team.generate(prompt, context=context)
    
    # If we generated a financial model with the AnalysisAgent, add it to the context
    # so it can be used by the agent or returned as part of the response
    if 'financial_model' in locals():
        response["financial_model"] = financial_model
    
    logger.info("Completed financial analysis request")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 