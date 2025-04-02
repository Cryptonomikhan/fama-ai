"""
Visualization Agent for Financial Modeling.
This agent is responsible for generating interactive dashboards and visualizations
based on the financial models and analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from textwrap import dedent
import json
from datetime import datetime

from agno.agent import Agent
from agno.tools import ToolSpec, tool

# Import our model helper
try:
    from src.utils.llm_models import get_llm_model
except ImportError:
    # Fallback or error handling if the util module isn't found
    logging.error("Could not import get_llm_model from src.utils.llm_models. Ensure the file exists and PYTHONPATH is correct.")
    # As a temporary fallback, you might import OpenAIChat directly, but it defeats the purpose
    from agno.models.openai import OpenAIChat as get_llm_model

logger = logging.getLogger(__name__)

class VisualizationAgent(Agent):
    """
    Agent specializing in visualization and dashboard generation.
    
    This agent converts financial models and analysis into interactive
    dashboards and visual reports that can be customized with white-label branding.
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        tools: Optional[List[Union[ToolSpec, callable]]] = None,
        **kwargs: Any,
    ):
        """Initialize the visualization agent with LLM model and tools."""
        _model = model or get_llm_model()
        _tools = tools or [
            # Add any specialized visualization tools here
        ]
        
        super().__init__(
            model=_model,
            tools=_tools,
            name="VisualizationSpecialist",
            description="Expert AI agent specialized in creating data visualizations and interactive dashboards from financial models.",
            instructions=dedent("""\
                You are a Visualization Specialist with expertise in financial dashboards.
                1. Transform financial model data into clear, impactful visualizations.
                2. Design responsive, interactive dashboard layouts.
                3. Apply white-label branding consistently across all elements.
                4. Create visuals that highlight key insights and trends.
                5. Optimize visualization formats for different data types and metrics.
                6. Generate executive summaries with the most critical visualizations.
            """),
            add_datetime_to_instructions=True,
            show_tool_calls=kwargs.pop('show_tool_calls', True),
            markdown=kwargs.pop('markdown', True),
            **kwargs,
        )
        
        logger.info("Initialized Visualization Agent with model and tools")
        
        # Define default color schemes and visualization templates
        self.color_schemes = {
            "default": {
                "primary": "#3366FF",
                "secondary": "#33CCFF",
                "background": "#F4F7FC",
                "text": "#2D3436",
                "accent1": "#00C896",
                "accent2": "#FF5A5F",
                "accent3": "#FFB400"
            },
            "dark": {
                "primary": "#4B7BFF",
                "secondary": "#50D8FF",
                "background": "#1A1D21",
                "text": "#E1E2E6",
                "accent1": "#00E6B0",
                "accent2": "#FF7478",
                "accent3": "#FFCB45"
            },
            "monochrome": {
                "primary": "#3C3C3C",
                "secondary": "#707070",
                "background": "#F8F8F8",
                "text": "#2A2A2A",
                "accent1": "#A3A3A3",
                "accent2": "#5A5A5A",
                "accent3": "#CCCCCC"
            }
        }
        
        # Define chart types for different data visualizations
        self.chart_types = {
            "revenue_projection": "line",
            "expense_breakdown": "stacked-area",
            "profit_margin": "line",
            "cash_flow": "bar",
            "customer_growth": "line",
            "kpi_dashboard": "metrics",
            "scenario_comparison": "grouped-bar"
        }
    
    async def create_visualizations(
        self,
        financial_model: Dict[str, Any],
        white_label_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate visualizations and dashboards based on the financial model.
        
        Args:
            financial_model: The comprehensive financial model with projections
            white_label_config: Customization options for white-label branding
            
        Returns:
            Dictionary containing visualization configurations and dashboard layouts
        """
        logger.info("Generating visualizations and dashboards")
        
        # Apply white label configuration if provided
        branding = self._apply_white_label_config(white_label_config)
        
        # Generate the various visualizations needed for the dashboard
        revenue_chart = self._create_revenue_chart(financial_model, branding)
        expense_chart = self._create_expense_chart(financial_model, branding)
        profit_chart = self._create_profit_chart(financial_model, branding)
        cash_flow_chart = self._create_cash_flow_chart(financial_model, branding)
        customer_chart = self._create_customer_chart(financial_model, branding)
        kpi_dashboard = self._create_kpi_dashboard(financial_model, branding)
        scenario_chart = self._create_scenario_chart(financial_model, branding)
        
        # Generate the main dashboard layout
        main_dashboard = self._create_dashboard_layout(
            financial_model,
            branding,
            {
                "revenue_chart": revenue_chart,
                "expense_chart": expense_chart,
                "profit_chart": profit_chart,
                "cash_flow_chart": cash_flow_chart,
                "customer_chart": customer_chart,
                "kpi_dashboard": kpi_dashboard,
                "scenario_chart": scenario_chart
            }
        )
        
        # Generate executive summary visualizations
        executive_summary = self._create_executive_summary(financial_model, branding)
        
        # Compile all visualizations into a complete package
        visualizations = {
            "dashboard": main_dashboard,
            "charts": {
                "revenue_chart": revenue_chart,
                "expense_chart": expense_chart,
                "profit_chart": profit_chart,
                "cash_flow_chart": cash_flow_chart,
                "customer_chart": customer_chart,
                "scenario_chart": scenario_chart
            },
            "kpi_dashboard": kpi_dashboard,
            "executive_summary": executive_summary,
            "branding": branding,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info("Completed visualization generation")
        return visualizations
    
    def _apply_white_label_config(
        self,
        white_label_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply white label configuration settings to create a branded experience."""
        logger.info("Applying white label configuration")
        
        # Start with default branding
        branding = {
            "colors": self.color_schemes["default"].copy(),
            "font_family": "Roboto, sans-serif",
            "logo_url": None,
            "company_name": "Financial Analysis",
            "show_powered_by": True
        }
        
        # If white label configuration is provided, apply customizations
        if white_label_config:
            # Apply custom colors if provided
            if "colors" in white_label_config:
                for key, value in white_label_config["colors"].items():
                    if key in branding["colors"]:
                        branding["colors"][key] = value
            
            # Apply custom font family if provided
            if "font_family" in white_label_config:
                branding["font_family"] = white_label_config["font_family"]
            
            # Apply logo URL if provided
            if "logo_url" in white_label_config:
                branding["logo_url"] = white_label_config["logo_url"]
            
            # Apply company name if provided
            if "company_name" in white_label_config:
                branding["company_name"] = white_label_config["company_name"]
            
            # Apply show_powered_by preference if provided
            if "show_powered_by" in white_label_config:
                branding["show_powered_by"] = white_label_config["show_powered_by"]
        
        return branding
    
    def _create_revenue_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a revenue projection chart."""
        logger.info("Creating revenue projection chart")
        
        # Extract revenue data from the financial model
        monthly_revenue = financial_model["revenue_projections"]["monthly"]["revenue"]
        
        # Create a configuration for a line chart showing revenue growth
        chart_config = {
            "type": "line",
            "title": "Revenue Projection",
            "subtitle": f"{financial_model['timeframe_years']} Year Projection",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {i+1}" for i in range(len(monthly_revenue))]
            },
            "y_axis": {
                "title": f"Revenue ({financial_model['currency']})",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Projected Revenue",
                    "data": monthly_revenue,
                    "color": branding["colors"]["primary"]
                }
            ],
            "annotations": [
                {
                    "x": 12,
                    "label": "Year 1",
                    "color": branding["colors"]["accent1"]
                },
                {
                    "x": 24,
                    "label": "Year 2",
                    "color": branding["colors"]["accent1"]
                }
            ],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_expense_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an expense breakdown chart."""
        logger.info("Creating expense breakdown chart")
        
        # Extract expense data from the financial model
        marketing_expenses = financial_model["expense_projections"]["monthly"]["marketing"]
        cogs = financial_model["expense_projections"]["monthly"]["cogs"]
        operating_expenses = financial_model["expense_projections"]["monthly"]["operating"]
        
        # Create a configuration for a stacked area chart showing expense breakdown
        chart_config = {
            "type": "stacked-area",
            "title": "Expense Breakdown",
            "subtitle": "Monthly Expense Categories",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {i+1}" for i in range(len(marketing_expenses))]
            },
            "y_axis": {
                "title": f"Expenses ({financial_model['currency']})",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Marketing & Customer Acquisition",
                    "data": marketing_expenses,
                    "color": branding["colors"]["accent2"]
                },
                {
                    "name": "Cost of Goods Sold",
                    "data": cogs,
                    "color": branding["colors"]["secondary"]
                },
                {
                    "name": "Operating Expenses",
                    "data": operating_expenses,
                    "color": branding["colors"]["accent3"]
                }
            ],
            "annotations": [],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_profit_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a profit margin chart."""
        logger.info("Creating profit margin chart")
        
        # Extract data from the financial model
        monthly_revenue = financial_model["revenue_projections"]["monthly"]["revenue"]
        monthly_expenses = financial_model["expense_projections"]["monthly"]["total"]
        
        # Calculate profit
        monthly_profit = [r - e for r, e in zip(monthly_revenue, monthly_expenses)]
        
        # Calculate profit margin as a percentage
        monthly_profit_margin = [
            (p / r) * 100 if r > 0 else 0
            for p, r in zip(monthly_profit, monthly_revenue)
        ]
        
        # Create a configuration for a combined line and bar chart
        chart_config = {
            "type": "combo",
            "title": "Profit and Margin Analysis",
            "subtitle": "Monthly Profit and Profit Margin",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {i+1}" for i in range(len(monthly_profit))]
            },
            "y_axis": [
                {
                    "title": f"Profit ({financial_model['currency']})",
                    "format": "currency",
                    "position": "left"
                },
                {
                    "title": "Profit Margin (%)",
                    "format": "percentage",
                    "position": "right"
                }
            ],
            "series": [
                {
                    "name": "Profit",
                    "type": "bar",
                    "data": monthly_profit,
                    "color": branding["colors"]["accent1"],
                    "y_axis_index": 0
                },
                {
                    "name": "Profit Margin",
                    "type": "line",
                    "data": monthly_profit_margin,
                    "color": branding["colors"]["primary"],
                    "y_axis_index": 1
                }
            ],
            "annotations": [
                {
                    "y": 0,
                    "label": "Break Even",
                    "color": branding["colors"]["accent2"],
                    "line_style": "dashed"
                }
            ],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_cash_flow_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a cash flow chart."""
        logger.info("Creating cash flow chart")
        
        # Extract cash flow data from the financial model
        monthly_cash_flow = financial_model["financial_statements"]["cash_flow"]["monthly"]["cash_flow"]
        monthly_ending_cash = financial_model["financial_statements"]["cash_flow"]["monthly"]["ending_cash"]
        
        # Create a configuration for a cash flow chart
        chart_config = {
            "type": "combo",
            "title": "Cash Flow Analysis",
            "subtitle": "Monthly Cash Flow and Ending Cash Balance",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {i+1}" for i in range(len(monthly_cash_flow))]
            },
            "y_axis": [
                {
                    "title": f"Cash Flow ({financial_model['currency']})",
                    "format": "currency",
                    "position": "left"
                },
                {
                    "title": f"Cash Balance ({financial_model['currency']})",
                    "format": "currency",
                    "position": "right"
                }
            ],
            "series": [
                {
                    "name": "Monthly Cash Flow",
                    "type": "bar",
                    "data": monthly_cash_flow,
                    "color": branding["colors"]["accent2"],
                    "y_axis_index": 0
                },
                {
                    "name": "Ending Cash Balance",
                    "type": "line",
                    "data": monthly_ending_cash,
                    "color": branding["colors"]["primary"],
                    "y_axis_index": 1
                }
            ],
            "annotations": [
                {
                    "y": 0,
                    "axis_index": 0,
                    "label": "Cash Flow Break Even",
                    "color": branding["colors"]["accent3"],
                    "line_style": "dashed"
                }
            ],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_customer_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a customer growth chart."""
        logger.info("Creating customer growth chart")
        
        # Extract customer data from the financial model
        monthly_customers = financial_model["revenue_projections"]["monthly"]["customers"]
        monthly_new_customers = financial_model["revenue_projections"]["monthly"]["new_customers"]
        monthly_churned_customers = financial_model["revenue_projections"]["monthly"]["churned_customers"]
        
        # Create a configuration for a customer growth chart
        chart_config = {
            "type": "combo",
            "title": "Customer Growth Analysis",
            "subtitle": "Monthly Customer Metrics",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {i+1}" for i in range(len(monthly_customers))]
            },
            "y_axis": [
                {
                    "title": "Customer Count",
                    "format": "number",
                    "position": "left"
                },
                {
                    "title": "New/Churned Customers",
                    "format": "number",
                    "position": "right"
                }
            ],
            "series": [
                {
                    "name": "Total Customers",
                    "type": "line",
                    "data": monthly_customers,
                    "color": branding["colors"]["primary"],
                    "y_axis_index": 0
                },
                {
                    "name": "New Customers",
                    "type": "bar",
                    "data": monthly_new_customers,
                    "color": branding["colors"]["accent1"],
                    "y_axis_index": 1
                },
                {
                    "name": "Churned Customers",
                    "type": "bar",
                    "data": monthly_churned_customers,
                    "color": branding["colors"]["accent2"],
                    "y_axis_index": 1
                }
            ],
            "annotations": [],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_kpi_dashboard(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a KPI metrics dashboard."""
        logger.info("Creating KPI metrics dashboard")
        
        # Extract key metrics from the financial model
        metrics = financial_model["key_financial_metrics"]
        
        # Create a configuration for a KPI metrics dashboard
        dashboard_config = {
            "type": "metrics",
            "title": "Key Financial Metrics",
            "layout": "grid",
            "metrics": [
                {
                    "title": "Customer Acquisition Cost (CAC)",
                    "value": metrics["cac"],
                    "format": "currency",
                    "description": "Average cost to acquire a new customer",
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Customer Lifetime Value (CLV)",
                    "value": metrics["clv"],
                    "format": "currency",
                    "description": "Average revenue a customer generates",
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "CLV:CAC Ratio",
                    "value": metrics["roi"],
                    "format": "number",
                    "description": "Ratio of customer value to acquisition cost",
                    "threshold": {
                        "good": 3,
                        "warning": 2,
                        "bad": 1
                    },
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "CAC Payback Period",
                    "value": metrics["payback_period"],
                    "format": "months",
                    "description": "Months to recoup customer acquisition cost",
                    "threshold": {
                        "good": 6,
                        "warning": 12,
                        "bad": 18
                    },
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Gross Margin",
                    "value": metrics["gross_margin"],
                    "format": "percentage",
                    "description": "Revenue minus cost of goods sold divided by revenue",
                    "threshold": {
                        "good": 0.6,
                        "warning": 0.4,
                        "bad": 0.2
                    },
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Net Margin",
                    "value": metrics["net_margin"],
                    "format": "percentage",
                    "description": "Net income divided by revenue",
                    "threshold": {
                        "good": 0.2,
                        "warning": 0.1,
                        "bad": 0
                    },
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Monthly Burn Rate",
                    "value": metrics["monthly_burn_rate"],
                    "format": "currency",
                    "description": "Rate at which company uses cash each month",
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Runway",
                    "value": metrics["runway"],
                    "format": "months",
                    "description": "Months of operation remaining at current burn rate",
                    "threshold": {
                        "good": 12,
                        "warning": 6,
                        "bad": 3
                    },
                    "color": branding["colors"]["primary"]
                }
            ],
            "responsive": True
        }
        
        return dashboard_config
    
    def _create_scenario_chart(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a scenario comparison chart."""
        logger.info("Creating scenario comparison chart")
        
        # Extract scenario data from the financial model
        base_scenario = financial_model["scenarios"]["base"]
        optimistic_scenario = financial_model["scenarios"]["optimistic"]
        pessimistic_scenario = financial_model["scenarios"]["pessimistic"]
        
        # Prepare data for the chart
        years = [scenario["year"] for scenario in base_scenario]
        base_profit = [scenario["profit"] for scenario in base_scenario]
        optimistic_profit = [scenario["profit"] for scenario in optimistic_scenario]
        pessimistic_profit = [scenario["profit"] for scenario in pessimistic_scenario]
        
        # Create a configuration for a scenario comparison chart
        chart_config = {
            "type": "grouped-bar",
            "title": "Scenario Analysis",
            "subtitle": "Profit Comparison Across Scenarios",
            "x_axis": {
                "title": "Year",
                "data": [f"Year {year}" for year in years]
            },
            "y_axis": {
                "title": f"Profit ({financial_model['currency']})",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Base Case",
                    "data": base_profit,
                    "color": branding["colors"]["primary"]
                },
                {
                    "name": "Optimistic Case",
                    "data": optimistic_profit,
                    "color": branding["colors"]["accent1"]
                },
                {
                    "name": "Pessimistic Case",
                    "data": pessimistic_profit,
                    "color": branding["colors"]["accent2"]
                }
            ],
            "annotations": [],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return chart_config
    
    def _create_dashboard_layout(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any],
        charts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create the main dashboard layout configuration."""
        logger.info("Creating main dashboard layout")
        
        # Create a configuration for the main dashboard layout
        dashboard_config = {
            "title": f"Financial Model: {financial_model['model_type']}",
            "subtitle": f"{financial_model['timeframe_years']} Year Financial Projection",
            "branding": {
                "logo_url": branding["logo_url"],
                "company_name": branding["company_name"],
                "show_powered_by": branding["show_powered_by"]
            },
            "theme": {
                "colors": branding["colors"],
                "font_family": branding["font_family"],
                "background_color": branding["colors"]["background"],
                "text_color": branding["colors"]["text"]
            },
            "layout": [
                {
                    "type": "row",
                    "height": "25%",
                    "components": [
                        {
                            "type": "chart",
                            "chart_id": "kpi_dashboard",
                            "width": "100%"
                        }
                    ]
                },
                {
                    "type": "row",
                    "height": "37.5%",
                    "components": [
                        {
                            "type": "chart",
                            "chart_id": "revenue_chart",
                            "width": "50%"
                        },
                        {
                            "type": "chart",
                            "chart_id": "profit_chart",
                            "width": "50%"
                        }
                    ]
                },
                {
                    "type": "row",
                    "height": "37.5%",
                    "components": [
                        {
                            "type": "chart",
                            "chart_id": "cash_flow_chart",
                            "width": "33%"
                        },
                        {
                            "type": "chart",
                            "chart_id": "customer_chart",
                            "width": "33%"
                        },
                        {
                            "type": "chart",
                            "chart_id": "scenario_chart",
                            "width": "34%"
                        }
                    ]
                }
            ],
            "filters": [
                {
                    "name": "Time Period",
                    "type": "range",
                    "default": [1, financial_model['timeframe_years'] * 12],
                    "min": 1,
                    "max": financial_model['timeframe_years'] * 12
                }
            ],
            "responsive": True,
            "export_options": ["pdf", "png", "csv"]
        }
        
        return dashboard_config
    
    def _create_executive_summary(
        self,
        financial_model: Dict[str, Any],
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an executive summary visualization."""
        logger.info("Creating executive summary")
        
        # Extract key metrics from the financial model
        kpis = financial_model["key_financial_metrics"]
        revenue_year5 = financial_model["revenue_projections"]["annual"]["revenue"][-1]
        cumulative_profit = sum([year["profit"] for year in financial_model["scenarios"]["base"]])
        break_even_month = kpis["break_even_point"]["month"]
        
        # Create a configuration for an executive summary
        summary_config = {
            "type": "executive_summary",
            "title": "Executive Summary",
            "subtitle": "Key Findings and Metrics",
            "sections": [
                {
                    "title": "Financial Highlights",
                    "items": [
                        {
                            "label": f"Year {financial_model['timeframe_years']} Revenue",
                            "value": revenue_year5,
                            "format": "currency"
                        },
                        {
                            "label": "Cumulative 5-Year Profit",
                            "value": cumulative_profit,
                            "format": "currency"
                        },
                        {
                            "label": "Break-Even Point",
                            "value": break_even_month,
                            "format": "month"
                        }
                    ]
                },
                {
                    "title": "Key Performance Indicators",
                    "items": [
                        {
                            "label": "Customer Acquisition Cost",
                            "value": kpis["cac"],
                            "format": "currency"
                        },
                        {
                            "label": "Customer Lifetime Value",
                            "value": kpis["clv"],
                            "format": "currency"
                        },
                        {
                            "label": "CAC Payback Period",
                            "value": kpis["payback_period"],
                            "format": "months"
                        }
                    ]
                },
                {
                    "title": "Revenue Model",
                    "text": f"The financial model is based on a {financial_model['model_type']} revenue model with an initial average revenue per customer of ${financial_model['starting_metrics']['average_revenue_per_customer']}."
                },
                {
                    "title": "Growth Trajectory",
                    "text": f"With a starting customer base of {financial_model['starting_metrics']['initial_customers']} and a customer acquisition rate of {financial_model['starting_metrics']['customer_acquisition_rate'] * 100}% per month, the business is projected to reach {round(financial_model['revenue_projections']['monthly']['customers'][-1])} customers by the end of year {financial_model['timeframe_years']}."
                }
            ],
            "theme": {
                "colors": branding["colors"],
                "font_family": branding["font_family"]
            }
        }
        
        return summary_config 