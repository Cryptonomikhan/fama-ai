from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from src.models.factory import create_model
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
import logging
from textwrap import dedent
from typing import Any, Optional, Iterator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class MetricsDerivingAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        searcher_data: Optional[str] = None,
        assumption_data: Optional[str] = None,
        **kwargs: Any
    ):

        logger.info("Initializing AssumptionGenerator Agent ")

        # Store the data first
        self.searcher_data = searcher_data
        self.assumption_data = assumption_data

        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Build tools list based on availability
        tools = [ThinkingTools()]

        # Define base instructions template
        instructions_template = dedent("""\
            ## Using the think tool
            Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                - List the specific rules that apply to the current request
                - Check if all required information is collected
                - Verify that the planned action complies with all policies
                - Iterate over tool results for correctness

            ## Rules
                - Use the gathered data in {searcher_data_placeholder} and {assumption_data_placeholder}
                - Use the think tool to think about the data collected.
                - If the data is relevant to the task at hand use it to derive/deduce key metrics that we should model in the financial model.
                - Structured the metrics in JSON.
                - Its expected that you will use the think tool generously to jot down thoughts and ideas.
                - Your job is to build comprehensive, reasonable metrics that a sophisticated financial model for the investment opportunity being assessed would require. 
                - When you are done thinking take additional actions if necessary to complete the task.
                - You ALWAYS reference {searcher_data_placeholder} and {assumption_data_placeholder} in deriving your metrics
        """)

        # Format the instructions with the data
        formatted_instructions = instructions_template.format(
            searcher_data_placeholder=self.searcher_data or "input data",
            assumption_data_placeholder=self.assumption_data or "input data"
        )

        self.agent = Agent(
            name="Assumption Generator Agent",
            model=model,
            tools=tools,
            role=dedent("""\
                Your role is to build comprehensive list of key
                financial metrics for a sophisticated and high quality,
                accurate, and comprehensive financial model to the investment
                opportunity.\
            """),
            description=dedent("""\
                You are Fama Metrics Expert, a distinguished financial analyst
                that is well known for deducing the metrics that a comprehensive
                financial model should contain for a given investment
                opportunity. You always use reasining to develop a
                comprehensive list of key metrics on both the return
                and expense side, You always organize and justify the metrics.
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

    searcher_response: RunResponse = searcher.agent.run("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms")
    searcher_data = searcher_response.content

    pprint_run_response(searcher_response, markdown=True)

    assumption_generator = AssumptionGeneratorAgent(
        provider="openai",
        model_id="gpt-4o",
        data=searcher_data
    )

    assumption_response: RunResponse = assumption_generator.agent.run("Build assumptions based on the provided data relevant to building a financial model for a 3 year time frame for a small real estate fund that invests in AI server farms")
    assumption_data = assumption_response.content

    pprint_run_response(searcher_response, markdown=True)

    metrics_deriver = MetricsDerivingAgent(
        provider="openai",
        model_id="gpt-4o",
        searcher_data=searcher_data,
        assumption_data=assumption_data
    )

    metrics_deriver.agent.print_response("Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for a 3 year time frame for a small real estate fund that invests in AI server farms", stream=True, markdown=True)
