#!/usr/bin/env python3
"""
Validator Agent for Fama AI.

This agent is responsible for validating financial models and ensuring
their accuracy, consistency, and compliance with industry standards.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.message import Message

from models.model_factory import create_model

# Set up logging
logger = logging.getLogger(__name__)

class ValidatorAgent:
    """
    Validator Agent for financial model validation.
    
    This agent verifies the accuracy, consistency, and compliance of
    financial models for investment vehicles.
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
        Initialize the Validator Agent.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments for the model
        """
        logger.info("Initializing Validator Agent")
        
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
                You are a meticulous financial model validator with decades of experience in
                auditing financial projections for investment vehicles. Your expertise lies in
                identifying errors, inconsistencies, and unrealistic assumptions in financial models.
                You have a comprehensive understanding of accounting principles, financial mathematics,
                and industry benchmarks across various sectors.
            """),
            instructions=[
                "Thoroughly examine financial models for mathematical accuracy and internal consistency",
                "Verify that all calculations follow proper accounting principles and industry standards",
                "Check that assumptions are realistic, well-documented, and consistent with market conditions",
                "Ensure that growth rates, margins, and other financial metrics are within reasonable ranges",
                "Validate that financial statements (income statement, cash flow, etc.) are properly linked",
                "Identify potential errors or omissions in the financial model",
                "Provide a comprehensive validation report with specific issues and recommendations",
                "Rate the overall quality and reliability of the financial model",
                "Flag areas of high risk or uncertainty that require additional scrutiny",
                "Verify that scenario analyses cover an appropriate range of outcomes",
                "Ensure models comply with relevant financial reporting standards and regulations",
                "Validate key financial metrics and ratios against industry benchmarks"
            ],
            markdown=True
        )
        
        logger.info("Validator Agent initialized")
    
    def validate_model(
        self,
        description: str,
        financial_model: Dict[str, Any],
        assumptions: Dict[str, Any],
        metrics: Dict[str, Any],
        scenarios: Dict[str, Any],
        research_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Validate a financial model for accuracy, consistency, and compliance.
        
        Args:
            description: Natural language description of the investment vehicle
            financial_model: The financial model to validate
            assumptions: Assumptions used in the model
            metrics: Financial metrics calculated from the model
            scenarios: Scenario analyses for the model
            research_data: Research data used to inform the model
            market_conditions: Market conditions considered in the model
            **kwargs: Additional parameters for the validation process
            
        Returns:
            Dict containing the validation results
        """
        logger.info("Validating financial model")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Investment Vehicle Description
            {description}
            
            # Financial Model
            {financial_model.get('raw_model', 'No financial model available')}
            
            # Assumptions
            {assumptions.get('raw_assumptions', 'No assumptions available')}
            
            # Financial Metrics
            {metrics}
            
            # Scenarios
            {scenarios.get('raw_scenarios', 'No scenarios available')}
            
            # Research Data
            {research_data.get('raw_research', 'No research data available')}
            
            # Market Conditions
            {market_conditions.get('market_conditions', 'No market conditions available')}
            
            # Task
            Perform a comprehensive validation of the financial model. Your validation should cover:
            
            1. Mathematical Accuracy:
               - Check that all calculations are correct
               - Verify that totals and subtotals match their components
               - Ensure growth rates are applied consistently
               - Validate that financial metrics (IRR, NPV, ROI) are calculated correctly
            
            2. Internal Consistency:
               - Verify that cash flows, income statements, and other financial statements are properly linked
               - Check that assumptions are applied consistently throughout the model
               - Ensure that scenarios are properly constructed and internally consistent
            
            3. Assumption Validation:
               - Evaluate whether assumptions are realistic and in line with market conditions
               - Compare growth rates, margins, and other key metrics against industry benchmarks
               - Assess whether risk factors are adequately considered
            
            4. Compliance and Standards:
               - Verify that the model follows generally accepted accounting principles
               - Check that the model is consistent with industry standards and best practices
               - Ensure regulatory considerations are properly addressed
            
            5. Scenario Analysis:
               - Verify that scenario analyses cover an appropriate range of outcomes
               - Check that scenarios are based on reasonable assumptions
               - Ensure that scenario impacts are properly calculated
            
            Provide a comprehensive validation report that includes:
            
            1. Overall validation score (out of 100)
            2. List of identified issues, categorized by severity (critical, major, minor)
            3. Specific recommendations for improving the model
            4. Areas of uncertainty or risk that require additional scrutiny
            5. Compliance notes regarding accounting principles and industry standards
            
            Structure your validation report in a clear, professional format.
        """)
        
        # Get the validation results from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured validation results
        validation_results = self._process_validation_response(response)
        
        logger.info("Financial model validation completed")
        return validation_results
    
    def validate_metrics(
        self,
        metrics: Dict[str, Any],
        financial_model: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Validate specific financial metrics for accuracy and reasonableness.
        
        Args:
            metrics: Financial metrics to validate
            financial_model: The financial model from which metrics were calculated
            **kwargs: Additional parameters for the validation process
            
        Returns:
            Dict containing the validation results for the metrics
        """
        logger.info("Validating financial metrics")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Financial Metrics
            {metrics}
            
            # Financial Model
            {financial_model.get('raw_model', 'No financial model available')}
            
            # Task
            Validate the following financial metrics for accuracy and reasonableness:
            
            1. IRR (Internal Rate of Return):
               - Verify that the IRR calculation is mathematically accurate
               - Check that the IRR is reasonable given the cash flow profile
               - Compare the IRR to industry benchmarks for similar investments
            
            2. NPV (Net Present Value):
               - Verify that the NPV calculation is mathematically accurate
               - Check that the discount rate used is appropriate
               - Assess whether the NPV is reasonable given the investment profile
            
            3. ROI (Return on Investment):
               - Verify that the ROI calculation is mathematically accurate
               - Compare the ROI to industry benchmarks
               - Check that the ROI calculation period is appropriate
            
            4. Payback Period:
               - Verify that the payback period calculation is mathematically accurate
               - Assess whether the payback period is reasonable given the investment profile
               - Compare the payback period to industry benchmarks
            
            5. Yield:
               - Verify that the yield calculation is mathematically accurate
               - Check that the yield is reasonable given the investment profile
               - Compare the yield to similar investments in the market
            
            For each metric, provide:
            
            1. Validation status (Valid, Questionable, Invalid)
            2. Identified issues (if any)
            3. Recommendations for improvement (if needed)
            4. Comparison to industry benchmarks
            
            Structure your validation report in a clear, professional format.
        """)
        
        # Get the validation results from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured validation results
        metric_validation_results = self._process_metric_validation_response(response)
        
        logger.info("Financial metrics validation completed")
        return metric_validation_results
    
    def validate_scenarios(
        self,
        scenarios: Dict[str, Any],
        financial_model: Dict[str, Any],
        assumptions: Dict[str, Any],
        market_conditions: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Validate scenario analyses for appropriateness and comprehensiveness.
        
        Args:
            scenarios: Scenario analyses to validate
            financial_model: The base financial model
            assumptions: Assumptions used in the model
            market_conditions: Market conditions considered in the model
            **kwargs: Additional parameters for the validation process
            
        Returns:
            Dict containing the validation results for the scenarios
        """
        logger.info("Validating scenario analyses")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Scenarios
            {scenarios.get('raw_scenarios', 'No scenarios available')}
            
            # Financial Model
            {financial_model.get('raw_model', 'No financial model available')}
            
            # Assumptions
            {assumptions.get('raw_assumptions', 'No assumptions available')}
            
            # Market Conditions
            {market_conditions.get('market_conditions', 'No market conditions available')}
            
            # Task
            Validate the scenario analyses for appropriateness and comprehensiveness. Your validation should cover:
            
            1. Scenario Coverage:
               - Assess whether the scenarios (baseline, bull, bear) cover an appropriate range of outcomes
               - Check if there are any significant scenarios that are missing
               - Evaluate whether the scenarios are sufficiently distinct to be useful
            
            2. Scenario Assumptions:
               - Verify that the assumptions for each scenario are reasonable and internally consistent
               - Check that the assumptions are properly linked to market conditions and research data
               - Assess whether the assumptions for different scenarios are appropriately differentiated
            
            3. Scenario Impact Analysis:
               - Verify that the impact of each scenario on financial metrics is correctly calculated
               - Check that the comparative analysis is comprehensive and insightful
               - Assess whether the risk assessment is thorough and well-reasoned
            
            4. Decision Framework:
               - Evaluate whether the decision framework is practical and actionable
               - Check that the decision framework addresses the key risks and opportunities
               - Assess whether the decision framework is aligned with the investment objectives
            
            For each aspect of the scenario analyses, provide:
            
            1. Validation status (Comprehensive, Adequate, Limited, Inadequate)
            2. Identified gaps or issues (if any)
            3. Recommendations for improvement (if needed)
            
            Structure your validation report in a clear, professional format.
        """)
        
        # Get the validation results from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured validation results
        scenario_validation_results = self._process_scenario_validation_response(response)
        
        logger.info("Scenario analyses validation completed")
        return scenario_validation_results
    
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
        
        # In a real implementation, this would parse the validation results into structured data
        # For now, we'll just return the raw response with minimal structure
        
        validation_results = {
            "raw_validation": raw_validation,
            "overall_score": None,
            "issues": {
                "critical": [],
                "major": [],
                "minor": []
            },
            "recommendations": {
                "items": []
            },
            "risk_areas": {
                "items": []
            },
            "compliance_notes": {
                "items": []
            }
        }
        
        # Extract the overall score using a simple pattern match
        score_match = re.search(r'overall.*score.*?(\d+)', raw_validation, re.IGNORECASE)
        if score_match:
            try:
                validation_results["overall_score"] = int(score_match.group(1))
            except ValueError:
                pass
        
        # Extract sections based on markdown headers
        sections = raw_validation.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            if "issue" in section_title.lower() or "problem" in section_title.lower():
                validation_results["issues"]["raw"] = section_content
                
                # Try to categorize issues by severity
                for line in section_content.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        issue = line.strip()[2:].strip()
                        if "critical" in line.lower():
                            validation_results["issues"]["critical"].append(issue)
                        elif "major" in line.lower():
                            validation_results["issues"]["major"].append(issue)
                        elif "minor" in line.lower():
                            validation_results["issues"]["minor"].append(issue)
                        else:
                            # Default to major if severity is not specified
                            validation_results["issues"]["major"].append(issue)
            
            elif "recommendation" in section_title.lower():
                validation_results["recommendations"]["raw"] = section_content
                
                # Extract individual recommendations
                for line in section_content.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        recommendation = line.strip()[2:].strip()
                        validation_results["recommendations"]["items"].append(recommendation)
            
            elif "risk" in section_title.lower() or "uncertainty" in section_title.lower():
                validation_results["risk_areas"]["raw"] = section_content
                
                # Extract individual risk areas
                for line in section_content.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        risk_area = line.strip()[2:].strip()
                        validation_results["risk_areas"]["items"].append(risk_area)
            
            elif "compliance" in section_title.lower():
                validation_results["compliance_notes"]["raw"] = section_content
                
                # Extract individual compliance notes
                for line in section_content.split("\n"):
                    if line.strip().startswith("- ") or line.strip().startswith("* "):
                        compliance_note = line.strip()[2:].strip()
                        validation_results["compliance_notes"]["items"].append(compliance_note)
        
        return validation_results
    
    def _process_metric_validation_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's metric validation response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured metric validation results
        """
        # Extract the raw response
        raw_validation = response.content
        
        # In a real implementation, this would parse the validation results into structured data
        # For now, we'll just return the raw response with minimal structure
        
        validation_results = {
            "raw_validation": raw_validation,
            "irr": {"status": None, "issues": [], "recommendations": []},
            "npv": {"status": None, "issues": [], "recommendations": []},
            "roi": {"status": None, "issues": [], "recommendations": []},
            "payback_period": {"status": None, "issues": [], "recommendations": []},
            "yield": {"status": None, "issues": [], "recommendations": []}
        }
        
        # Extract sections based on markdown headers
        sections = raw_validation.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            # Map section title to metric key
            metric_key = None
            if "irr" in section_title.lower() or "internal rate of return" in section_title.lower():
                metric_key = "irr"
            elif "npv" in section_title.lower() or "net present value" in section_title.lower():
                metric_key = "npv"
            elif "roi" in section_title.lower() or "return on investment" in section_title.lower():
                metric_key = "roi"
            elif "payback" in section_title.lower():
                metric_key = "payback_period"
            elif "yield" in section_title.lower():
                metric_key = "yield"
            
            if metric_key:
                validation_results[metric_key]["raw"] = section_content
                
                # Extract status
                status_match = re.search(r'status.*?:\s*(\w+)', section_content, re.IGNORECASE)
                if status_match:
                    validation_results[metric_key]["status"] = status_match.group(1)
                
                # Extract issues and recommendations
                for line in section_content.split("\n"):
                    if "issue" in line.lower() and (":" in line or "-" in line):
                        issue = line.split(":", 1)[1].strip() if ":" in line else line.split("-", 1)[1].strip()
                        validation_results[metric_key]["issues"].append(issue)
                    elif "recommendation" in line.lower() and (":" in line or "-" in line):
                        recommendation = line.split(":", 1)[1].strip() if ":" in line else line.split("-", 1)[1].strip()
                        validation_results[metric_key]["recommendations"].append(recommendation)
        
        return validation_results
    
    def _process_scenario_validation_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's scenario validation response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured scenario validation results
        """
        # Extract the raw response
        raw_validation = response.content
        
        # In a real implementation, this would parse the validation results into structured data
        # For now, we'll just return the raw response with minimal structure
        
        validation_results = {
            "raw_validation": raw_validation,
            "scenario_coverage": {"status": None, "gaps": [], "recommendations": []},
            "scenario_assumptions": {"status": None, "issues": [], "recommendations": []},
            "scenario_impact": {"status": None, "issues": [], "recommendations": []},
            "decision_framework": {"status": None, "issues": [], "recommendations": []}
        }
        
        # Extract sections based on markdown headers
        sections = raw_validation.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            # Map section title to aspect key
            aspect_key = None
            if "coverage" in section_title.lower():
                aspect_key = "scenario_coverage"
            elif "assumption" in section_title.lower():
                aspect_key = "scenario_assumptions"
            elif "impact" in section_title.lower():
                aspect_key = "scenario_impact"
            elif "decision" in section_title.lower() or "framework" in section_title.lower():
                aspect_key = "decision_framework"
            
            if aspect_key:
                validation_results[aspect_key]["raw"] = section_content
                
                # Extract status
                status_match = re.search(r'status.*?:\s*(\w+)', section_content, re.IGNORECASE)
                if status_match:
                    validation_results[aspect_key]["status"] = status_match.group(1)
                
                # Extract gaps/issues and recommendations
                for line in section_content.split("\n"):
                    if ("gap" in line.lower() or "issue" in line.lower()) and (":" in line or "-" in line):
                        issue = line.split(":", 1)[1].strip() if ":" in line else line.split("-", 1)[1].strip()
                        if aspect_key == "scenario_coverage":
                            validation_results[aspect_key]["gaps"].append(issue)
                        else:
                            validation_results[aspect_key]["issues"].append(issue)
                    elif "recommendation" in line.lower() and (":" in line or "-" in line):
                        recommendation = line.split(":", 1)[1].strip() if ":" in line else line.split("-", 1)[1].strip()
                        validation_results[aspect_key]["recommendations"].append(recommendation)
        
        return validation_results 