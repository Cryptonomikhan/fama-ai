#!/usr/bin/env python3
"""
Dashboard Builder Agent for Fama AI.

This agent is responsible for creating interactive Next.js dashboards
from financial modeling results using the Agno Agent Framework.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

from agno.agent import Agent

from models.model_factory import create_model
from tools.dashboard_tools import NextJsTemplateGeneratorTool, ChartComponentGeneratorTool
from tools.thinking_tools import ThinkingTool, CodeReasoningTool

# Set up logging
logger = logging.getLogger(__name__)

class DashboardBuilderAgent:
    """
    Agent for building interactive Next.js dashboards from financial modeling results.
    
    This agent uses specialized tools to create dashboard components for visualizing
    financial data, including charts, metrics displays, and scenario comparisons.
    """
    
    def __init__(
        self,
        provider: str = "anthropic",
        model_id: Optional[str] = None,
        temperature: float = 0.2,
        output_dir: str = "dashboard",
        **kwargs: Any
    ):
        """
        Initialize the Dashboard Builder Agent.
        
        Args:
            provider: Model provider (e.g., "anthropic", "openai")
            model_id: Specific model ID to use, if None will use default for provider
            temperature: Controls randomness of output (0.0-1.0)
            output_dir: Directory where dashboard files will be generated
            **kwargs: Additional parameters for the model
        """
        # Create model
        self.model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            **kwargs
        )
        
        # Store configuration
        self.output_dir = output_dir
        
        # Initialize dashboard tools
        nextjs_tool = NextJsTemplateGeneratorTool(output_dir=output_dir)
        chart_tool = ChartComponentGeneratorTool(output_dir=output_dir)
        thinking_tool = ThinkingTool()
        code_reasoning_tool = CodeReasoningTool()
        
        # Create the Agno agent with dashboard tools
        self.agent = Agent(
            model=self.model,
            name="Dashboard Builder",
            role="Financial dashboard developer",
            description="An expert in creating interactive Next.js dashboards for financial data visualization",
            instructions=[
                "Analyze financial data structure to identify key metrics for visualization",
                "Design dashboard components that effectively communicate financial insights",
                "Create React components for visualizing financial data using Next.js and charting libraries",
                "Ensure responsive design and professional appearance for all dashboard elements",
                "Use the thinking tool to break down complex tasks into manageable steps",
                "Use code reasoning for designing component architecture and data flow",
                "Follow best practices for React and Next.js development"
            ],
            tools=[
                thinking_tool,
                code_reasoning_tool,
                nextjs_tool,
                chart_tool
            ],
            markdown=True,
            show_tool_calls=False
        )
        
        # Create dashboard output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        logger.info(f"Dashboard Builder Agent initialized with {provider} model and output directory: {output_dir}")
        
    def create_dashboard(
        self,
        results: Dict[str, Any],
        project_name: str = "fama-dashboard",
        theme: str = "light",
        chart_library: str = "recharts",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate a Next.js dashboard from financial modeling results.
        
        Args:
            results: Financial modeling results containing research, market conditions,
                    yield data, financial model, metrics, scenarios, etc.
            project_name: Name of the dashboard project
            theme: Dashboard theme ("light" or "dark")
            chart_library: Chart library to use ("recharts", "chart.js", or "d3")
            **kwargs: Additional parameters for dashboard generation
            
        Returns:
            Dictionary containing dashboard generation results and paths
        """
        logger.info(f"Starting dashboard generation for project: {project_name}")
        
        try:
            # Step 1: Create the Next.js project template
            template_config = {
                "project_name": project_name,
                "theme": theme,
                "chart_library": chart_library,
                "typescript": kwargs.get("typescript", True)
            }
            
            template_response = self.agent.run_tool(
                "nextjs_template_generator",
                json.dumps(template_config)
            )
            template_result = json.loads(template_response)
            
            if not template_result.get("success", False):
                error_msg = template_result.get("error", "Unknown error creating template")
                logger.error(f"Failed to create dashboard template: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Track completed components
            completed_components = []
            
            # Step 2: Create Financial Metrics Chart Components
            if "financial_metrics" in results:
                metrics_chart = self._create_metrics_chart(
                    results["financial_metrics"],
                    project_name,
                    chart_library,
                    kwargs.get("typescript", True)
                )
                if metrics_chart.get("success", False):
                    completed_components.append(metrics_chart)
            
            # Step 3: Create Scenario Comparison Chart
            if "scenarios" in results and "scenario_impact" in results:
                scenario_chart = self._create_scenario_chart(
                    results["scenarios"],
                    results["scenario_impact"],
                    project_name,
                    chart_library,
                    kwargs.get("typescript", True)
                )
                if scenario_chart.get("success", False):
                    completed_components.append(scenario_chart)
            
            # Step 4: Create Yield Comparison Chart
            if "yield_data" in results:
                yield_chart = self._create_yield_chart(
                    results["yield_data"],
                    project_name,
                    chart_library,
                    kwargs.get("typescript", True)
                )
                if yield_chart.get("success", False):
                    completed_components.append(yield_chart)
            
            # Prepare dashboard generation results
            dashboard_result = {
                "success": True,
                "project_name": project_name,
                "project_directory": os.path.join(self.output_dir, project_name),
                "components_created": completed_components,
                "next_steps": [
                    "Navigate to the project directory",
                    "Run 'npm install' to install dependencies",
                    "Run 'npm run dev' to start the development server"
                ]
            }
            
            logger.info(f"Dashboard generation completed successfully for project: {project_name}")
            return dashboard_result
            
        except Exception as e:
            error_msg = f"Error generating dashboard: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _create_metrics_chart(
        self,
        metrics: Dict[str, Any],
        project_name: str,
        chart_library: str,
        use_typescript: bool
    ) -> Dict[str, Any]:
        """Create a chart component for financial metrics."""
        
        # Transform metrics data for chart
        chart_data = []
        for key, value in metrics.items():
            if key != "details" and isinstance(value, (int, float)):
                chart_data.append({
                    "metric": key.replace("_", " ").title(),
                    "value": value
                })
        
        chart_config = {
            "project_name": project_name,
            "chart_type": "bar",
            "chart_title": "Financial Metrics",
            "chart_description": "Key financial metrics from the investment model",
            "chart_library": chart_library,
            "typescript": use_typescript,
            "data_structure": {
                "items": chart_data
            }
        }
        
        chart_response = self.agent.run_tool(
            "chart_component_generator",
            json.dumps(chart_config)
        )
        
        try:
            return json.loads(chart_response)
        except Exception as e:
            logger.error(f"Error parsing metrics chart response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_scenario_chart(
        self,
        scenarios: Dict[str, Any],
        scenario_impact: Dict[str, Any],
        project_name: str,
        chart_library: str,
        use_typescript: bool
    ) -> Dict[str, Any]:
        """Create a chart component for scenario comparison."""
        
        # Transform scenario data for chart
        chart_data = []
        
        # Get the impact metrics
        scenario_names = ["baseline", "bull", "bear"]
        metrics = ["irr", "npv", "roi", "payback_period"]
        
        for metric in metrics:
            if metric in scenario_impact:
                data_item = {"metric": metric.replace("_", " ").title()}
                
                for scenario in scenario_names:
                    if scenario in scenario_impact[metric]:
                        data_item[scenario] = scenario_impact[metric][scenario]
                
                chart_data.append(data_item)
        
        chart_config = {
            "project_name": project_name,
            "chart_type": "bar",
            "chart_title": "Scenario Comparison",
            "chart_description": "Comparison of financial metrics across different scenarios",
            "chart_library": chart_library,
            "typescript": use_typescript,
            "data_structure": {
                "items": chart_data
            }
        }
        
        chart_response = self.agent.run_tool(
            "chart_component_generator",
            json.dumps(chart_config)
        )
        
        try:
            return json.loads(chart_response)
        except Exception as e:
            logger.error(f"Error parsing scenario chart response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_yield_chart(
        self,
        yield_data: Dict[str, Any],
        project_name: str,
        chart_library: str,
        use_typescript: bool
    ) -> Dict[str, Any]:
        """Create a chart component for yield comparison."""
        
        # Transform yield data for chart
        chart_data = []
        
        # If yield_data is a simple dictionary with yield values
        if isinstance(yield_data, dict):
            for key, value in yield_data.items():
                if isinstance(value, (int, float)):
                    chart_data.append({
                        "category": key.replace("_", " ").title(),
                        "yield": value
                    })
        # If yield_data is a list of comparable investments
        elif isinstance(yield_data, list):
            for item in yield_data:
                if isinstance(item, dict) and "name" in item and "yield" in item:
                    chart_data.append({
                        "category": item["name"],
                        "yield": item["yield"]
                    })
        
        if not chart_data:
            return {"success": False, "error": "Could not extract yield data in a suitable format"}
        
        chart_config = {
            "project_name": project_name,
            "chart_type": "bar",
            "chart_title": "Yield Comparison",
            "chart_description": "Comparison of yields across similar investments",
            "chart_library": chart_library,
            "typescript": use_typescript,
            "data_structure": {
                "items": chart_data
            }
        }
        
        chart_response = self.agent.run_tool(
            "chart_component_generator",
            json.dumps(chart_config)
        )
        
        try:
            return json.loads(chart_response)
        except Exception as e:
            logger.error(f"Error parsing yield chart response: {str(e)}")
            return {"success": False, "error": str(e)} 