#!/usr/bin/env python3
"""
Research Agent for Fama AI.

This agent is responsible for domain-specific research for financial modeling.
"""
import logging
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.message import Message

from models.model_factory import create_model

# Set up logging
logger = logging.getLogger(__name__)

class ResearchAgent:
    """
    Research Agent for gathering financial and market data.
    
    This agent leverages internet search and financial data sources to gather information
    necessary for financial modeling of investment vehicles.
    """
    
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Initialize the Research Agent.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments for the model
        """
        logger.info("Initializing Research Agent")
        
        # Create model for the agent
        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Initialize agent with tools and separate description and instructions
        self.agent = Agent(
            model=model,
            description=dedent("""
                You are a world-class financial research expert specializing in yield-generating investment vehicles. 
                Your expertise encompasses deep knowledge of financial markets, investment analysis, and economic trends.
                You have decades of experience researching complex investment opportunities and providing data-driven insights.
            """),
            instructions=[
                "Begin by searching for authoritative financial information sources on the topic",
                "Focus on gathering specific numerical data points for financial modeling",
                "Prioritize reputable financial sources (Bloomberg, Financial Times, SEC filings, industry reports)",
                "Provide specific numbers and data points whenever possible (market size, growth rates, yields)",
                "When specific data is unavailable, provide reasonable ranges based on comparable investments",
                "Always cite sources when providing data points",
                "Indicate confidence levels for data points (high, medium, low)",
                "Focus exclusively on verifiable facts and data, not opinions",
                "Identify clearly when estimates are being provided vs. hard data",
                "Never fabricate specific numbers when data is unavailable",
                "Indicate data gaps explicitly rather than guessing",
                "Use ranges when exact figures aren't available",
                "For forward-looking projections, provide multiple scenarios (conservative, base, optimistic)"
            ],
            expected_output=dedent("""
                # Financial Research Report: {Investment Vehicle Type}

                ## Executive Summary
                {Brief overview of key findings}

                ## Market Analysis
                - Market Size: {Size in USD} 
                - CAGR: {Growth rate percentage}
                - Key Players: {Major entities in this space}
                - Competitive Landscape: {Brief description}

                ## Financial Metrics
                ### Revenue Metrics
                - Pricing Models: {Common pricing structures}
                - Average Yields: {Percentage ranges with historical trends}
                - Growth Rates: {Historical and projected percentages}

                ### Cost Structure
                - Initial Capital Requirements: {USD amounts or ranges}
                - Operating Expense Ratios: {Percentages of revenue}
                - Maintenance Costs: {USD or percentage of capital}
                - Regulatory Compliance Costs: {Initial and ongoing}

                ## Regulatory Environment
                {Current regulations and potential changes}

                ## Risk Assessment
                {Detailed analysis of risks with quantified impacts}

                ## Data Confidence
                {Assessment of data reliability and completeness}

                ## Sources
                {Citations for all key data points}
            """),
            tools=[DuckDuckGoTools()],
            markdown=True
        )
        
        logger.info(f"Research Agent initialized with {provider} model")
    
    def research_investment_vehicle(
        self,
        description: str,
        time_horizon: int = 5,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform research on an investment vehicle based on its description.
        
        Args:
            description: Natural language description of the investment vehicle
            time_horizon: Time horizon for the investment in years
            additional_context: Additional context or parameters for the research
            
        Returns:
            Dict containing research results
        """
        logger.info(f"Researching investment vehicle with time horizon of {time_horizon} years")
        
        # Build the prompt for the agent
        prompt = f"""
        I need comprehensive research on the following investment vehicle:
        
        {description}
        
        Time Horizon: {time_horizon} years
        
        Perform detailed market research and gather relevant information to inform financial modeling. 
        Focus on:
        
        1. Market size and growth trends relevant to this investment
        2. Historical performance data of similar investment vehicles
        3. Regulatory environment and compliance requirements
        4. Key risk factors and their historical impacts
        5. Current and projected market conditions that could affect this investment
        6. Benchmark data for comparison (e.g., average yields, costs, timeframes)
        
        IMPORTANT: Include specific numerical data points whenever possible, such as:
        - Estimated market size in USD
        - Annual growth rates as percentages
        - Average yields for similar investments
        - Typical operating expense ratios
        - Capital expenditure requirements
        - Depreciation schedules
        - Regulatory compliance costs
        """
        
        if additional_context:
            prompt += "\n\nAdditional Context:\n"
            for key, value in additional_context.items():
                prompt += f"- {key}: {value}\n"
        
        # Get response from the agent
        response = self.agent.run(prompt)
        
        # Parse the response
        # For now, we just return the raw content, but in a real implementation,
        # we would parse this into a structured format for other agents to use
        result = {
            "raw_research": response.content,
            "time_horizon": time_horizon,
            "description": description
        }
        
        logger.info("Research completed")
        return result
    
    def get_yield_data(self, vehicle_type: str, time_period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical yield data for specific investment vehicle types.
        
        Args:
            vehicle_type: Type of investment vehicle (e.g., "real estate", "dividend stocks")
            time_period: Optional time period for the data (e.g., "last 5 years")
            
        Returns:
            Dict containing yield data
        """
        logger.info(f"Retrieving yield data for {vehicle_type}")
        
        time_period_str = f" for {time_period}" if time_period else ""
        
        prompt = f"""
        Research and provide historical yield data for {vehicle_type}{time_period_str}.
        
        I need:
        1. Specific, numerical yield data with exact percentages whenever possible
        2. Year-by-year performance trends
        3. Breakdown of yields by capital appreciation and income components
        4. Comparison against relevant benchmarks
        5. Volatility metrics (standard deviation, Sharpe ratio, maximum drawdown)
        6. Explanation of any anomaly periods
        
        Please include a data table summarizing key yield metrics for each year,
        with proper citations for all data points.
        """
        
        response = self.agent.run(prompt)
        
        # For now, we just return the raw content
        result = {
            "vehicle_type": vehicle_type,
            "time_period": time_period,
            "yield_data": response.content
        }
        
        logger.info(f"Yield data retrieved for {vehicle_type}")
        return result
    
    def get_market_conditions(self) -> Dict[str, Any]:
        """
        Get current market conditions and forecasts.
        
        Returns:
            Dict containing market condition data
        """
        logger.info("Retrieving current market conditions")
        
        prompt = """
        Research and provide a comprehensive analysis of current market conditions 
        that would impact investment decisions for yield-generating vehicles.
        
        I need specific numerical data points on:
        1. Interest rates (Fed Funds rate, Treasury yields)
        2. Inflation metrics (CPI, PCE)
        3. Economic indicators (GDP, unemployment, consumer confidence)
        4. Market sentiment indicators (VIX, P/E ratios)
        5. Recent regulatory changes affecting investments
        6. Industry-specific trends
        
        For forward-looking data, please provide conservative, base case, 
        and optimistic scenarios with numerical values.
        
        Include a "Market Dashboard" section with the most critical current 
        metrics in a tabular format.
        """
        
        response = self.agent.run(prompt)
        
        result = {
            "market_conditions": response.content,
            "timestamp": "current" # In a real implementation, we would include the actual timestamp
        }
        
        logger.info("Market conditions retrieved")
        return result 