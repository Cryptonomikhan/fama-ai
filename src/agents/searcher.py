from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.thinking import ThinkingTools
from agno.tools.crawl4ai import Crawl4aiTools
from agno.tools.firecrawl import FirecrawlTools
from agno.tools.spider import SpiderTools
from src.models.factory import create_model
import logging
from textwrap import dedent
from typing import Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if Spider API key exists
has_spider_api_key = bool(os.environ.get("SPIDER_API_KEY"))

logger = logging.getLogger(__name__)


class SearchingAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        firecrawl: bool = False,
        use_spider: Optional[bool] = None,
        **kwargs: Any
    ):

        logger.info("Initializing WebSearch Agent ")
        
        # Determine whether to use Spider based on API key availability
        use_spider = has_spider_api_key if use_spider is None else use_spider
        
        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Build tools list
        tools = [DuckDuckGoTools(), ThinkingTools()]
        
        if firecrawl:
            tools.append(FirecrawlTools(scrape=True, crawl=True))
        else:
            tools.append(Crawl4aiTools(max_length=None))
            
        # Only add Spider if we have an API key
        if use_spider:
            tools.append(SpiderTools())
            logger.info("Spider tool enabled")
        else:
            logger.info("Spider tool disabled (no API key)")

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
            instructions=dedent("""\
                ## Using the think tool
                Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                    - List the specific rules that apply to the current request
                    - Check if all required information is collected
                    - Verify that the planned action complies with all policies
                    - Iterate over tool results for correctness

                ## Rules
                    - Use the DuckDuckGo and available crawling tools to search the web for relevant information
                    - When you find a site that may contain relevant information use the crawling tools provided to crawl and scrape the website.
                    - Convert the data found into the website into a format that is easy to reason about.
                    - Use the think tool to think about whether the data collected is relevant to the task at hand.
                    - Whenever you come across quantitative data, you will structure the data in a way that is easy for other tools to use.
                    - Structured quantitative data may be in JSON, Comma Separated, Tab Separated or Table format in markdown.
                    - For non-quantitative data it will be written out in markdown format so that it can be parsed and used later.
                    - Its expected that you will use the think tool generously to jot down thoughts and ideas.
                    - Your job is to search for and gather information, and to present the information in a comprehensible and complete manner.
                    - When you are done thinking take additional actions if necessary to complete the task.
            """),
            show_tool_calls=True,
            markdown=True
        )


if __name__ == "__main__":

    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o",
        use_spider=False  # Explicitly disable Spider tool regardless of API key
    )

    searcher.agent.print_response("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms", stream=True)
