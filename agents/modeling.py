#!/usr/bin/env python3
"""
Modeling Agent for Fama AI.

This agent is responsible for creating financial models for investment vehicles.
"""
import logging
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.models.message import Message

from models.model_factory import create_model

# Set up logging
logger = logging.getLogger(__name__)

class ModelingAgent:
    """
    Modeling Agent for creating financial models.
    
    This agent creates comprehensive financial models for investment vehicles,
    including income statements, cash flow projections, and IRR/NPV calculations.
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
        Initialize the Modeling Agent.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional keyword arguments for the model
        """
        logger.info("Initializing Modeling Agent")
        
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
                You are a world-class financial modeling expert specializing in yield-generating investment vehicles.
                Your expertise lies in creating accurate, robust financial models that project cash flows, calculate returns,
                and provide comprehensive financial analysis for investment decision-making.
                You have decades of experience in financial analysis, investment banking, and asset management.
            """),
            instructions=[
                "Create comprehensive financial models based on research data",
                "Generate detailed income statements and cash flow projections",
                "Calculate key financial metrics (IRR, NPV, payback period, ROI)",
                "Follow GAAP/IFRS accounting standards in all financial models",
                "Include clear documentation for all calculations and formulas",
                "Structure models with clear sections for assumptions, calculations, and outputs",
                "Use consistent formatting for all financial statements",
                "Include both annual and quarterly projections when appropriate",
                "Ensure mathematical accuracy and cross-validation of all calculations",
                "Incorporate sensitivity analysis for key variables",
                "Apply appropriate discount rates based on risk profiles",
                "Document all data sources and methodologies"
            ],
            markdown=True
        )
        
        logger.info("Modeling Agent initialized")
    
    def create_financial_model(
        self,
        description: str,
        research_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        yield_data: Dict[str, Any],
        time_horizon: int = 5,
        risk_factors: str = "moderate",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a comprehensive financial model for an investment vehicle.
        
        Args:
            description: Natural language description of the investment vehicle
            research_data: Research data about the investment vehicle
            market_conditions: Current and projected market conditions
            yield_data: Historical and projected yield data for similar investments
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            **kwargs: Additional parameters for the modeling process
            
        Returns:
            Dict containing the financial model with income statements, cash flows, and metrics
        """
        logger.info(f"Creating financial model with {time_horizon} year horizon and {risk_factors} risk profile")
        
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
            
            # Task
            Create a comprehensive financial model for this investment vehicle with the following components:
            
            1. Key Assumptions:
               - Break down all major revenue and cost assumptions
               - Document growth rates and their justifications
               - Specify depreciation schedules and methodologies
            
            2. Income Statement Projections (Annual for {time_horizon} years):
               - Detailed revenue streams
               - Operating expenses categorized appropriately
               - Depreciation and amortization
               - Interest expenses
               - Tax calculations
               - Net income and margins
            
            3. Cash Flow Projections (Annual for {time_horizon} years):
               - Operating cash flows
               - Capital expenditures
               - Changes in working capital
               - Financing cash flows
               - Free cash flow to equity
            
            4. Investment Metrics:
               - Internal Rate of Return (IRR)
               - Net Present Value (NPV)
               - Payback period
               - Return on Investment (ROI)
               - Cash-on-cash return
               - Yield metrics
            
            5. Sensitivity Analysis:
               - Impact of varying key assumptions
               - Best, base, and worst-case scenarios
            
            Risk profile: {risk_factors}
            
            Please structure the financial model in a clear, professional format with all calculations and assumptions documented.
        """)
        
        # Get the financial model from the agent
        response = self.agent.run(prompt)
        
        # Process the response into a structured financial model
        financial_model = self._process_model_response(response, time_horizon, risk_factors)
        
        logger.info("Financial model created successfully")
        return financial_model
    
    def generate_metrics(
        self,
        financial_model: Dict[str, Any],
        time_horizon: int = 5,
        discount_rate: float = 0.1,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate key financial metrics from a financial model.
        
        Args:
            financial_model: The financial model to analyze
            time_horizon: Time horizon for the investment in years
            discount_rate: Discount rate for NPV calculations
            **kwargs: Additional parameters for the metrics calculation
            
        Returns:
            Dict containing the financial metrics
        """
        logger.info(f"Generating financial metrics with {discount_rate} discount rate")
        
        # Prepare the prompt for the model
        prompt = dedent(f"""
            # Financial Model
            {financial_model}
            
            # Task
            Calculate the following financial metrics based on the financial model:
            
            1. Internal Rate of Return (IRR)
            2. Net Present Value (NPV) with a discount rate of {discount_rate}
            3. Payback period
            4. Return on Investment (ROI)
            5. Cash-on-cash return
            6. Yield metrics (annual yield, average yield)
            7. Profitability index
            
            Please provide the calculations and explanations for each metric.
        """)
        
        # Get the metrics from the agent
        response = self.agent.run(prompt)
        
        # Process the response into structured metrics
        metrics = self._process_metrics_response(response)
        
        logger.info("Financial metrics generated successfully")
        return metrics
    
    def _process_model_response(
        self,
        response: Message,
        time_horizon: int,
        risk_factors: str
    ) -> Dict[str, Any]:
        """
        Process the agent's response into a structured financial model.
        
        Args:
            response: The response from the agent
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider
            
        Returns:
            Dict containing the structured financial model
        """
        # Extract the raw response
        raw_model = response.content
        
        # In a real implementation, this would parse the model into structured data
        # For now, we'll just return the raw response with minimal structure
        
        financial_model = {
            "raw_model": raw_model,
            "time_horizon": time_horizon,
            "risk_factors": risk_factors,
            "assumptions": {"raw": None},
            "income_statement": {"raw": None},
            "cash_flow": {"raw": None},
            "metrics": {"raw": None},
            "sensitivity": {"raw": None}
        }
        
        # Extract sections based on markdown headers
        sections = raw_model.split("##")
        for section in sections:
            if not section.strip():
                continue
            
            section_lines = section.strip().split("\n")
            section_title = section_lines[0].strip()
            section_content = "\n".join(section_lines[1:]).strip()
            
            if "assumption" in section_title.lower():
                financial_model["assumptions"]["raw"] = section_content
            elif "income" in section_title.lower() or "statement" in section_title.lower():
                financial_model["income_statement"]["raw"] = section_content
            elif "cash flow" in section_title.lower():
                financial_model["cash_flow"]["raw"] = section_content
            elif "metric" in section_title.lower() or "irr" in section_title.lower() or "npv" in section_title.lower():
                financial_model["metrics"]["raw"] = section_content
            elif "sensitivity" in section_title.lower() or "scenario" in section_title.lower():
                financial_model["sensitivity"]["raw"] = section_content
        
        return financial_model
    
    def _process_metrics_response(self, response: Message) -> Dict[str, Any]:
        """
        Process the agent's metrics response into structured data.
        
        Args:
            response: The response from the agent
            
        Returns:
            Dict containing the structured financial metrics
        """
        # Extract the raw response
        raw_metrics = response.content
        
        # In a real implementation, this would parse the metrics into structured data
        # For now, we'll just return the raw response with minimal structure
        
        metrics = {
            "raw_metrics": raw_metrics,
            "irr": None,
            "npv": None,
            "payback_period": None,
            "roi": None,
            "cash_on_cash": None,
            "yield": None,
            "profitability_index": None
        }
        
        # Extract metrics from the response
        # This is a simplified extraction and would be more robust in a real implementation
        
        if "irr" in raw_metrics.lower():
            irr_lines = [line for line in raw_metrics.split("\n") if "irr" in line.lower()]
            if irr_lines:
                metrics["irr"] = irr_lines[0].split(":")[-1].strip() if ":" in irr_lines[0] else None
        
        if "npv" in raw_metrics.lower():
            npv_lines = [line for line in raw_metrics.split("\n") if "npv" in line.lower()]
            if npv_lines:
                metrics["npv"] = npv_lines[0].split(":")[-1].strip() if ":" in npv_lines[0] else None
        
        if "payback" in raw_metrics.lower():
            payback_lines = [line for line in raw_metrics.split("\n") if "payback" in line.lower()]
            if payback_lines:
                metrics["payback_period"] = payback_lines[0].split(":")[-1].strip() if ":" in payback_lines[0] else None
        
        if "roi" in raw_metrics.lower():
            roi_lines = [line for line in raw_metrics.split("\n") if "roi" in line.lower()]
            if roi_lines:
                metrics["roi"] = roi_lines[0].split(":")[-1].strip() if ":" in roi_lines[0] else None
        
        if "cash-on-cash" in raw_metrics.lower() or "cash on cash" in raw_metrics.lower():
            coc_lines = [line for line in raw_metrics.split("\n") if "cash-on-cash" in line.lower() or "cash on cash" in line.lower()]
            if coc_lines:
                metrics["cash_on_cash"] = coc_lines[0].split(":")[-1].strip() if ":" in coc_lines[0] else None
        
        if "yield" in raw_metrics.lower():
            yield_lines = [line for line in raw_metrics.split("\n") if "yield" in line.lower()]
            if yield_lines:
                metrics["yield"] = yield_lines[0].split(":")[-1].strip() if ":" in yield_lines[0] else None
        
        if "profitability index" in raw_metrics.lower():
            pi_lines = [line for line in raw_metrics.split("\n") if "profitability index" in line.lower()]
            if pi_lines:
                metrics["profitability_index"] = pi_lines[0].split(":")[-1].strip() if ":" in pi_lines[0] else None
        
        return metrics 