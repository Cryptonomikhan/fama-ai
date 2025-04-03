#!/usr/bin/env python3
"""
Assumption Generator Agent for Fama AI.

This agent is responsible for generating assumptions for financial models.
"""
import logging
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.message import Message

from models.model_factory import create_model

# Set up logging
logger = logging.getLogger(__name__)

class AssumptionGeneratorAgent:
    """
    Assumption Generator Agent for creating financial model assumptions.
    
    This agent generates detailed and well-documented assumptions
    for financial models of investment vehicles.
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
        Initialize the Assumption Generator Agent.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments for the model
        """
        logger.info("Initializing Assumption Generator Agent")
        
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
                You are a world-class financial analyst specializing in creating assumptions for financial models.
                Your expertise lies in developing detailed, well-documented, and realistic assumptions for yield-generating
                investment vehicles based on research data and market conditions. You have decades of experience
                in creating assumptions for complex financial models across various investment types.
            """),
            instructions=[
                "Create comprehensive assumptions for financial models based on research data and market conditions",
                "Categorize assumptions by type (revenue, expenses, capital, growth, etc.)",
                "Provide clear rationale and sources for each assumption",
                "Base assumptions on historical data, industry benchmarks, and market trends",
                "Include both core assumptions and sensitivity parameters",
                "Document the confidence level and range for each assumption",
                "Ensure assumptions are consistent with the investment vehicle type and time horizon",
                "Consider macro and micro economic factors in assumption development",
                "Provide alternative assumptions for different scenarios (baseline, bull, bear)",
                "Flag assumptions that carry the highest risk or uncertainty",
                "Ensure all assumptions are quantifiable and testable",
                "Consider regulatory and compliance factors in assumption development"
            ],
            markdown=True
        )
        
        logger.info("Assumption Generator Agent initialized")
    
    def generate_assumptions(
        self,
        description: str,
        research_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        yield_data: Dict[str, Any],
        financial_model: Dict[str, Any],
        scenarios: Dict[str, Any],
        time_horizon: int = 5,
        risk_factors: str = "moderate",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate comprehensive assumptions for a financial model.
        
        Args:
            description: Natural language description of the investment vehicle
            research_data: Research data about the investment vehicle
            market_conditions: Current and projected market conditions
            yield_data: Historical and projected yield data for similar investments
            financial_model: The base financial model
            scenarios: The generated scenarios (baseline, bull, bear)
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            **kwargs: Additional parameters for the assumption generation process
            
        Returns:
            Dict containing categorized assumptions with rationales
        """
        logger.info(f"Generating assumptions with {time_horizon} year horizon and {risk_factors} risk profile")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Investment Vehicle Description
            {description}
            
            # Research Data
            {research_data.get('raw_research', 'No research data available')}
            
            # Market Conditions
            {market_conditions.get('market_conditions', 'No market conditions available')}
            
            # Yield Data
            {yield_data.get('yield_data', 'No yield data available')}
            
            # Financial Model Summary
            {financial_model.get('raw_model', 'No financial model available')}
            
            # Scenarios
            {scenarios.get('raw_scenarios', 'No scenarios available')}
            
            # Task
            Create comprehensive assumptions for the financial model of this investment vehicle.
            
            For each category of assumptions:
            
            1. Revenue Assumptions:
               - Initial pricing/yield levels
               - Growth rates and their justification
               - Seasonality or cyclicality factors
               - Market penetration and adoption curves
            
            2. Operating Expense Assumptions:
               - Fixed costs and their components
               - Variable costs and scaling factors
               - Maintenance and operational requirements
               - Staffing and administrative costs
            
            3. Capital Expenditure Assumptions:
               - Initial investment requirements
               - Replacement/upgrade cycles
               - Depreciation schedules and methodologies
               - Salvage values
            
            4. Market Assumptions:
               - Competitive landscape evolution
               - Market size and growth projections
               - Supply and demand dynamics
               - Regulatory environment changes
            
            5. Financial Assumptions:
               - Discount rates and justification
               - Financing structures and costs
               - Tax considerations
               - Inflation expectations
            
            For each assumption:
               - Provide a clear numeric value or range
               - Explain the rationale behind it
               - Cite sources or benchmarks where applicable
               - Indicate confidence level (high, medium, low)
               - Note implications for sensitivity analysis
            
            Time horizon: {time_horizon} years
            Risk profile: {risk_factors}
            
            Please structure the assumptions in a clear, professional format that can be easily integrated into the financial model.
        """)
        
        # Get the assumptions from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured assumptions
        assumptions = self._process_assumptions_response(response)
        
        logger.info("Assumptions generated successfully")
        return assumptions
    
    def validate_assumptions(
        self,
        assumptions: Dict[str, Any],
        research_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Validate the generated assumptions against research data and market conditions.
        
        Args:
            assumptions: The generated assumptions to validate
            research_data: Research data about the investment vehicle
            market_conditions: Current and projected market conditions
            **kwargs: Additional parameters for the validation process
            
        Returns:
            Dict containing the validation results
        """
        logger.info("Validating assumptions")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Assumptions
            {assumptions.get('raw_assumptions', 'No assumptions available')}
            
            # Research Data
            {research_data.get('raw_research', 'No research data available')}
            
            # Market Conditions
            {market_conditions.get('market_conditions', 'No market conditions available')}
            
            # Task
            Validate the provided assumptions against the research data and market conditions.
            
            For each category of assumptions:
            
            1. Consistency Check:
               - Are the assumptions internally consistent?
               - Do they align with the research data?
               - Are they supported by market conditions?
            
            2. Realism Assessment:
               - Are the assumptions realistic based on industry benchmarks?
               - Are the growth rates and projections defensible?
               - Are there any outliers that require justification?
            
            3. Risk Evaluation:
               - Which assumptions carry the highest risk?
               - What assumptions have the greatest impact on the model outcomes?
               - Are there alternative assumptions that should be considered?
            
            4. Gaps Analysis:
               - Are there any missing critical assumptions?
               - Are there areas where more detailed assumptions are needed?
               - Are there interdependencies between assumptions that are not addressed?
            
            Please provide a structured validation report with specific recommendations for any assumptions that need revision.
        """)
        
        # Get the validation results from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured validation results
        validation_results = self._process_validation_response(response)
        
        logger.info("Assumptions validation completed")
        return validation_results
    
    def _process_assumptions_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's assumptions response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured assumptions
        """
        # Extract the raw response
        raw_assumptions = response.content
        
        # In a real implementation, this would parse the assumptions into structured data
        # For now, we'll just return the raw response with minimal structure
        
        assumptions = {
            "raw_assumptions": raw_assumptions,
            "revenue": {},
            "operating_expenses": {},
            "capital_expenditures": {},
            "market": {},
            "financial": {}
        }
        
        # Extract sections based on markdown headers
        sections = raw_assumptions.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            if "revenue" in section_title.lower():
                assumptions["revenue"]["raw"] = section_content
            elif "operating" in section_title.lower() or "expense" in section_title.lower():
                assumptions["operating_expenses"]["raw"] = section_content
            elif "capital" in section_title.lower() or "expenditure" in section_title.lower():
                assumptions["capital_expenditures"]["raw"] = section_content
            elif "market" in section_title.lower():
                assumptions["market"]["raw"] = section_content
            elif "financial" in section_title.lower():
                assumptions["financial"]["raw"] = section_content
        
        return assumptions
    
    def _process_validation_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's validation response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured validation results
        """
        # Extract the raw response
        raw_validation = response.content
        
        # In a real implementation, this would parse the validation into structured data
        # For now, we'll just return the raw response with minimal structure
        
        validation_results = {
            "raw_validation": raw_validation,
            "consistency_check": {},
            "realism_assessment": {},
            "risk_evaluation": {},
            "gaps_analysis": {}
        }
        
        # Extract sections based on markdown headers
        sections = raw_validation.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            if "consistency" in section_title.lower():
                validation_results["consistency_check"]["raw"] = section_content
            elif "realism" in section_title.lower() or "assessment" in section_title.lower():
                validation_results["realism_assessment"]["raw"] = section_content
            elif "risk" in section_title.lower() or "evaluation" in section_title.lower():
                validation_results["risk_evaluation"]["raw"] = section_content
            elif "gap" in section_title.lower() or "analysis" in section_title.lower():
                validation_results["gaps_analysis"]["raw"] = section_content
        
        return validation_results 