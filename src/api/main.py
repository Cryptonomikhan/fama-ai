from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uuid
import logging
import os
import asyncio
import inspect
import time
from functools import wraps
from dotenv import load_dotenv
import re

from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
from src.agents.financial_modeler import FinancialModelingAgent
from src.tools.website_scraper import WebsiteScraperTools

# Patch for Crawl4ai to work with FastAPI
import agno.tools.crawl4ai as crawl4ai_module
from agno.tools.crawl4ai import Crawl4aiTools
import threading
import concurrent.futures

# Create a patch for the web_crawler method to properly handle asyncio
original_web_crawler = Crawl4aiTools.web_crawler

@wraps(original_web_crawler)
def patched_web_crawler(self, url: str, max_length: Optional[int] = None):
    """Patched version that properly handles asyncio in FastAPI using threading
    
    This avoids the "Cannot run the event loop while another loop is running" error
    by running the async operation in a separate thread with its own event loop.
    """
    def run_async_in_thread():
        """Run the async crawler in a separate thread with its own event loop"""
        try:
            # Create a new loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Run the crawler with a timeout
            result = loop.run_until_complete(
                asyncio.wait_for(
                    self._async_web_crawler(url, max_length),
                    timeout=30.0
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.warning(f"Web crawler error in thread: {str(e)}")
            return f"Error fetching webpage content: {str(e)}"

    # Use ThreadPoolExecutor to run the async function in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        try:
            # Submit the task to the executor and get the result with a timeout
            future = executor.submit(run_async_in_thread)
            return future.result(timeout=35.0)  # Add extra timeout for thread execution
        except (concurrent.futures.TimeoutError, Exception) as e:
            logger.warning(f"Web crawler thread execution error: {str(e)}")
            return "Error fetching webpage content: Execution timed out or failed"

# Apply the patch
Crawl4aiTools.web_crawler = patched_web_crawler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a simple test API key - hardcoded for development
TEST_API_KEY = "test-api-key-1234"

# Create FastAPI app
app = FastAPI(title="Financial Modeling API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class ModelRequest(BaseModel):
    description: str = Field(..., description="Investment description")
    openai_api_key: str = Field(..., description="Client's OpenAI API key (required)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    timeout: Optional[int] = Field(default=600, description="Timeout in seconds for the entire request")

# Define response model
class ModelResponse(BaseModel):
    request_id: str
    search_results: str
    assumptions: str
    metrics: str
    financial_model: str

@app.post("/api/model", response_model=ModelResponse)
async def create_model(
    request: ModelRequest,
    x_api_key: Optional[str] = Header(None)
):
    # Verify API key
    if x_api_key != TEST_API_KEY:
        logger.warning(f"Invalid API key provided. Use test key: {TEST_API_KEY}")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    logger.info(f"Processing request {request_id}")
    
    # Set a timeout for the entire request
    timeout = request.timeout or 600  # Default 10 minutes
    
    # Define the actual processing function
    async def process_request():
        try:
            # Initialize our website scraper tool
            website_scraper = WebsiteScraperTools(timeout=15)
            
            # Run search agent with our website scraper
            logger.info("Running search agent")
            searcher = SearchingAgent(
                provider="openai",
                model_id="gpt-4o",
                use_spider=False,  # Spider still disabled as it requires API key
                api_key=request.openai_api_key,
                additional_tools=[website_scraper]  # Add our custom website scraper
            )
            search_prompt = f"Gather the information necessary to build a financial model for {request.description}"
            
            # Handle potential coroutine issues
            try:
                search_response = searcher.agent.run(search_prompt)
                if inspect.iscoroutine(search_response):
                    search_response = await search_response
                
                search_results = search_response.content
                if inspect.iscoroutine(search_results):
                    search_results = await search_results
                
                # Add additional context by extracting relevant URLs from the search_results
                # This regex is a basic URL extractor - may need refinement for real-world use
                url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
                urls = re.findall(url_pattern, search_results)
                
                # Limit to first 3 unique URLs to avoid overloading
                unique_urls = list(set(urls))[:3]
                
                if unique_urls:
                    logger.info(f"Extracting additional context from {len(unique_urls)} URLs")
                    try:
                        # Scrape content from the URLs (now returns a formatted string)
                        additional_context = website_scraper.scrape_multiple_urls(
                            unique_urls, 
                            max_length_per_url=5000  # Limit content length per URL
                        )
                        
                        # Add the scraped content to the search results
                        search_results += "\n\n" + additional_context
                    except Exception as e:
                        logger.warning(f"Error extracting additional context: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error in search agent: {str(e)}")
                search_results = f"Error in search process: {str(e)}"
            
            logger.info("Search agent completed with additional context extraction")
            
            # Run assumption generator
            logger.info("Running assumption generator")
            assumption_generator = AssumptionGeneratorAgent(
                provider="openai",
                model_id="gpt-4o",
                data=search_results,
                use_spider=False,
                api_key=request.openai_api_key,
                additional_tools=[website_scraper]  # Pass the website scraper to the assumption generator
            )
            assumption_prompt = f"Build assumptions based on the provided data relevant to building a financial model for {request.description}"
            
            # Handle potential coroutine issues
            try:
                assumption_response = assumption_generator.agent.run(assumption_prompt)
                if inspect.iscoroutine(assumption_response):
                    assumption_response = await assumption_response
                    
                assumptions = assumption_response.content
                if inspect.iscoroutine(assumptions):
                    assumptions = await assumptions
            except Exception as e:
                logger.error(f"Error in assumption generator: {str(e)}")
                assumptions = f"Error in assumption generation process: {str(e)}"
                
            logger.info("Assumption generator completed")
            
            # Run metrics deriver
            logger.info("Running metrics deriver")
            metrics_deriver = MetricsDerivingAgent(
                provider="openai",
                model_id="gpt-4o",
                searcher_data=search_results,
                assumption_data=assumptions,
                api_key=request.openai_api_key
            )
            metrics_prompt = f"Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for {request.description}"
            
            # Handle potential coroutine issues
            try:
                metrics_response = metrics_deriver.agent.run(metrics_prompt)
                if inspect.iscoroutine(metrics_response):
                    metrics_response = await metrics_response
                    
                metrics = metrics_response.content
                if inspect.iscoroutine(metrics):
                    metrics = await metrics
            except Exception as e:
                logger.error(f"Error in metrics deriver: {str(e)}")
                metrics = f"Error in metrics derivation process: {str(e)}"
                
            logger.info("Metrics deriver completed")
            
            # Run financial modeler
            logger.info("Running financial modeler")
            financial_modeler = FinancialModelingAgent(
                provider="openai",
                model_id="gpt-4o",
                searcher_data=search_results,
                assumption_data=assumptions,
                metrics_data=metrics,
                api_key=request.openai_api_key
            )
            model_prompt = f"""
            Based on the provided search data, assumptions, and metrics, build a comprehensive financial model for {request.description}.
            
            Your financial model should include:
            1. Income statements
            2. Cash flow statements
            3. Scenario analysis (bull, bear, baseline)
            4. Key financial metrics (NPV, IRR, payback period)
            5. Appropriate visualizations
            """
            
            # Handle potential coroutine issues
            try:
                model_response = financial_modeler.agent.run(model_prompt.strip())
                if inspect.iscoroutine(model_response):
                    model_response = await model_response
                    
                financial_model = model_response.content
                if inspect.iscoroutine(financial_model):
                    financial_model = await financial_model
            except Exception as e:
                logger.error(f"Error in financial modeler: {str(e)}")
                financial_model = f"Error in financial modeling process: {str(e)}"
                
            logger.info("Financial modeler completed")
            
            # Return the response
            return ModelResponse(
                request_id=request_id,
                search_results=search_results,
                assumptions=assumptions,
                metrics=metrics,
                financial_model=financial_model
            )
            
        except Exception as e:
            logger.error(f"Error generating model: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    try:
        # Run with timeout
        return await asyncio.wait_for(process_request(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Request {request_id} timed out after {timeout} seconds")
        raise HTTPException(
            status_code=408, 
            detail=f"Request timed out after {timeout} seconds. Please try again with a simpler query or increase the timeout."
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True) 