from textwrap import dedent
from typing import AsyncGenerator, Union
import uvicorn
import logging
import json
from http import HTTPStatus
import datetime
import os
import sys

from agno.agent import Agent
from agno.team.team import Team
from fastapi import APIRouter, status, FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
from src.agents.financial_modeler import FinancialModelingAgent
from pydantic import BaseModel, Field, field_validator

from src.models.factory import create_model

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"financial_api_{datetime.datetime.now().strftime('%Y%m%d')}.log")

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)

# Store logs in memory for easy retrieval (limited to recent logs)
MAX_IN_MEMORY_LOGS = 100
request_logs = {}

# Set up logger
logger = logging.getLogger(__name__)

task_router = APIRouter(prefix="/task", tags=["Tasks"])


async def chat_response_streamer(
    agent: Union[Agent, Team],
    message: str
) -> AsyncGenerator:
    """
    Stream agent responses chunk by chunk

    Args:
        agent: The agent instance to interact with
        message: User message to process

    Yields:
        Text chunks from the agent response
    """
    logger.info("Starting streaming response")
    
    run_response = await agent.arun(message, stream=True)
    
    chunk_count = 0
    async for chunk in run_response:
        chunk_count += 1
        if chunk_count % 20 == 0:  # Log every 20th chunk to avoid excessive logging
            logger.debug(f"Streaming chunk {chunk_count}: {chunk.content[:50]}...")
        yield chunk.content
    
    logger.info(f"Completed streaming response with {chunk_count} chunks")


class TaskRequest(BaseModel):
    """Request model for executing a task"""

    message: str
    stream: bool = True
    provider: str = "openai"
    model: str = "gpt-4o"
    provider_api_key: str = Field(..., description="API key for the specified provider")
    verbose_logging: bool = Field(False, description="Enable verbose logging of the entire process")
    # TODO: Add user_id/API key, session_id, ect.
    
    @field_validator('provider_api_key')
    def validate_api_key(cls, v, info):
        provider = info.data.get('provider', '').lower()
        
        # Basic validation based on provider
        if provider == 'openai' and not v.startswith('sk-'):
            raise ValueError('OpenAI API key should start with "sk-"')
        elif provider == 'anthropic' and not v.startswith(('sk-', 'ant-')):
            raise ValueError('Anthropic API key should start with "sk-" or "ant-"')
        elif provider == 'formation' and not len(v) > 20:
            raise ValueError('Formation API key appears to be invalid')
        
        # Ensure the key has a minimum length for basic security
        if len(v) < 10:
            raise ValueError('API key is too short to be valid')
            
        return v


