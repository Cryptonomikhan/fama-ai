from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from src.models.factory import create_model
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
import logging
from textwrap import dedent
from typing import Any, Optional, List
import os
from dotenv import load_dotenv
from src.knowledge.logging import wrap_knowledge_base

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class MetricsDerivingAgent:
    """
    Agent specialized in deriving key financial metrics for financial models based on research and assumptions.
    
    This agent analyzes information to identify and define the most relevant financial metrics for various
    investment opportunities. It can leverage previous research, assumptions, and knowledge base information
    to determine which metrics are most critical for a comprehensive financial model.
    """
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        searcher_data: Optional[str] = None,
        assumption_data: Optional[str] = None,
        additional_tools: Optional[List] = None,
        knowledge_base: Optional[Any] = None,
        search_knowledge: bool = True,
        session_id: Optional[str] = None,
        storage: Optional[Any] = None,
        **kwargs: Any
    ):
        """
        Initialize a MetricsDerivingAgent with the specified parameters.
        
        Args:
            provider: Model provider (e.g., "openai", "formation", "anthropic")
            model_id: ID of the model to use
            temperature: Temperature for model generation (higher = more creative, lower = more deterministic)
            max_tokens: Maximum tokens to generate in responses
            searcher_data: Research data from the SearchingAgent
            assumption_data: Generated assumptions from the AssumptionGeneratorAgent
            additional_tools: Additional tools to give the agent
            knowledge_base: Knowledge base instance to use for semantic search
            search_knowledge: Whether to search the knowledge base for relevant information
            session_id: Session ID for knowledge tracking across agents
            storage: Optional storage backend for maintaining agent state across sessions
            **kwargs: Additional keyword arguments for the model
        """

        logger.info("Initializing Metrics Deriving Agent")

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
        
        # Add any additional tools provided
        if additional_tools:
            for tool in additional_tools:
                tools.append(tool)
                logger.info(f"Added additional tool to MetricsDerivingAgent: {tool.name}")

        # Instructions for the agent
        base_instructions = dedent("""
        # Instructions for Deriving Financial Metrics
        
        ## Core Purpose
        Your task is to identify the most relevant financial metrics that should be included in a comprehensive financial model for the given investment opportunity. You will define exactly what metrics should be calculated, why they matter, and how they should be interpreted.
        
        ## The Metrics You Should Define
        
        For ALL investment types, consider these metric categories:
        
        1. **Return Metrics**
           - Gross Yield: Total returns before expenses (%)
           - Net Yield: Returns after all expenses (%)
           - Return on Investment (ROI): Total profit as percentage of investment
           - Internal Rate of Return (IRR): Time-adjusted return rate
           - Cash-on-Cash Return: Annual cash flow relative to cash invested
           - Yield on Cost (YOC): Annual income as percentage of total investment
        
        2. **Valuation Metrics**
           - Net Present Value (NPV): Present value of future cash flows minus initial investment
           - Multiple on Invested Capital (MOIC): Total value divided by total investment
           - Terminal Value: Estimated value at the end of the projection period
           - Capitalization Rate: Net operating income divided by current market value
        
        3. **Risk Metrics**
           - Payback Period: Time required to recover the initial investment
           - Break-even Analysis: Point at which revenue equals expenses
           - Debt Service Coverage Ratio (DSCR): Operating income divided by debt obligations
           - Sensitivity Analysis: How changes in key variables affect outcomes
        
        4. **Efficiency Metrics**
           - Operating Expense Ratio: Operating expenses as percentage of revenue
           - Gross Margin: Gross profit as percentage of revenue
           - Net Margin: Net profit as percentage of revenue
           - Operating Margin: Operating profit as percentage of revenue
        
        5. **Asset-Specific Metrics**
           - For Real Estate: Cap Rate, Price per Square Foot, Occupancy Rate
           - For Business Operations: Customer Acquisition Cost, Lifetime Value, Churn Rate
           - For Financial Assets: Dividend Yield, Earnings Per Share, P/E Ratio
           - For Technology: User Growth Rate, Engagement Metrics, Monetization Rate
        
        ## Instructions for Each Metric
        
        For each metric you recommend, provide:
        
        1. **Clear Definition**: Concise explanation of what the metric measures
        2. **Formula**: The exact mathematical formula used to calculate it
        3. **Relevance**: Why this metric is important for this specific investment
        4. **Interpretation Guidelines**: How to interpret different values (e.g., what constitutes a "good" value)
        5. **Calculation Frequency**: When/how often this metric should be calculated (e.g., annually, quarterly)
        6. **Data Dependencies**: What inputs are required to calculate this metric
        
        ## Asset-Class Specificity
        
        Tailor your metrics to the specific investment type:
        
        - **Real Estate Investments**: Emphasize cap rates, cash-on-cash returns, NOI, debt service coverage
        - **Operating Businesses**: Focus on profit margins, growth rates, customer metrics, unit economics
        - **Financial Instruments**: Include interest/dividend metrics, yield curves, volatility measures
        - **Technology Assets**: Highlight user economics, growth metrics, monetization efficiency
        - **Infrastructure**: Concentrate on utilization rates, maintenance efficiency, regulatory returns
        
        ## Creating a Comprehensive Framework
        
        Organize your metrics into a logical framework:
        
        1. Start with the most critical metrics that directly relate to investment returns
        2. Include secondary metrics that provide insight into operational performance
        3. Add risk-assessment metrics to evaluate downside protection
        4. Include comparison metrics for benchmarking against alternatives
        5. Balance short-term and long-term performance indicators
        
        ## Balancing Thoroughness with Practicality
        
        - Be comprehensive but avoid unnecessary complexity
        - Include all standard metrics for the asset class
        - Emphasize metrics that align with investor goals
        - Ensure the metrics together tell a complete story about the investment's potential
        
        ## Presentation Guidelines
        
        Present your metrics in a well-organized format:
        
        1. Group metrics by category (return, risk, efficiency, etc.)
        2. Use clear, consistent formatting
        3. Present formulas in a readable mathematical notation
        4. Provide brief examples for complex metrics
        """)
        
        # Add knowledge base instructions if a knowledge base is provided
        knowledge_base_instruction = ""
        if knowledge_base and search_knowledge:
            # Wrap knowledge base with logging if it hasn't been wrapped already
            if session_id and not hasattr(knowledge_base, '_kb_logging_wrapped'):
                knowledge_base = wrap_knowledge_base(
                    knowledge_base,
                    agent_name="MetricsDerivingAgent",
                    session_id=session_id
                )
                knowledge_base._kb_logging_wrapped = True
                logger.info("Knowledge base wrapped with logging for MetricsDerivingAgent")
            
            knowledge_base_instruction = dedent("""
            ## Using the Knowledge Base for Metrics
            
            When using the knowledge base:
            
            1. Search for industry-standard metrics specific to this asset class
            2. Look for case studies showing which metrics were most valuable in similar investments
            3. Find benchmark values for key performance indicators
            4. Check for specialized calculation methodologies preferred by institutional investors
            5. Identify any emerging metrics gaining adoption in this investment domain
            
            When knowledge base information conflicts with standard approaches:
            
            1. Consider the recency and authority of the knowledge base sources
            2. Evaluate whether specialized metrics offer advantages over standard ones
            3. Determine if the investment has unique characteristics requiring tailored metrics
            4. When in doubt, include both standard and specialized metrics with explanation
            """)
            logger.info("Knowledge base provided, updating metrics derivation instructions")
        
        # Format the instructions with the knowledge base instruction
        formatted_instructions = base_instructions + knowledge_base_instruction
        
        # Print data if available to help debug
        if searcher_data:
            logger.debug(f"Searcher data available (first 100 chars): {searcher_data[:100]}")
        if assumption_data:
            logger.debug(f"Assumption data available (first 100 chars): {assumption_data[:100]}")

        self.agent = Agent(
            name="Metrics Deriving Agent",
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
                opportunity. You always use reasoning to develop a
                comprehensive list of key metrics on both the return
                and expense side, You always organize and justify the metrics.
            """),
            instructions=formatted_instructions,
            knowledge_base=knowledge_base,
            search_knowledge=search_knowledge,
            show_tool_calls=True,
            markdown=True,
            storage=storage
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
