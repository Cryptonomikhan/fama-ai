#!/usr/bin/env python3
"""
Scenario Planner Agent for Fama AI.

This agent is responsible for generating scenario models for investment vehicles.
"""
import logging
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.message import Message

from models.model_factory import create_model

# Set up logging
logger = logging.getLogger(__name__)

class ScenarioPlannerAgent:
    """
    Scenario Planner Agent for generating multiple financial scenarios.
    
    This agent creates baseline, bull, and bear scenario models
    for investment vehicles based on their financial model.
    """
    
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Initialize the Scenario Planner Agent.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments for the model
        """
        logger.info("Initializing Scenario Planner Agent")
        
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
                You are a world-class financial scenario planner specializing in yield-generating investment vehicles.
                Your expertise lies in creating realistic and data-driven scenario models (baseline, bull, and bear)
                for financial projections, accounting for various risk factors and market conditions.
                You have decades of experience in scenario planning for complex investments.
            """),
            instructions=[
                "Create baseline, bull, and bear scenarios based on financial models",
                "Identify key variables that most impact financial outcomes",
                "Ensure scenarios are realistic and data-driven, not arbitrary",
                "Base bull and bear scenarios on specific market conditions and risk factors",
                "Quantify the impact of different variables on financial outcomes",
                "Provide clear narratives describing the conditions under which each scenario might occur",
                "Adjust revenue, expense, and growth projections appropriately for each scenario",
                "Maintain internal consistency within each scenario model",
                "Include probability estimates for each scenario when appropriate",
                "Provide clear documentation of all assumptions unique to each scenario",
                "Ensure scenarios reflect the full range of realistic outcomes",
                "Consider historical volatility in similar investments when setting ranges"
            ],
            markdown=True
        )
        
        logger.info("Scenario Planner Agent initialized")
    
    def generate_scenarios(
        self,
        description: str,
        financial_model: Dict[str, Any],
        research_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        risk_factors: str = "moderate",
        time_horizon: int = 5,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate baseline, bull, and bear scenarios for a financial model.
        
        Args:
            description: Natural language description of the investment vehicle
            financial_model: The base financial model
            research_data: Research data about the investment vehicle
            market_conditions: Current and projected market conditions
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            time_horizon: Time horizon for the scenarios in years
            **kwargs: Additional parameters for the scenario planning process
            
        Returns:
            Dict containing the scenarios with financial projections
        """
        logger.info(f"Generating scenarios with {time_horizon} year horizon and {risk_factors} risk profile")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Investment Vehicle Description
            {description}
            
            # Financial Model (Base Case)
            {financial_model.get('raw_model', 'No financial model available')}
            
            # Research Data
            {research_data.get('raw_research', 'No research data available')}
            
            # Market Conditions
            {market_conditions.get('market_conditions', 'No market conditions available')}
            
            # Task
            Create three comprehensive scenarios (baseline, bull, and bear) for this investment vehicle.
            
            For each scenario:
            
            1. Define the scenario conditions:
               - What market conditions would lead to this scenario?
               - What assumptions differ from the base case?
               - What is the estimated probability of this scenario occurring?
            
            2. Adjusted Income Statement Projections (Annual for {time_horizon} years):
               - Revenue adjustments (% change from base case)
               - Expense adjustments (% change from base case)
               - Profit margin implications
            
            3. Adjusted Cash Flow Projections (Annual for {time_horizon} years):
               - Cash flow adjustments (% change from base case)
               - Capital expenditure adjustments
               - Working capital requirement changes
            
            4. Adjusted Investment Metrics:
               - Revised IRR
               - Revised NPV
               - Revised payback period
               - Impact on yield
            
            5. Sensitivity Triggers:
               - Key variables that could shift the scenario
               - Warning indicators to monitor
            
            Risk profile: {risk_factors}
            
            Please structure each scenario in a clear, professional format with all differences from the base case clearly documented.
        """)
        
        # Get the scenarios from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured scenarios
        scenarios = self._process_scenarios_response(response, time_horizon)
        
        logger.info("Scenarios generated successfully")
        return scenarios
    
    def analyze_scenario_impact(
        self,
        scenarios: Dict[str, Any],
        financial_metrics: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Analyze the impact of different scenarios on financial metrics.
        
        Args:
            scenarios: The scenarios generated for the investment vehicle
            financial_metrics: The base case financial metrics
            **kwargs: Additional parameters for the impact analysis
            
        Returns:
            Dict containing the analysis of scenario impacts
        """
        logger.info("Analyzing scenario impact on financial metrics")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Scenarios
            {scenarios.get('raw_scenarios', 'No scenarios available')}
            
            # Base Case Financial Metrics
            {financial_metrics.get('raw_metrics', 'No metrics available')}
            
            # Task
            Analyze the impact of the different scenarios on the financial metrics.
            
            For each scenario (baseline, bull, and bear):
            
            1. Comparative Analysis:
               - Compare key metrics (IRR, NPV, payback period) across scenarios
               - Calculate the percentage change from base case
               - Identify the most sensitive metrics
            
            2. Risk Assessment:
               - Evaluate the risk-adjusted return for each scenario
               - Determine the downside protection measures
               - Assess the probability-weighted expected return
            
            3. Decision Framework:
               - Provide guidance on what conditions would favor investment
               - Identify key indicators that would suggest shifting between scenarios
               - Recommend risk mitigation strategies for the bear case
            
            Please provide a clear, data-driven analysis that helps with investment decision-making.
        """)
        
        # Get the impact analysis from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured impact analysis
        impact_analysis = self._process_impact_response(response)
        
        logger.info("Scenario impact analysis completed")
        return impact_analysis
    
    def _process_scenarios_response(
        self,
        response: Message,
        time_horizon: int
    ) -> Dict[str, Any]:
        """
        Process the agent's scenarios response into structured data.
        
        Args:
            response: The response from the agent
            time_horizon: Time horizon for the scenarios in years
            
        Returns:
            Dict containing the structured scenarios
        """
        # Extract the raw response
        raw_scenarios = response.content
        
        # In a real implementation, this would parse the scenarios into structured data
        # For now, we'll just return the raw response with minimal structure
        
        scenarios = {
            "raw_scenarios": raw_scenarios,
            "time_horizon": time_horizon,
            "baseline": {},
            "bull": {},
            "bear": {}
        }
        
        # Extract sections based on markdown headers
        sections = raw_scenarios.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            # Determine which scenario this section belongs to
            if "baseline" in section_title.lower() or "base case" in section_title.lower() or "base scenario" in section_title.lower():
                scenarios["baseline"]["description"] = section_content
            elif "bull" in section_title.lower() or "upside" in section_title.lower() or "optimistic" in section_title.lower():
                scenarios["bull"]["description"] = section_content
            elif "bear" in section_title.lower() or "downside" in section_title.lower() or "pessimistic" in section_title.lower():
                scenarios["bear"]["description"] = section_content
            
            # Extract financial projections if they exist in the section
            if "income" in section_title.lower() or "statement" in section_title.lower():
                if "baseline" in section_title.lower() or "base case" in section_title.lower():
                    scenarios["baseline"]["income_statement"] = section_content
                elif "bull" in section_title.lower() or "upside" in section_title.lower():
                    scenarios["bull"]["income_statement"] = section_content
                elif "bear" in section_title.lower() or "downside" in section_title.lower():
                    scenarios["bear"]["income_statement"] = section_content
            
            if "cash flow" in section_title.lower():
                if "baseline" in section_title.lower() or "base case" in section_title.lower():
                    scenarios["baseline"]["cash_flow"] = section_content
                elif "bull" in section_title.lower() or "upside" in section_title.lower():
                    scenarios["bull"]["cash_flow"] = section_content
                elif "bear" in section_title.lower() or "downside" in section_title.lower():
                    scenarios["bear"]["cash_flow"] = section_content
            
            if "metric" in section_title.lower() or "irr" in section_title.lower() or "npv" in section_title.lower():
                if "baseline" in section_title.lower() or "base case" in section_title.lower():
                    scenarios["baseline"]["metrics"] = section_content
                elif "bull" in section_title.lower() or "upside" in section_title.lower():
                    scenarios["bull"]["metrics"] = section_content
                elif "bear" in section_title.lower() or "downside" in section_title.lower():
                    scenarios["bear"]["metrics"] = section_content
        
        # If we couldn't extract structured data, at least provide baseline scenarios
        if not scenarios["baseline"]:
            baseline_content = ""
            bull_content = ""
            bear_content = ""
            
            if "baseline scenario" in raw_scenarios.lower() or "base case scenario" in raw_scenarios.lower():
                parts = raw_scenarios.lower().split("baseline scenario")
                if len(parts) > 1:
                    baseline_end = parts[1].find("bull scenario") if "bull scenario" in parts[1] else len(parts[1])
                    baseline_content = parts[1][:baseline_end].strip()
            
            if "bull scenario" in raw_scenarios.lower() or "optimistic scenario" in raw_scenarios.lower():
                parts = raw_scenarios.lower().split("bull scenario")
                if len(parts) > 1:
                    bull_end = parts[1].find("bear scenario") if "bear scenario" in parts[1] else len(parts[1])
                    bull_content = parts[1][:bull_end].strip()
            
            if "bear scenario" in raw_scenarios.lower() or "pessimistic scenario" in raw_scenarios.lower():
                parts = raw_scenarios.lower().split("bear scenario")
                if len(parts) > 1:
                    bear_content = parts[1].strip()
            
            if baseline_content:
                scenarios["baseline"]["description"] = baseline_content
            if bull_content:
                scenarios["bull"]["description"] = bull_content
            if bear_content:
                scenarios["bear"]["description"] = bear_content
        
        return scenarios
    
    def _process_impact_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's impact analysis response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured impact analysis
        """
        # Extract the raw response
        raw_analysis = response.content
        
        # In a real implementation, this would parse the analysis into structured data
        # For now, we'll just return the raw response with minimal structure
        
        impact_analysis = {
            "raw_analysis": raw_analysis,
            "comparative_analysis": {},
            "risk_assessment": {},
            "decision_framework": {}
        }
        
        # Extract sections based on markdown headers
        sections = raw_analysis.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            if "comparative" in section_title.lower() or "comparison" in section_title.lower():
                impact_analysis["comparative_analysis"]["raw"] = section_content
            elif "risk" in section_title.lower() or "assessment" in section_title.lower():
                impact_analysis["risk_assessment"]["raw"] = section_content
            elif "decision" in section_title.lower() or "framework" in section_title.lower() or "recommendation" in section_title.lower():
                impact_analysis["decision_framework"]["raw"] = section_content
        
        return impact_analysis 