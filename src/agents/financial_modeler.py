from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from src.models.factory import create_model
from src.tools.financial_calculations import FinancialCalculationTools
from src.tools.model_formatting import ModelFormattingTools
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
import logging
from textwrap import dedent
from typing import Any, Dict, List, Optional, Iterator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class FinancialModelingAgent:
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        searcher_data: Optional[str] = None,
        assumption_data: Optional[str] = None,
        metrics_data: Optional[str] = None,
        **kwargs: Any
    ):
        logger.info("Initializing Financial Modeling Agent")
        
        # Store input data
        self.searcher_data = searcher_data
        self.assumption_data = assumption_data
        self.metrics_data = metrics_data
        
        # Initialize the model
        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Initialize tools as toolkit instances
        tools = [
            ThinkingTools(),
            FinancialCalculationTools(),
            ModelFormattingTools()
        ]
        
        # Instructions for the agent
        instructions_template = dedent("""
            ## Using the think tool
            Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
                - Analyze the data from previous agents
                - Determine which financial calculations are needed
                - Plan how to structure the model
                - Ensure consistency across all calculations
                
            ## IMPORTANT: Consistency requirements
                - ENSURE that the key metrics (NPV, IRR, Payback Period) shown at the top of the report match exactly the values for the baseline scenario
                - ALL calculations must be derived from the same underlying assumptions for each scenario
                - Use a consistent set of input values for ALL calculations within each scenario
                - DOUBLE-CHECK that all related metrics are consistent across the income statement, cash flow statement, and scenario analysis
                - If cash flows are used in multiple calculations (like NPV, IRR, payback period), use the EXACT SAME cash flow values in all calculations
                - Verify that all formulas and calculations are applied consistently across scenarios
                - Carefully check that growth rates and assumptions align with the scenario descriptions
                
            ## Rules
                - NEVER perform complex mathematical calculations yourself
                - ALWAYS use the provided calculation tools for quantitative analysis
                - Use the input data from researcher findings, assumptions, and metrics
                - Structure all outputs in a consistent, machine-readable format
                - Provide clear narrative context around the calculations
                - For each calculation, explain the inputs, methodology, and significance of the outputs
                - Base your financial calculations on the data provided by the search agent, assumption generator, and metrics deriver
                - Generate both income statement and cash flow statement for the investment model
                - Perform scenario analysis for bull, bear, and baseline cases
                - Calculate NPV, IRR, and payback period for each scenario
                - Use the format_model_summary function to generate the final report in markdown format
                - Include appropriate visualizations to illustrate key financial projections
                - When reporting the key metrics at the top of the model summary, use the baseline scenario metrics
                - ALWAYS check your inputs and outputs for logical consistency before finalizing the model
                
            ## Modeling Workflow
                1. Define consistent input assumptions for each scenario
                2. Build the income statement and cash flow statement using consistent inputs
                3. Calculate key metrics (NPV, IRR, payback period) using the exact same cash flows across all calculations
                4. Perform scenario analysis with the same assumptions used in previous steps
                5. Verify all numbers match before finalizing the model
                
            ## Debugging and Testing
                - After building each component, double-check that all numbers align with previous calculations
                - If there are inconsistencies, trace the issue back to the source and recalculate
                - Verify that scenario-specific numbers maintain proper relationships (bull case > baseline > bear case where applicable)
        """)
        
        # Initialize the agent
        self.agent = Agent(
            name="Financial Modeling Agent",
            model=model,
            tools=tools,
            role=dedent("""
                Your role is to build a sophisticated financial model using the data provided by previous agents.
                You will use specialized calculation tools to perform all quantitative analysis, ensuring accuracy
                and reliability in the financial projections. Above all, you must maintain consistency across
                all calculations and ensure that the model is coherent and logically sound.
            """),
            description=dedent("""
                You are Fama Financial Modeler, a distinguished financial modeling expert known for creating
                accurate, comprehensive, and insightful financial models for investment opportunities.
                Your models account for multiple scenarios (bull, bear, baseline) and include all standard
                financial statements and analyses required for investment decision-making.
                
                You NEVER perform complex calculations yourself, but ALWAYS use appropriate financial
                calculation tools to ensure accuracy. You provide clear documentation and context around
                all calculations. You are meticulous about ensuring consistency across all parts of the model.
            """),
            instructions=instructions_template,
            show_tool_calls=True,
            markdown=True
        )


if __name__ == "__main__":
    from agno.utils.pprint import pprint_run_response
    
    # Run the search agent
    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o",
        use_spider=False
    )
    
    print("\n--- Running Search Agent ---\n")
    searcher_response = searcher.agent.run("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms")
    searcher_data = searcher_response.content
    
    print("\n--- Search Results ---\n")
    pprint_run_response(searcher_response, markdown=True)
    
    # Run the assumption generator agent
    print("\n--- Running Assumption Generator Agent ---\n")
    assumption_generator = AssumptionGeneratorAgent(
        provider="openai",
        model_id="gpt-4o",
        data=searcher_data,
        use_spider=False
    )
    
    assumption_response = assumption_generator.agent.run("Build assumptions based on the provided data relevant to building a financial model for a 3 year time frame for a small real estate fund that invests in AI server farms")
    assumption_data = assumption_response.content
    
    print("\n--- Assumption Results ---\n")
    pprint_run_response(assumption_response, markdown=True)
    
    # Run the metrics deriver agent
    print("\n--- Running Metrics Deriver Agent ---\n")
    metrics_deriver = MetricsDerivingAgent(
        provider="openai",
        model_id="gpt-4o",
        searcher_data=searcher_data,
        assumption_data=assumption_data
    )
    
    metrics_response = metrics_deriver.agent.run("Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for a 3 year time frame for a small real estate fund that invests in AI server farms")
    metrics_data = metrics_response.content
    
    print("\n--- Metrics Results ---\n")
    pprint_run_response(metrics_response, markdown=True)
    
    # Run the financial modeling agent
    print("\n--- Running Financial Modeling Agent ---\n")
    financial_modeler = FinancialModelingAgent(
        provider="openai",
        model_id="gpt-4o",
        searcher_data=searcher_data,
        assumption_data=assumption_data,
        metrics_data=metrics_data
    )
    
    # Get and print the financial model
    model_prompt = """
    Based on the provided search data, assumptions, and metrics, build a comprehensive financial model for a 3-year timeframe
    for a small real estate fund that invests in AI server farms.
    
    Your financial model should include:
    1. Income statements for all 3 years
    2. Cash flow statements for all 3 years
    3. Scenario analysis (bull, bear, baseline)
    4. Key financial metrics (NPV, IRR, payback period)
    5. Appropriate visualizations
    
    IMPORTANT: 
    - Ensure that your calculations are consistent across all parts of the model. 
    - The key metrics shown at the top of your summary should match exactly with the values in your baseline scenario.
    - All calculations for each scenario should use the same underlying assumptions.
    - The cash flows used for calculating NPV, IRR, and payback period should be identical.
    - Format your output using TABLES for all financial statements and scenario analysis, not bullet points.
    - Use a clean, tabular format for the income statement, cash flow statement, and scenario analysis.
    - Include proper column and row headers for all tables.
    
    Remember to use the calculation tools for all numerical computations and present the results in a well-structured format.
    """
    
    model_response = financial_modeler.agent.run(model_prompt.strip())
    
    print("\n--- Financial Model Results ---\n")
    pprint_run_response(model_response, markdown=True)
    
    print("\n--- Process Complete ---\n")
