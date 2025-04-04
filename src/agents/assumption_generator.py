from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from agno.tools.crawl4ai import Crawl4aiTools
from agno.tools.spider import SpiderTools
from agno.tools.firecrawl import FirecrawlTools
from src.models.factory import create_model
from src.agents.searcher import SearchingAgent
import logging
from textwrap import dedent
from typing import Any, Optional, Iterator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if Spider API key exists
has_spider_api_key = bool(os.environ.get("SPIDER_API_KEY"))

logger = logging.getLogger(__name__)


class AssumptionGeneratorAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        firecrawl: bool = False,
        data: Optional[str] = None,
        use_spider: Optional[bool] = None,
        **kwargs: Any
    ):

        logger.info("Initializing AssumptionGenerator Agent ")
        
        # Store the data first
        self.data = data
        
        # Determine whether to use Spider based on API key availability
        use_spider = has_spider_api_key if use_spider is None else use_spider

        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Build tools list based on availability
        tools = [ThinkingTools()]
        
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

        # Define base instructions template
        instructions_template = dedent("""\
            ## Using the think tool
            Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                - List the specific rules that apply to the current request
                - Check if all required information is collected
                - Verify that the planned action complies with all policies
                - Iterate over tool results for correctness

            ## Rules
                - Use the provided tools to gather data from any URLs provided in {data_placeholder}
                - Use the think tool to think about whether the data collected is relevant to the task at hand.
                - If the data is relevant to the task at hand use it to derive/deduce assumptions for the financial model.
                - Whenever you come across quantitative data, you will structure the data in a way that is easy for other tools to use.
                - Structured quantitative data may be in JSON, Comma Separated, Tab Separated or Table format in markdown.
                - For non-quantitative data it will be written out in markdown format so that it can be parsed and used later.
                - Its expected that you will use the think tool generously to jot down thoughts and ideas.
                - Your job is to build comprehensive, yet concise and reasonable assumptions that will be used to generate a sophisticated financial model for an investment opportunity being assessed. 
                - When you are done thinking take additional actions if necessary to complete the task.
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
        model_id="gpt-4o",
        use_spider=False
    )

    response: RunResponse = searcher.agent.run("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms")
    data = response.content
    
    pprint_run_response(response, markdown=True)
    
    assumption_generator = AssumptionGeneratorAgent(
        provider="openai",
        model_id="gpt-4o",
        data=data,
        use_spider=False  # Explicitly disable Spider tool regardless of API key
    )
    assumption_generator.agent.print_response("Build assumptions based on the provided data relevant to building a financial model for a 3 year time frame for a small real estate fund that invests in AI server farms", stream=True, markdown=True)