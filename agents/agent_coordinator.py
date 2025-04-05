#!/usr/bin/env python3
"""
Agent Coordinator for Fama AI.

This module coordinates the interactions between specialized agents
to produce comprehensive financial models for investment vehicles.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from textwrap import dedent

from agno.agent import Agent
from agno.team import Team
from agno.models.message import Message

from models.model_factory import create_model
from agents.research import ResearchAgent
from agents.modeling import ModelingAgent
from agents.scenario_planner import ScenarioPlannerAgent
from agents.assumption_generator import AssumptionGeneratorAgent
from agents.validator import ValidatorAgent
from tools.report_tools import ReportGeneratorTool, PDFReportTool
from reports.report_generator import generate_report

# Set up logging
logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    Coordinates multiple specialized agents to generate financial models.
    
    This coordinator orchestrates the workflow between Research, Modeling,
    Scenario Planner, Assumption Generator, and Validator agents.
    """
    
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Initialize the Agent Coordinator with specialized agents.
        
        Args:
            provider: Model provider (e.g., "formation", "openai", "anthropic")
            model_id: Model ID to use (if None, will use default for provider)
            **kwargs: Additional keyword arguments for the models
        """
        logger.info("Initializing Agent Coordinator")
        
        # Create the specialized agents
        self.research_agent = ResearchAgent(
            provider=provider,
            model_id=model_id,
            temperature=0.2,
            **kwargs
        )
        
        self.assumption_generator = AssumptionGeneratorAgent(
            provider=provider,
            model_id=model_id,
            temperature=0.1,
            **kwargs
        )
        
        self.modeling_agent = ModelingAgent(
            provider=provider,
            model_id=model_id,
            temperature=0.1,
            **kwargs
        )
        
        self.scenario_planner = ScenarioPlannerAgent(
            provider=provider,
            model_id=model_id,
            temperature=0.1,
            **kwargs
        )
        
        self.validator = ValidatorAgent(
            provider=provider,
            model_id=model_id,
            temperature=0.1,
            **kwargs
        )
        
        # Create a coordinator model for the Team
        coordinator_model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=0.3,
            **kwargs
        )
        
        # Create the report generation tools
        self.report_tools = [
            ReportGeneratorTool(output_dir="reports"),
            PDFReportTool(output_dir="reports")
        ]
        
        # Create an Agent that will serve as the coordinator for the team
        self.coordinator = Agent(
            model=coordinator_model,
            name="Coordinator",
            role="Coordinates the financial modeling workflow",
            description=dedent("""
                You are a seasoned financial modeling expert who coordinates a team of specialized agents
                to create comprehensive financial models for yield-generating investment vehicles.
                Your expertise is in breaking down complex investment descriptions into structured analysis tasks,
                delegating to appropriate specialists, and synthesizing their outputs into a cohesive model.
            """),
            instructions=[
                "First, ensure deep market research is conducted before any modeling begins",
                "Generate critical assumptions based on research before building financial models",
                "Build financial models using well-researched assumptions and market data",
                "Create multiple scenarios to account for different market conditions",
                "Validate all aspects of the analysis to ensure accuracy and consistency",
                "Synthesize all outputs into a comprehensive financial analysis with clear documentation",
                "Generate well-formatted reports in requested formats (JSON, CSV, PDF)"
            ],
            tools=self.report_tools,
            markdown=True
        )
        
        # Create the Team with a sequential workflow in the optimal order
        self.team = Team(
            name="Financial Modeling Team",
            mode="sequential",  # Sequential mode for step-by-step processing
            members=[
                self.research_agent,
                self.assumption_generator,
                self.modeling_agent,
                self.scenario_planner,
                self.validator
            ],
            model=coordinator_model,
            success_criteria="A comprehensive financial model including income statements, cash flows, and IRR/NPV calculations with multiple scenarios based on well-researched assumptions.",
            instructions=[
                "STEP 1: Research Agent - Conduct deep research on the investment vehicle, market conditions, and gather all relevant data. This is the foundation of the analysis.",
                "STEP 2: Assumption Generator - Based on the research, generate critical modeling assumptions categorized by type (revenue, expenses, capital, market, financial).",
                "STEP 3: Modeling Agent - Using research data and assumptions, create detailed financial models including income statements, cash flows, and calculate key financial metrics.",
                "STEP 4: Scenario Planner - Build multiple scenarios (baseline, bull, bear) based on the financial model and conduct impact analysis.",
                "STEP 5: Validator - Comprehensively validate all aspects of the analysis including models, metrics, scenarios, and assumptions.",
                "STEP 6: Report Generation - Generate well-formatted reports in the requested format (JSON, CSV, PDF)."
            ],
            tools=self.report_tools,
            show_tool_calls=True,
            markdown=True,
            show_members_responses=True  # Set to True to show detailed agent responses in the logs
        )
        
        logger.info("Agent Coordinator initialized")
    
    def process_investment_vehicle(
        self,
        description: str,
        time_horizon: int = 5,
        risk_factors: str = "moderate",
        output_format: str = "json",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process an investment vehicle description to generate a financial model.
        
        This is the main entry point that coordinates the full workflow.
        
        Args:
            description: Natural language description of the investment vehicle
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            output_format: Format for output (json, csv, pdf)
            **kwargs: Additional parameters for the modeling process
            
        Returns:
            Dict containing the results of the financial modeling process
        """
        logger.info(f"Processing investment vehicle with {time_horizon} year horizon and {risk_factors} risk profile")
        
        # Generate a unique ID for this processing request
        request_id = str(uuid.uuid4())
        
        # For team-based processing, we have two options:
        # 1. Use the existing step-by-step approach (better for structured output)
        # 2. Use the Agno Team framework (better for agent coordination)
        
        # Determine if we should use the team approach
        use_team_approach = kwargs.get("use_team_approach", False)
        
        if use_team_approach:
            return self._process_with_team(
                request_id=request_id,
                description=description,
                time_horizon=time_horizon,
                risk_factors=risk_factors,
                output_format=output_format,
                **kwargs
            )
        else:
            return self._process_step_by_step(
                request_id=request_id,
                description=description,
                time_horizon=time_horizon,
                risk_factors=risk_factors,
                output_format=output_format,
                **kwargs
            )
    
    def _process_with_team(
        self,
        request_id: str,
        description: str,
        time_horizon: int,
        risk_factors: str,
        output_format: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process an investment vehicle using the Agno Team approach.
        
        Args:
            request_id: Unique identifier for this request
            description: Natural language description of the investment vehicle
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            output_format: Format for output (json, csv, pdf)
            **kwargs: Additional parameters for the modeling process
            
        Returns:
            Dict containing the results of the financial modeling process
        """
        logger.info("Processing investment vehicle using Team approach")
        
        # Build the prompt for the team
        prompt = dedent(f"""
            # Investment Vehicle Analysis Request
            
            ## Description
            {description}
            
            ## Parameters
            - Time Horizon: {time_horizon} years
            - Risk Profile: {risk_factors}
            - Research Context: {kwargs.get("research_context", "General market research")}
            - Output Format: {output_format}
            
            ## Task
            Please conduct a comprehensive financial analysis of this investment vehicle by following these steps:
            
            1. Deep market research on the underlying asset and investment vehicle structure
            2. Generate well-documented assumptions based on research findings
            3. Build detailed financial models using these assumptions
            4. Create baseline, bull, and bear scenarios to account for different market conditions
            5. Validate all aspects of the analysis for accuracy, consistency, and compliance
            6. Generate a comprehensive report in the requested format ({output_format})
            
            The analysis should include the following components:
            - Comprehensive market research including competitive landscape
            - Key assumptions categorized by type (revenue, expense, capital, market, financial)
            - Pro forma financial statements (income statement, cash flow)
            - Financial metrics (IRR, NPV, ROI, payback period)
            - Multiple scenario analyses with impact assessment
            - Validation report highlighting any issues or recommendations
            
            Please provide detailed explanations and documentation for all aspects of the analysis.
            
            After completing the analysis, please generate a report in {output_format} format using the report_generator or pdf_report_generator tool.
        """)
        
        # Process the investment vehicle with the team
        try:
            logger.info("Starting team-based analysis")
            response = self.team.run(prompt)
            logger.info("Team-based analysis completed")
            
            # Extract the results from the team's response
            # In a real implementation, this would parse the structured data from the response
            # For now, we'll just include the response content along with metadata
            results = {
                "request_id": request_id,
                "description": description,
                "time_horizon": time_horizon,
                "risk_factors": risk_factors,
                "team_response": response.content,
                "status": "complete",
                "output_format": output_format
            }
            
            # Generate a report from the results using the direct method
            # This ensures we have a report even if the team didn't generate one
            report_path = generate_report(
                results=results,
                format=output_format,
                filename=f"report_{request_id[:8]}",
                output_dir="reports"
            )
            
            # Add the report path to the results
            results["report_path"] = report_path
            
            return results
            
        except Exception as e:
            logger.error(f"Error in team-based analysis: {str(e)}")
            return {
                "request_id": request_id,
                "status": "error",
                "error": str(e)
            }
    
    def _process_step_by_step(
        self,
        request_id: str,
        description: str,
        time_horizon: int,
        risk_factors: str,
        output_format: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Process an investment vehicle step-by-step, following the optimal sequence.
        
        Args:
            request_id: Unique identifier for this request
            description: Natural language description of the investment vehicle
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            output_format: Format for output (json, csv, pdf)
            **kwargs: Additional parameters for the modeling process
            
        Returns:
            Dict containing the results of the financial modeling process
        """
        logger.info("Processing investment vehicle step-by-step")
        
        # Get the update callback if provided
        update_callback = kwargs.get("update_callback")
        
        # Step 1: Research Phase
        logger.info("Starting research phase")
        research_results = self.research_agent.research_investment_vehicle(
            description=description,
            time_horizon=time_horizon,
            additional_context=kwargs.get("research_context")
        )
        # Send update if callback is provided
        if update_callback:
            update_callback("research", research_results)
        
        # Get additional market conditions
        market_conditions = self.research_agent.get_market_conditions()
        if update_callback:
            update_callback("market_conditions", market_conditions)
        
        # Get yield data for similar investments
        yield_data = self.research_agent.get_yield_data(
            vehicle_type=kwargs.get("vehicle_type", "yield-generating investment"),
            time_period=f"last {time_horizon} years"
        )
        if update_callback:
            update_callback("yield_data", yield_data)
        
        # Step 2: Assumption Generation Phase (moved earlier in the workflow)
        logger.info("Starting assumption generation phase")
        assumptions = self.assumption_generator.generate_assumptions(
            description=description,
            research_data=research_results,
            market_conditions=market_conditions,
            yield_data=yield_data,
            time_horizon=time_horizon,
            risk_factors=risk_factors
        )
        if update_callback:
            update_callback("assumptions", assumptions)
        
        # Validate the assumptions
        assumption_validation = self.assumption_generator.validate_assumptions(
            assumptions=assumptions,
            research_data=research_results,
            market_conditions=market_conditions
        )
        if update_callback:
            update_callback("assumption_validation", assumption_validation)
        
        # Step 3: Modeling Phase (now uses validated assumptions)
        logger.info("Starting modeling phase")
        financial_model = self.modeling_agent.create_financial_model(
            description=description,
            research_data=research_results,
            market_conditions=market_conditions,
            yield_data=yield_data,
            assumptions=assumptions,  # Now passing validated assumptions to the model
            time_horizon=time_horizon,
            risk_factors=risk_factors
        )
        if update_callback:
            update_callback("financial_model", financial_model)
        
        # Generate financial metrics
        metrics = self.modeling_agent.generate_metrics(
            financial_model=financial_model,
            time_horizon=time_horizon,
            discount_rate=kwargs.get("discount_rate", 0.1)
        )
        if update_callback:
            update_callback("metrics", metrics)
        
        # Step 4: Scenario Planning Phase
        logger.info("Starting scenario planning phase")
        scenarios = self.scenario_planner.generate_scenarios(
            description=description,
            financial_model=financial_model,
            research_data=research_results,
            market_conditions=market_conditions,
            assumptions=assumptions,  # Now passing validated assumptions to scenarios
            risk_factors=risk_factors,
            time_horizon=time_horizon
        )
        if update_callback:
            update_callback("scenarios", scenarios)
        
        # Analyze the impact of different scenarios
        scenario_impact = self.scenario_planner.analyze_scenario_impact(
            scenarios=scenarios,
            financial_metrics=metrics
        )
        if update_callback:
            update_callback("scenario_impact", scenario_impact)
        
        # Step 5: Validation Phase
        logger.info("Starting validation phase")
        validation_results = self.validator.validate_model(
            description=description,
            financial_model=financial_model,
            assumptions=assumptions,
            metrics=metrics,
            scenarios=scenarios,
            research_data=research_results,
            market_conditions=market_conditions
        )
        if update_callback:
            update_callback("validation", validation_results)
        
        # Additional validation of specific components
        metric_validation = self.validator.validate_metrics(
            metrics=metrics,
            financial_model=financial_model
        )
        if update_callback:
            update_callback("metric_validation", metric_validation)
        
        scenario_validation = self.validator.validate_scenarios(
            scenarios=scenarios,
            financial_model=financial_model,
            assumptions=assumptions,
            market_conditions=market_conditions
        )
        if update_callback:
            update_callback("scenario_validation", scenario_validation)
        
        # Combine results
        results = {
            "request_id": request_id,
            "description": description,
            "time_horizon": time_horizon,
            "risk_factors": risk_factors,
            "research_results": research_results,
            "market_conditions": market_conditions,
            "yield_data": yield_data,
            "assumptions": assumptions,
            "assumption_validation": assumption_validation,
            "financial_model": financial_model,
            "metrics": metrics,
            "scenarios": scenarios,
            "scenario_impact": scenario_impact,
            "validation": {
                "model_validation": validation_results,
                "metric_validation": metric_validation,
                "scenario_validation": scenario_validation
            },
            "status": "complete",
            "output_format": output_format
        }
        
        # Step 6: Report Generation Phase
        logger.info(f"Starting report generation phase in {output_format} format")
        report_path = generate_report(
            results=results,
            format=output_format,
            filename=f"report_{request_id[:8]}",
            output_dir="reports"
        )
        
        # Add the report path to the results
        results["report_path"] = report_path
        
        # Final update with report path
        if update_callback:
            update_callback("report", {"path": report_path})
        
        logger.info(f"Investment vehicle processing completed. Report generated at {report_path}")
        return results
    
    async def process_investment_vehicle_async(
        self,
        description: str,
        time_horizon: int = 5,
        risk_factors: str = "moderate",
        output_format: str = "json",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Asynchronous version of the process_investment_vehicle method.
        
        This would be implemented when all agents support async operations.
        
        Args:
            description: Natural language description of the investment vehicle
            time_horizon: Time horizon for the investment in years
            risk_factors: Risk factors to consider (conservative, moderate, aggressive)
            output_format: Format for output (json, csv, pdf)
            **kwargs: Additional parameters for the modeling process
            
        Returns:
            Dict containing the results of the financial modeling process
        """
        # This is a placeholder for future async implementation
        # For now, we'll just call the synchronous version
        return self.process_investment_vehicle(
            description=description,
            time_horizon=time_horizon,
            risk_factors=risk_factors,
            output_format=output_format,
            **kwargs
        ) 