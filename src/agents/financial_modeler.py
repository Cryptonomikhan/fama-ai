from agno.agent import Agent
from agno.tools.thinking import ThinkingTools
from src.tools.math_tools import MathTools
from src.models.factory import create_model
from src.tools.financial_calculations import FinancialCalculationTools
from src.tools.model_formatting import ModelFormattingTools
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
from src.knowledge.logging import wrap_knowledge_base
import logging
from textwrap import dedent
from typing import Any, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class FinancialModelingAgent:
    """
    Agent specialized in creating comprehensive financial models based on research, assumptions, and metrics.
    
    This agent builds sophisticated financial models for various investment opportunities. It can leverage data from
    previous agents in the pipeline, as well as knowledge base information, to create accurate, detailed financial
    projections across multiple scenarios (bull, base, and bear cases).
    """
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        searcher_data: Optional[str] = None,
        assumption_data: Optional[str] = None,
        metrics_data: Optional[str] = None,
        additional_tools: Optional[List] = None,
        knowledge_base: Optional[Any] = None,
        search_knowledge: bool = True,
        session_id: Optional[str] = None,
        storage: Optional[Any] = None,
        **kwargs: Any
    ):
        """
        Initialize a FinancialModelingAgent with the specified parameters.
        
        Args:
            provider: Model provider (e.g., "openai", "formation", "anthropic")
            model_id: ID of the model to use
            temperature: Temperature for model generation (higher = more creative, lower = more deterministic)
            max_tokens: Maximum tokens to generate in responses
            searcher_data: Data from the SearchingAgent with market research
            assumption_data: Data from the AssumptionGeneratorAgent with key assumptions
            metrics_data: Data from the MetricsDerivingAgent defining metrics to calculate
            additional_tools: Additional tools to give the agent
            knowledge_base: Knowledge base instance to use for semantic search
            search_knowledge: Whether to search the knowledge base for relevant information
            session_id: Session ID for knowledge tracking across agents
            storage: Optional storage backend for maintaining agent state across sessions
            **kwargs: Additional keyword arguments for the model
        """
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
            ModelFormattingTools(),
            MathTools()
        ]
        
        # Add any additional tools provided
        if additional_tools:
            for tool in additional_tools:
                tools.append(tool)
                logger.info(f"Added additional tool to FinancialModelingAgent: {tool.name}")
        
        # Instructions for the agent
        base_instructions = dedent("""
            ## CRITICAL: Revenue Calculation Requirements
                - For ALL investment types:
                  * ALWAYS calculate realistic annual revenue by considering practical utilization/occupancy rates
                  * Apply appropriate industry standards for capacity utilization
                  * NEVER assume 100% utilization/occupancy; use realistic rates based on the industry
                  * For each investment type, consider the appropriate factors:
                    - Occupancy rates
                    - Seasonality
                    - Demand fluctuations
                    - Maintenance periods
                    - Market competition
                    - Industry benchmarks
                  * Use conservative estimates for bear scenarios and realistic estimates for baseline scenarios
                  * Document all utilization assumptions clearly in your calculations
                  * MANDATORY: Use MathTools for ALL calculations - never perform arithmetic yourself
                  * Break down complex calculations into step-by-step operations using MathTools
                
            ## IMPORTANT: Universal Financial Modeling Principles
                - Follow these principles regardless of investment type:
                  1. Break large calculations into smaller steps using MathTools
                  2. Store intermediate results as variables
                  3. Document the reasoning for each calculation 
                  4. Verify results against industry benchmarks
                  5. Ensure calculations are mathematically sound
                  6. Apply realistic assumptions based on the specific investment context
                  
            ## EXAMPLE: General Investment Calculation Process
                - For a rental property with the following parameters:
                  * Monthly Rental Income: $5,000
                  * Occupancy Rate: 95%
                  * Property Value: $800,000
                  * Annual Property Tax: $6,000
                  * Annual Insurance: $2,400
                  * Annual Maintenance: $3,600
                  * Property Management Fee: 8% of rental income
                
                1. Calculate annual revenue with realistic occupancy:
                   ```
                   monthly_rent = 5000
                   occupancy_rate = 95  # 95% occupancy rate
                   
                   # Calculate effective monthly revenue with occupancy
                   effective_monthly_revenue = math_tools.multiply(
                       monthly_rent, 
                       math_tools.divide(occupancy_rate, 100)
                   )
                   # $5,000 * 0.95 = $4,750 effective monthly revenue
                   
                   # Calculate annual revenue
                   annual_revenue = math_tools.multiply(effective_monthly_revenue, 12)
                   # $4,750 * 12 = $57,000 annual revenue
                   ```
                   
                2. Calculate annual expenses:
                   ```
                   # Example: Property expenses
                   property_tax = 6000
                   insurance = 2400
                   maintenance = 3600
                   property_management = math_tools.multiply(
                       annual_revenue, 
                       math_tools.divide(8, 100)  # 8% management fee
                   )
                   # $57,000 * 0.08 = $4,560 property management fee
                   
                   # Sum all expenses
                   total_expenses = math_tools.add(
                       math_tools.add(property_tax, insurance),
                       math_tools.add(maintenance, property_management)
                   )
                   # $6,000 + $2,400 + $3,600 + $4,560 = $16,560 total expenses
                   ```
                   
                3. Calculate net operating income:
                   ```
                   net_operating_income = math_tools.subtract(annual_revenue, total_expenses)
                   # $57,000 - $16,560 = $40,440 NOI
                   ```
                   
                4. Calculate cap rate and cash-on-cash return:
                   ```
                   property_value = 800000
                   
                   # Calculate cap rate (NOI / Property Value)
                   cap_rate = math_tools.calculate_yield(net_operating_income, property_value)
                   # ($40,440 / $800,000) * 100 = 5.06% cap rate
                   
                   # Calculate cash-on-cash return (for 25% down payment)
                   down_payment = math_tools.multiply(
                       property_value, 
                       math_tools.divide(25, 100)
                   )
                   # $800,000 * 0.25 = $200,000 down payment
                   
                   # Assume annual mortgage payment of $30,000
                   mortgage_payment = 30000
                   cash_flow = math_tools.subtract(net_operating_income, mortgage_payment)
                   # $40,440 - $30,000 = $10,440 annual cash flow
                   
                   cash_on_cash_return = math_tools.calculate_yield(cash_flow, down_payment)
                   # ($10,440 / $200,000) * 100 = 5.22% cash-on-cash return
                   ```
                   
                5. The correct values for this example:
                   - Annual Revenue (95% occupancy): $57,000
                   - Total Annual Expenses: $16,560
                   - Net Operating Income: $40,440
                   - Cap Rate: 5.06%
                   - Cash-on-Cash Return: 5.22%

            {knowledge_base_instruction}

            ## IMPORTANT: Context-Specific Financial Analysis
                - ANALYZE the specific context of each investment opportunity to identify the key metrics investors care about
                - ADAPT your approach to each unique investment by focusing on the metrics mentioned in the description
                - For yield-generating investments, ALWAYS calculate and clearly show:
                  * Gross Yield = (Annual Revenue / Investment Amount) * 100%
                  * Net Yield = (Annual Revenue - Annual Expenses) / Investment Amount * 100%
                - ALWAYS provide detailed, specific figures and percentages for all key metrics across:
                  * Bull Scenario (optimistic case)
                  * Baseline Scenario (expected case) 
                  * Bear Scenario (pessimistic case)
                - If certain metrics are specifically requested in the investment description, PRIORITIZE calculating and highlighting those
                
            ## Using MathTools for ALL Calculations
                - NEVER perform ANY mathematical calculations yourself - even simple ones
                - EVERY numeric calculation MUST use MathTools functions:
                  * For multiplication: math_tools.multiply(a, b)
                  * For division: math_tools.divide(a, b)
                  * For addition: math_tools.add(a, b)
                  * For subtraction: math_tools.subtract(a, b)
                  * For percentages: math_tools.percentage(value, percentage) or math_tools.percentage_of(part, whole)
                  * For yields: math_tools.calculate_yield(annual_income, investment)
                  * For token revenue: math_tools.calculate_hourly_revenue and math_tools.calculate_annual_revenue
                - For specialized calculations relevant to particular investments:
                  * Use the appropriate MathTools methods suitable to that investment type
                - When calculating compounds or sequences:
                  * Break down into individual MathTools operations
                  * Store intermediate results explicitly
                  * Show your reasoning in the think tool
                - DOUBLE-CHECK each calculation by verifying inputs and outputs are reasonable
                
            ## CORRECT Yield Calculation Process
                - For ALL investment types:
                  1. Calculate REALISTIC revenue using appropriate MathTools functions
                     * Use REALISTIC utilization/occupancy values, not theoretical maximums
                     * Apply current market rates appropriate to the investment type
                  2. Calculate annual revenue with REALISTIC utilization/occupancy rates
                     * Rates should reflect industry standards and current market conditions
                  3. Calculate all applicable expenses (operating, maintenance, taxes, etc.)
                  4. Calculate Gross Yield using math_tools.calculate_yield(annual_revenue, investment_amount)
                  5. Calculate Net Yield using math_tools.calculate_yield(annual_revenue - annual_expenses, investment_amount)
                  6. Express all yields as percentages with clear labels
                
            ## IMPORTANT: Consistency and Reality Checking
                - NEVER generate implausible returns (e.g., 10,000% yields or million-dollar returns on small investments)
                - ALL calculations must be derived from the same underlying assumptions for each scenario
                - Use a consistent set of input values for ALL calculations within each scenario
                - DOUBLE-CHECK that all related metrics are consistent across the income statement, cash flow statement
                - If cash flows are used in multiple calculations (like NPV, IRR, payback period), use IDENTICAL cash flow values
                - Verify that your calculations make real-world economic sense - if returns seem too high, revisit your assumptions
                - ALWAYS check your final numbers against the original investment description for plausibility
                
            ## Rules for Numerical Accuracy
                - ALWAYS use MathTools for ALL calculations, even simple ones
                - EVERY percentage must be calculated using math_tools.percentage_of
                - ALWAYS work step by step through complex calculations
                - For each calculation, clearly document the inputs, formula used, and outputs
                - EXPLICITLY calculate and show the following for EACH scenario:
                  * Annual Revenue (broken down by revenue stream)
                  * Annual Expenses (broken down by category)
                  * Net Income
                  * Cash Flow
                  * Gross Yield (as a percentage)
                  * Net Yield (as a percentage)
                  * ROI
                  * IRR
                  * NPV
                  * Payback Period
                - ENSURE Bull > Baseline > Bear values maintain proper relationship for all metrics
                
            ## Table Formatting Requirements
                - ALWAYS present key metrics in a well-formatted markdown table
                - Include a summary table at the top of your response showing:
                  * Gross Yield (%) for all scenarios
                  * Net Yield (%) for all scenarios
                  * IRR (%) for all scenarios
                  * NPV for all scenarios
                  * Payback Period for all scenarios
                - Use the following format for the summary table:
                  ```
                  | Metric | Bull Scenario | Baseline Scenario | Bear Scenario |
                  | ------ | ------------- | ----------------- | ------------- |
                  | Gross Yield | xx.xx% | xx.xx% | xx.xx% |
                  | Net Yield | xx.xx% | xx.xx% | xx.xx% |
                  | IRR | xx.xx% | xx.xx% | xx.xx% |
                  | NPV | $x,xxx,xxx | $x,xxx,xxx | $x,xxx,xxx |
                  | Payback Period | x.xx years | x.xx years | x.xx years |
                  ```
                - Present ALL financial statements in properly formatted tables
                - Use clear column headers and row labels in all tables
                - Format all currency values with appropriate symbols and commas
                - Format all percentages with % symbol and appropriate decimal places
                - NEVER use bullet points or plain text for presenting numerical data
                
            ## Investment Analysis Workflow
                1. Analyze the investment description to identify the type of investment and key metrics
                2. Determine the appropriate inputs needed based on the investment type
                3. Define realistic input assumptions for each scenario
                4. Use MathTools for EVERY calculation in the model
                5. Build income statement and cash flow statement using consistent inputs
                6. Calculate key metrics using identical cash flows across all calculations
                7. Perform reality checks on ALL calculated values
                8. Format results highlighting the metrics most relevant to investors
                
            ## Debugging and Testing
                - After EACH calculation, verify the output is reasonable given the inputs
                - If a calculation yields an unexpected result, trace through each step to find the error
                - After completing a section, cross-check all related values for consistency
                - VERIFY all metrics follow logical relationships (Bull > Baseline > Bear where applicable)
                - If any metric seems unrealistic (too high or too low), re-examine ALL assumptions and calculations
        """)
        
        # Add knowledge base instructions if a knowledge base is provided
        knowledge_base_instruction = ""
        if knowledge_base and search_knowledge:
            # Wrap knowledge base with logging if it hasn't been wrapped already
            if session_id and not hasattr(knowledge_base, '_kb_logging_wrapped'):
                knowledge_base = wrap_knowledge_base(
                    knowledge_base,
                    agent_name="FinancialModelingAgent",
                    session_id=session_id
                )
                knowledge_base._kb_logging_wrapped = True
                logger.info("Knowledge base wrapped with logging for FinancialModelingAgent")
            
            knowledge_base_instruction = dedent("""
            ## Using the Knowledge Base
                - REFERENCE the knowledge base for industry-specific financial modeling approaches and standards
                - SEARCH the knowledge base for comparable investment modeling examples to ensure your calculations align with industry norms
                - VERIFY your financial ratios against knowledge base benchmarks for similar investments
                - ADJUST your financial projections based on historical data available in the knowledge base
                - CHECK the knowledge base for specialized calculation methods specific to this investment type
                - INCORPORATE financial modeling best practices from the knowledge base into your approach
                - CITE knowledge base sources when utilizing specialized calculations or industry-specific methodologies
                - PRIORITIZE knowledge base information over general assumptions when there are conflicts
            """)
            logger.info("Knowledge base provided, updating financial modeling instructions")
        
        # Format the instructions with the knowledge base instruction
        instructions_template = base_instructions.format(knowledge_base_instruction=knowledge_base_instruction)
        
        # Initialize the agent
        self.agent = Agent(
            name="Financial Modeling Agent",
            model=model,
            tools=tools,
            role=dedent("""
                Your role is to build a sophisticated financial model using the data provided by previous agents.
                You must adapt your approach to fit each specific investment context, analyzing what metrics and
                calculations are most relevant for the particular opportunity, and providing detailed numerical
                values for all key metrics including specific yield percentages across scenarios.
            """),
            description=dedent("""
                You are Fama Financial Modeler, a distinguished financial modeling expert known for creating
                accurate, comprehensive, and insightful financial models for diverse investment opportunities.
                
                You excel at adapting your analysis to the specific investment context, identifying the most 
                relevant metrics for each type of investment, and providing detailed calculations of yields,
                returns, and other key metrics across different scenarios.
                
                You NEVER perform complex calculations yourself, but ALWAYS use appropriate financial
                calculation tools to ensure accuracy. You provide clear documentation and context around
                all calculations. You are meticulous about ensuring consistency across all parts of the model.
                
                Most importantly, you ALWAYS provide specific numerical values for ALL key metrics, including
                gross yield and net yield percentages, across all scenarios as these are critical for investor
                decision-making.
            """),
            instructions=instructions_template,
            knowledge_base=knowledge_base,
            search_knowledge=search_knowledge,
            show_tool_calls=True,
            markdown=True,
            storage=storage  # Pass storage object if available
        )


if __name__ == "__main__":
    from agno.utils.pprint import pprint_run_response
    
    # Run the search agent
    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o"
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
        data=searcher_data
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
