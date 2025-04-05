from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from agno.tools.firecrawl import FirecrawlTools
from src.models.factory import create_model
from src.agents.searcher import SearchingAgent
from src.tools.website_scraper import WebsiteScraperTools
import logging
from textwrap import dedent
from typing import Any, Optional, Iterator, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class AssumptionGeneratorAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        firecrawl: bool = False,
        firecrawl_api_key: Optional[str] = None,
        data: Optional[str] = None,
        additional_tools: List = None,
        **kwargs: Any
    ):

        logger.info("Initializing AssumptionGenerator Agent ")
        
        # Store the data first
        self.data = data

        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Build tools list based on availability
        tools = [ThinkingTools()]
        
        # Always add our custom WebsiteScraperTools
        tools.append(WebsiteScraperTools())
        logger.info("Added WebsiteScraperTools for webpage crawling")
        
        # Add Firecrawl if explicitly requested and API key is provided
        if firecrawl and firecrawl_api_key:
            tools.append(FirecrawlTools(scrape=True, crawl=True, api_key=firecrawl_api_key))
            logger.info("Firecrawl tool enabled")
        elif firecrawl:
            firecrawl_api_key = os.environ.get("FIRECRAWL_API_KEY")
            if firecrawl_api_key:
                tools.append(FirecrawlTools(scrape=True, crawl=True, api_key=firecrawl_api_key))
                logger.info("Firecrawl tool enabled with API key from environment")
            else:
                logger.warning("Firecrawl requested but no API key provided - falling back to WebsiteScraperTools only")

        # Add any additional tools provided
        if additional_tools:
            for tool in additional_tools:
                tools.append(tool)
                logger.info(f"Added additional tool: {tool.name}")

        # Define base instructions template
        instructions_template = dedent("""\
            ## Using the think tool
            Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                - List the specific rules that apply to the current request
                - Check if all required information is collected
                - Verify that the planned action complies with all policies
                - Iterate over tool results for correctness

            ## Rules
                - Use the provided data as your primary source of information
                - If you need to verify information or get additional details from URLs in the data, use the WebsiteScraperTools:
                  - scrape_url: Extract content from a single URL
                  - scrape_multiple_urls: Extract content from multiple URLs in parallel
                  - summarize_webpage: Get a summary of a webpage including title, content, and links
                - Use the think tool to evaluate whether the data is relevant to generating assumptions
                - If the data is relevant, use it to derive/deduce assumptions for the financial model
                - Create three distinct sets of assumptions: bull case, baseline case, and bear case
                - Structure quantitative data in JSON, CSV, TSV, or markdown table format for easy use by other tools
                - Format non-quantitative assumptions in markdown for clarity and ease of use
                - Use the think tool generously to develop your assumptions with clear reasoning
                - Your job is to build comprehensive, defensible, and realistic assumptions for the financial model
                - Always justify your assumptions with data and cite sources where applicable
        """)
        
        # Format the instructions with the data
        formatted_instructions = instructions_template.format(data_placeholder=self.data or "input data")

        self.agent = Agent(
            name="Assumption Generator Agent",
            model=model,
            tools=tools,
            role=dedent("""\
                Your role is to build sophisticated and reasonable assumptions
                to be used in generating a sophisticated and high quality,
                accurate, and comprehensive financial model to the investment
                opportunity.\
            """),
            description=dedent("""\
                You are Fama Assumer, a distinguished assumption creator
                that is well known for deriving and deducing high quality
                assumptions based on relevant information for the creation
                of a sophisticated financial model. You always craft the
                assumptions for multiple scenarios: bull case, bear case,
                and baseline case. Your assumptions are clear and concise,
                yet pointed and easy to comprehend and understand.
                You always organize your assumptions and cite sources to
                relevant information that you used to derive and deduce
                your assumptions.
            """),
            instructions=formatted_instructions,
            show_tool_calls=True,
            markdown=True
        )


if __name__ == "__main__":
    from agno.utils.pprint import pprint_run_response

    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o"
    )

    response: RunResponse = searcher.agent.run("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms")
    data = response.content
    
    pprint_run_response(response, markdown=True)
    
    assumption_generator = AssumptionGeneratorAgent(
        provider="openai",
        model_id="gpt-4o",
        data=data
    )
    assumption_generator.agent.print_response("Build assumptions based on the provided data relevant to building a financial model for a 3 year time frame for a small real estate fund that invests in AI server farms", stream=True, markdown=True)