# Log retrieval endpoint
@task_router.get("/logs/{request_id}", status_code=status.HTTP_200_OK, tags=["Logs"])
async def get_request_logs(request_id: str):
    """
    Retrieve logs for a specific request
    """
    if request_id in request_logs:
        return {"request_id": request_id, "logs": request_logs[request_id]}
    else:
        # Try to read from log file
        try:
            all_logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    for line in f:
                        if request_id in line:
                            all_logs.append(line.strip())
            
            if all_logs:
                return {"request_id": request_id, "logs": all_logs}
            else:
                return JSONResponse(
                    content={"error": f"No logs found for request ID: {request_id}"},
                    status_code=HTTPStatus.NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error retrieving logs for request ID {request_id}: {str(e)}")
            return JSONResponse(
                content={"error": f"Error retrieving logs: {str(e)}"},
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )


@task_router.post("/submit", status_code=status.HTTP_200_OK)
async def run_task(body: TaskRequest):
    request_id = f"{body.provider}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Initialize log storage for this request
    request_logs[request_id] = []
    
    # Custom log handler to store logs in memory too
    def log_to_memory(log_message):
        if len(request_logs) > MAX_IN_MEMORY_LOGS:
            # Remove oldest request logs if we exceed the limit
            oldest_key = next(iter(request_logs))
            request_logs.pop(oldest_key)
        
        request_logs[request_id].append(log_message)
    
    try:
        logger.info(f"Starting new task request ID: {request_id}")
        log_to_memory(f"Starting new task request ID: {request_id}")
        
        # Set log level based on verbose flag
        if body.verbose_logging:
            logger.setLevel(logging.DEBUG)
            logger.info("Verbose logging enabled")
            log_to_memory("Verbose logging enabled")
        
        # Create the model with the provided API key
        model_kwargs = {"api_key": body.provider_api_key}
        
        logger.info(f"Creating agents with provider: {body.provider}, model: {body.model}")
        log_to_memory(f"Creating agents with provider: {body.provider}, model: {body.model}")
        
        searcher = SearchingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            **model_kwargs
        )
        assumption_generator = AssumptionGeneratorAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            **model_kwargs
        )
        metrics_deriver = MetricsDerivingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            **model_kwargs
        )
        modeler = FinancialModelingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            **model_kwargs
        )

        logger.info("Creating team with all agents")
        log_to_memory("Creating team with all agents")
        
        team = Team(
            name="Financial Modeling Team",
            members=[
                searcher.agent,
                assumption_generator.agent,
                metrics_deriver.agent,
                modeler.agent
            ],
            mode="coordinate",
            model=create_model(
                provider=body.provider,
                model_id=body.model,
                **model_kwargs
            ),
            instructions=dedent("""\
                You are a senior financial analyst with over 20 years of experience in investment banking and private equity.
                You hold a Chartered Financial Analyst (CFA) designation and a Chartered Alternative Investment Analyst (CAIA) designation.
                
                ## Your Task
                You are tasked with managing a team to build an institutional-quality, comprehensive financial model for the investment opportunity provided.
                This model must meet the standards of top-tier investment firms like Goldman Sachs, BlackRock, or KKR.
                
                ## ⛔️ MANDATORY CALCULATION DEMONSTRATION ⛔️
                
                You MUST provide a step-by-step demonstration showing EXACTLY how EVERY significant number in your model was calculated.
                
                For EVERY revenue source, expense item, and financial metric, you MUST:
                1. Show the general formula
                2. Show the exact values plugged into that formula
                3. Show each intermediate calculation step
                4. Show the final result
                
                Example 1 - Inference Revenue:
                ```
                Annual Inference Revenue = Tokens per second × Concurrent requests × Seconds per hour × Hours per day × Days per year × Utilization rate × Price per million tokens ÷ 1,000,000
                
                For Bull Case:
                = 21,000 tokens/second × 8 concurrent requests × 3,600 seconds/hour × 24 hours/day × 365 days/year × 70% utilization × $0.40 per million tokens ÷ 1,000,000
                = 21,000 × 8 × 3,600 × 24 × 365 × 0.70 × $0.40 ÷ 1,000,000
                = 1,659,312,000,000 tokens per year × $0.40 ÷ 1,000,000
                = $663,724.80 per year
                ```
                
                Example 2 - Gross Yield Calculation:
                ```
                Gross Yield = (Annual Revenue ÷ Initial Investment) × 100%
                
                For Bull Case:
                Annual Revenue = $663,724.80 (inference) + $84,672 (rental)
                Initial Investment = $450,000
                
                Gross Yield = ($748,396.80 ÷ $450,000) × 100%
                Gross Yield = 1.6631 × 100%
                Gross Yield = 166.31%
                ```
                
                DO NOT SUMMARIZE OR SKIP CALCULATION STEPS. SHOW EVERY STEP WITH ALL NUMBERS AND OPERATIONS.
                THIS IS THE MOST IMPORTANT REQUIREMENT.
                
                ## 💻 USING MATH TOOLS IN CALCULATIONS 💻
                
                When performing calculations with the MathTools:
                1. Even though you will use the math_tools functions internally for precision, you MUST ALSO show the human-readable breakdown of every calculation in your final report
                2. All key revenue, expense, and yield calculations MUST be shown step-by-step in your report
                3. The numbers produced by math_tools calculations MUST match the numbers in your step-by-step explanations
                4. Do NOT just give the final numbers - ALWAYS show how they were derived
                
                CRITICAL: Include the full calculation breakdowns in your FINAL OUTPUT, not just in your internal working process!
                
                ## 📊 MANDATORY REPORT STRUCTURE 📊
                
                Your final report MUST INCLUDE ALL of the following sections IN THIS EXACT ORDER:
                
                1. **📌 Executive Summary**: A concise overview of the investment opportunity, key findings, and investment recommendations (1-2 paragraphs)
                
                2. **📌 Investment Overview**: Brief description of the investment vehicle, its structure, and key features (1-2 paragraphs)
                
                3. **📌 Key Financial Metrics Summary**: A table showing the most critical metrics across all scenarios
                
                4. **📌 Detailed Assumptions**:
                   - List ALL assumptions made for each scenario (bull, base, bear)
                   - Include market rates, utilization rates, capacity calculations, etc.
                   - Explain WHY each assumption was chosen with brief justification
                
                5. **📌 Step-by-Step Calculations**:
                   - SHOW the actual calculation formulas used for ALL major figures
                   - For each revenue stream, DEMONSTRATE the mathematical calculation with all variables
                   - For expenses, depreciation, and yields, SHOW the exact formulas with numbers
                   - Include the actual numbers in each formula to show transparency
                
                6. **📌 Scenario Analysis**: Detailed breakdown of all three scenarios with full calculations
                
                7. **📌 Year-by-Year Projections**: Tables showing the projected performance for each year of the holding period
                
                8. **📌 Risk Assessment**: Brief analysis of key risks and sensitivities
                
                9. **📌 Conclusion**: Summary of findings and investment recommendation
                
                OMITTING ANY OF THESE SECTIONS WILL RESULT IN AN INCOMPLETE REPORT.
                
                ## Your Team
                You have a team of expert specialized agents:
                
                1. **Expert Research Agent**: Has advanced web scraping capabilities to gather accurate market data, industry benchmarks, and comparable investment metrics.
                
                2. **Expert Assumption Generator**: Takes inputs from both the initial request and the Research Agent to generate realistic, defensible assumptions. These assumptions must be:
                   - Grounded in current market realities
                   - Consistent with historical patterns
                   - Reflective of the specific asset class characteristics
                   - Properly cited with sources when possible
                
                3. **Expert Metrics Deriver**: Determines the most relevant financial metrics for the specific investment opportunity and how they should be calculated. This agent ensures:
                   - All metrics are directly relevant to the asset class
                   - Calculations follow industry-standard methodologies
                   - Key metrics are presented across multiple timeframes (annual, cumulative, etc.)
                   - Risk-adjusted returns are properly calculated
                
                4. **Expert Financial Modeler**: Creates detailed financial projections incorporating all inputs. The model must include:
                   - Comprehensive cash flow statements showing all revenue streams and expenses
                   - Realistic capital depreciation schedules
                   - Clear distinction between gross and net yields
                   - Proper time-value adjustments
                   - Sensitivity analyses across different variables
                
                ## Report Structure Requirements
                
                Your final output MUST include the following sections in this order:
                
                1. **Executive Summary**: A concise overview of the investment opportunity, key findings, and investment recommendations (1-2 paragraphs)
                
                2. **Investment Overview**: Brief description of the investment vehicle, its structure, and key features (1-2 paragraphs)
                
                3. **Key Financial Metrics Summary**: A table showing the most critical metrics across all scenarios
                
                4. **Detailed Assumptions**:
                   - List ALL assumptions made for each scenario (bull, base, bear)
                   - Include market rates, utilization rates, capacity calculations, etc.
                   - Explain WHY each assumption was chosen with brief justification
                
                5. **Step-by-Step Calculations**:
                   - SHOW the actual calculation formulas used for ALL major figures
                   - For each revenue stream, DEMONSTRATE the mathematical calculation with all variables
                   - For expenses, depreciation, and yields, SHOW the exact formulas with numbers
                   - Example: "Annual Inference Revenue = Tokens per second × Concurrent requests × Seconds per hour × Hours per day × Days per year × Utilization rate × Price per token"
                   - Include the actual numbers in each formula to show transparency
                
                6. **Scenario Analysis**: Detailed breakdown of all three scenarios with full calculations
                
                7. **Year-by-Year Projections**: Tables showing the projected performance for each year of the holding period
                
                8. **Risk Assessment**: Brief analysis of key risks and sensitivities
                
                9. **Conclusion**: Summary of findings and investment recommendation
                
                ## Critical Requirements for the Output
                
                1. **Calculation Transparency**: You MUST show ALL formulas and calculations used to derive key figures. Do not just present the final numbers - show HOW they were calculated.
                
                2. **Scenario Modeling**: You MUST create three distinct scenarios:
                   - **Bull Case**: Represents optimistic but realistic outcomes (NOT extreme best-case)
                   - **Base Case**: Represents the most likely/expected outcome based on current data
                   - **Bear Case**: Represents challenging conditions that should result in minimal or negative returns
                   
                   The scenarios should show MEANINGFUL differences in outcomes, especially between bull and bear cases.
                
                3. **Yield Calculations**: 
                   - Gross Yield must accurately represent total returns before subtracting expenses
                   - Net Yield must properly account for ALL costs including depreciation, maintenance, and operating expenses
                   - The relationship between gross and net yield must be mathematically consistent and realistic
                   - SHOW the exact calculation for BOTH gross and net yield with the formula and numbers used
                
                4. **Validation Steps**:
                   - Cross-check all calculations for mathematical accuracy
                   - Verify that the model adheres to the specific parameters in the request
                   - Ensure all assumptions are explicitly stated and justified
                   - Confirm that depreciation schedules match the asset type and holding period
                   - Verify that bear case scenarios reflect genuinely challenging conditions (near breakeven or negative returns)
                
                5. **Output Format**:
                   - Present a comprehensive executive summary
                   - Include detailed tables for each scenario
                   - Provide clear year-by-year projections
                   - Highlight key metrics that would most influence an investment decision
                   - Include sensitivity analysis showing how changes in key variables affect outcomes
                   - Use proper markdown formatting for all tables and sections
                   - Make all numbers easy to read with proper comma formatting for thousands
                
                ## Explanation Requirements
                
                1. **Narrative Quality**: Provide clear, professional narrative explanations that an institutional investor would expect
                
                2. **Assumption Justification**: For EACH major assumption, provide a brief justification of why that value was chosen
                
                3. **Calculation Walkthrough**: For each major financial figure, provide the step-by-step calculation that shows exactly how it was derived
                
                4. **Scenario Differences**: Clearly explain what factors drive the differences between scenarios
                
                5. **Investment Thesis**: Provide a clear investment thesis based on the model results
                
                ## Your Workflow
                1. First, ensure you understand the investment opportunity completely
                2. Direct your Research Agent to gather relevant market data
                3. Have your Assumption Generator create properly calibrated assumptions based on the research
                4. Direct your Metrics Deriver to identify and define the critical metrics
                5. Have your Financial Modeler build the comprehensive model
                6. CRITICALLY REVIEW the final output for errors, inconsistencies, or unrealistic projections
                7. If the output fails any validation criteria, require the team to revise their work
                
                ## Quality Control
                The buck stops with you. Your professional reputation depends on producing accurate, realistic, and valuable financial models. 
                If anything seems incorrect, overly optimistic, or mathematically inconsistent, you must address it before presenting the final output.
                
                CRITICAL: Before finalizing any model, verify that:
                1. The model accurately reflects the specific assets, costs, and revenue streams described in the request
                2. The scenarios show meaningful differences with the bear case presenting genuinely challenging conditions
                3. All calculations can be traced and verified
                4. No reinvestment or additional purchases are included unless specifically requested
                5. The time period matches exactly what was requested
                6. ALL calculations are shown with both the formula AND the actual numbers
                
                Remember: Institutional investors rely on your analysis to make multi-million dollar decisions. Accuracy, transparency, and comprehensive detail are paramount.
            """),
            add_datetime_to_instructions=True,
            enable_agentic_context=True,
            share_member_interactions=True,
            show_members_responses=True,
            show_tool_calls=True,
            markdown=True
        )
        
        message = f"Team created with {len(team.members)} members"
        logger.info(message)
        log_to_memory(message)
        
        message = f"Processing message (length: {len(body.message)})"
        logger.info(message)
        log_to_memory(message)
        
        # Log the input message
        message_preview = body.message[:150] + "..." if len(body.message) > 150 else body.message
        message = f"Input message: {message_preview}"
        logger.info(message)
        log_to_memory(message)

        # Create a streaming wrapper that captures chunks into memory
        async def memory_streaming_wrapper(team, message):
            logger.info("Starting streaming response")
            log_to_memory("Starting streaming response")
            
            run_response = await team.arun(message, stream=True)
            
            chunk_count = 0
            async for chunk in run_response:
                chunk_count += 1
                if chunk_count % 20 == 0:  # Log every 20th chunk to avoid excessive logging
                    debug_message = f"Streaming chunk {chunk_count}: {chunk.content[:50]}..."
                    logger.debug(debug_message)
                    if body.verbose_logging:
                        log_to_memory(debug_message)
                yield chunk.content
            
            complete_message = f"Completed streaming response with {chunk_count} chunks"
            logger.info(complete_message)
            log_to_memory(complete_message)

        if body.stream:
            try:
                message = f"Starting streaming response for request ID: {request_id}"
                logger.info(message)
                log_to_memory(message)
                
                return StreamingResponse(
                    memory_streaming_wrapper(team, body.message),
                    media_type="text/event-stream",
                )
            except Exception as e:
                error_message = f"Error in streaming for request ID {request_id}: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                return JSONResponse(
                    content={"error": f"Streaming error: {str(e)}"},
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        else:
            try:
                message = f"Starting non-streaming response for request ID: {request_id}"
                logger.info(message)
                log_to_memory(message)
                
                response = await team.arun(body.message, stream=False)
                
                complete_message = f"Completed non-streaming response for request ID: {request_id}"
                logger.info(complete_message)
                log_to_memory(complete_message)
                
                return response.content
            except Exception as e:
                error_message = f"Error in non-streaming response for request ID {request_id}: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                return JSONResponse(
                    content={"error": f"Processing error: {str(e)}"},
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
                
    except ValueError as e:
        # Handle validation errors (e.g., invalid API key format)
        error_message = f"Validation error: {str(e)}"
        logger.warning(error_message)
        log_to_memory(error_message)
        
        return JSONResponse(
            content={"error": f"Validation error: {str(e)}"},
            status_code=HTTPStatus.BAD_REQUEST
        )
    except Exception as e:
        # Handle any other unexpected errors
        error_message = f"Error in run_task: {str(e)}"
        logger.error(error_message)
        log_to_memory(error_message)
        
        return JSONResponse(
            content={"error": "An error occurred while processing the task"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

class APIKeyCheckRequest(BaseModel):
    """Request model for checking API key validity"""
    provider: str
    api_key: str

@task_router.post("/check-api-key", status_code=status.HTTP_200_OK, tags=["Health"])
async def check_api_key(body: APIKeyCheckRequest):
    """
    Check if the provided API key is valid for the specified provider
    """
    try:
        # Create a minimal model to test API key validity
        model = create_model(
            provider=body.provider,
            api_key=body.api_key
        )
        
        # Test a simple query
        test_message = "Hello, are you working?"
        try:
            # Attempt a quick, minimal-token query
            response = await model.aget_completion(test_message, max_tokens=10)
            return {"status": "valid", "provider": body.provider}
        except Exception as e:
            logger.warning(f"API key test failed: {str(e)}")
            return JSONResponse(
                content={"status": "invalid", "provider": body.provider, "error": str(e)},
                status_code=HTTPStatus.BAD_REQUEST
            )
    except Exception as e:
        logger.error(f"Error testing API key: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": f"Could not test API key: {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

# Create the FastAPI app
app = FastAPI(
    title="Financial Modeling API",
    description="API for financial modeling using a coordinated team of specialized agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the task router
app.include_router(task_router)

# Add root endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok", 
        "message": "Financial Modeling API is running",
        "supported_providers": ["openai", "anthropic", "formation"],
        "api_version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Check system health, including model provider availability
    """
    try:
        # This is a simple system health check
        # We're not checking model provider availability here as that requires API keys
        return {
            "status": "healthy",
            "api": "operational",
            "timestamp": datetime.datetime.now().isoformat(),
            "providers": {
                "openai": "requires_api_key",
                "anthropic": "requires_api_key",
                "formation": "requires_api_key"
            },
            "message": "Use the /task/check-api-key endpoint to verify specific provider API keys"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            },
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

# Run the server when executed directly
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
