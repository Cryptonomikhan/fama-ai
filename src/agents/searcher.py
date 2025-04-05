from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.thinking import ThinkingTools
from agno.tools.firecrawl import FirecrawlTools
from src.models.factory import create_model
from src.tools.website_scraper import WebsiteScraperTools
import logging
from textwrap import dedent
from typing import Any, Optional, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class SearchingAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        firecrawl: bool = False,
        firecrawl_api_key: Optional[str] = None,
        additional_tools: List = None,
        **kwargs: Any
    ):

        logger.info("Initializing WebSearch Agent ")
        
        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Build tools list
        tools = [DuckDuckGoTools(), ThinkingTools()]
        
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

        # Update instructions to mention our website scraper
        instructions = dedent("""\
            ## Using the think tool
            Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                - List the specific rules that apply to the current request
                - Check if all required information is collected
                - Verify that the planned action complies with all policies
                - Iterate over tool results for correctness

            ## Rules
                - Use the DuckDuckGo search tool to find relevant information on the web
                - When you find a site that may contain relevant information, use the WebsiteScraperTools to:
                  - scrape_url: Extract content from a single URL
                  - scrape_multiple_urls: Extract content from multiple URLs in parallel
                  - summarize_webpage: Get a summary of a webpage including title, content, and links
                - Convert the data found into a format that is easy to reason about
                - Use the think tool to evaluate whether the collected data is relevant to the task
                - Structure quantitative data in JSON, CSV, TSV, or markdown table format for easy use by other tools
                - Format non-quantitative data in markdown for parsing and later use
                - Use the think tool generously to develop thoughts and ideas
                - Your job is to gather comprehensive information and present it in a clear, well-organized manner
                - When done thinking, take additional actions if necessary to complete the task
                - Always provide sources for the information you gather, including URLs
        """)

        self.agent = Agent(
            name="Web Search Agent",
            model=model,
            tools=tools,
            role=dedent("""\
                Your role is to gather information related to the investment
                opportunity that is relevant to building a sophisticated
                and high quality financial model for the opportunity.\
            """),
            description=dedent("""\
                You are Fama Datagatherer, a distinguished research assisstant
                that is well known for searching to the end of the earth to
                find relevant inforamtion for a given subject. Today you are
                aiding in building a sophisticated financial model for an
                investment opportunity. You search the web to find information
                that can be used to derive assumptions, determine key metrics,
                risk factors, and other key components to a financial model.
                Once you've gathered the necessary information you structure it
                in a way that makes it usable by your teammates and others.

                You always organize data and provide sources for it, including
                links to webpages where you found the data.
            """),
            instructions=instructions,
            show_tool_calls=True,
            markdown=True
        )


if __name__ == "__main__":

    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o"
    )

    searcher.agent.print_response("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms", stream=True)
