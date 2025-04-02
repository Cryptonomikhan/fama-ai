"""
Visualization Tools for Financial Modeling.

This module provides tools for generating interactive dashboards and visualizations
for financial models and analysis.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VisualizationTools:
    """
    Tools for creating financial visualizations and dashboards.
    
    Provides methods for generating revenue charts, financial statement visualizations,
    and interactive dashboards with customizable branding.
    """
    
    def __init__(self):
        self.name = "VisualizationTools"
        self.description = "Tools for creating financial visualizations and dashboards"
        
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
    
    async def create_revenue_chart(self, query: str) -> str:
        """
        Create a revenue projection chart.
        
        Args:
            query: Query with chart data or parameters
            
        Returns:
            Chart configuration in JSON format for the frontend
        """
        logger.info("Creating revenue projection chart")
        
        # Parse chart data from query
        # In a real implementation, this would be more sophisticated
        chart_data = None
        
        # Check if the query is a dictionary with chart_data
        if isinstance(query, dict) and 'chart_data' in query:
            chart_data = query['chart_data']
        else:
            # Try to parse JSON from the query string
            try:
                # Look for JSON block in the query
                import re
                json_match = re.search(r"```json\n([\s\S]*?)\n```", query)
                if json_match:
                    chart_data = json.loads(json_match.group(1))
            except:
                # If we can't find valid JSON, we'll use simulated data
                pass
        
        # If we still don't have chart data, use simulated data
        if not chart_data:
            # Generate simulated data for demonstration
            months = list(range(1, 61))  # 5 years (60 months)
            revenue = [10000 * (1.05 ** (i / 12)) for i in range(60)]  # 5% annual growth
            
            chart_data = {
                "months": months,
                "revenue": revenue
            }
        
        # Extract color scheme from query (default to the default scheme)
        color_scheme = self.color_schemes["default"]
        if isinstance(query, dict) and "color_scheme" in query:
            scheme_name = query["color_scheme"]
            if scheme_name in self.color_schemes:
                color_scheme = self.color_schemes[scheme_name]
        
        # Create a chart configuration
        chart_config = {
            "type": "line",
            "title": "Revenue Projection",
            "subtitle": "Monthly Revenue Growth",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {month}" for month in chart_data["months"]]
            },
            "y_axis": {
                "title": "Revenue ($)",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Projected Revenue",
                    "data": chart_data["revenue"],
                    "color": color_scheme["primary"]
                }
            ],
            "annotations": [
                {
                    "x": 12,
                    "label": "Year 1",
                    "color": color_scheme["accent1"]
                },
                {
                    "x": 24,
                    "label": "Year 2",
                    "color": color_scheme["accent1"]
                },
                {
                    "x": 36,
                    "label": "Year 3",
                    "color": color_scheme["accent1"]
                },
                {
                    "x": 48,
                    "label": "Year 4",
                    "color": color_scheme["accent1"]
                }
            ],
            "colors": color_scheme,
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        # Return the chart configuration as JSON
        return json.dumps(chart_config, indent=2)
    
    async def create_metrics_dashboard(self, query: str) -> str:
        """
        Create a KPI metrics dashboard.
        
        Args:
            query: Query with metrics data or parameters
            
        Returns:
            Dashboard configuration in JSON format for the frontend
        """
        logger.info("Creating KPI metrics dashboard")
        
        # Parse metrics data from query
        metrics_data = None
        
        # Check if the query is a dictionary with metrics_data
        if isinstance(query, dict) and 'metrics_data' in query:
            metrics_data = query['metrics_data']
        else:
            # Try to parse JSON from the query string
            try:
                # Look for JSON block in the query
                import re
                json_match = re.search(r"```json\n([\s\S]*?)\n```", query)
                if json_match:
                    metrics_data = json.loads(json_match.group(1))
            except:
                # If we can't find valid JSON, we'll use simulated data
                pass
        
        # If we still don't have metrics data, use simulated data
        if not metrics_data:
            # Generate simulated data for demonstration
            metrics_data = {
                "cac": 300,
                "clv": 1500,
                "ltv_cac_ratio": 5,
                "payback_period": 6,
                "gross_margin": 0.7,
                "churn_rate": 0.05,
                "arpu": 50,
                "monthly_burn_rate": 25000,
                "runway_months": 18,
                "break_even_month": 14
            }
        
        # Extract color scheme from query (default to the default scheme)
        color_scheme = self.color_schemes["default"]
        if isinstance(query, dict) and "color_scheme" in query:
            scheme_name = query["color_scheme"]
            if scheme_name in self.color_schemes:
                color_scheme = self.color_schemes[scheme_name]
        
        # Create a metrics dashboard configuration
        dashboard_config = {
            "type": "metrics",
            "title": "Key Financial Metrics",
            "layout": "grid",
            "colors": color_scheme,
            "metrics": [
                {
                    "title": "Customer Acquisition Cost (CAC)",
                    "value": metrics_data.get("cac", 0),
                    "format": "currency",
                    "description": "Average cost to acquire a new customer",
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Customer Lifetime Value (CLV)",
                    "value": metrics_data.get("clv", 0),
                    "format": "currency",
                    "description": "Average revenue a customer generates",
                    "color": color_scheme["primary"]
                },
                {
                    "title": "LTV:CAC Ratio",
                    "value": metrics_data.get("ltv_cac_ratio", 0),
                    "format": "decimal",
                    "description": "Ratio of customer value to acquisition cost",
                    "threshold": {
                        "good": 3,
                        "warning": 2,
                        "bad": 1
                    },
                    "color": color_scheme["primary"]
                },
                {
                    "title": "CAC Payback Period",
                    "value": metrics_data.get("payback_period", 0),
                    "format": "months",
                    "description": "Months to recoup customer acquisition cost",
                    "threshold": {
                        "good": 6,
                        "warning": 12,
                        "bad": 18
                    },
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Gross Margin",
                    "value": metrics_data.get("gross_margin", 0),
                    "format": "percentage",
                    "description": "Revenue minus cost of goods sold divided by revenue",
                    "threshold": {
                        "good": 0.6,
                        "warning": 0.4,
                        "bad": 0.2
                    },
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Monthly Churn Rate",
                    "value": metrics_data.get("churn_rate", 0),
                    "format": "percentage",
                    "description": "Percentage of customers who cancel each month",
                    "threshold": {
                        "good": 0.03,
                        "warning": 0.05,
                        "bad": 0.08
                    },
                    "inverted_threshold": True,  # Lower is better
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Average Revenue Per User",
                    "value": metrics_data.get("arpu", 0),
                    "format": "currency",
                    "description": "Average monthly revenue per customer",
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Monthly Burn Rate",
                    "value": metrics_data.get("monthly_burn_rate", 0),
                    "format": "currency",
                    "description": "Rate at which company uses cash each month",
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Runway",
                    "value": metrics_data.get("runway_months", 0),
                    "format": "months",
                    "description": "Months of operation remaining at current burn rate",
                    "threshold": {
                        "good": 12,
                        "warning": 6,
                        "bad": 3
                    },
                    "color": color_scheme["primary"]
                },
                {
                    "title": "Break-Even Point",
                    "value": metrics_data.get("break_even_month", 0),
                    "format": "months",
                    "description": "Month when the business becomes profitable",
                    "threshold": {
                        "good": 12,
                        "warning": 18,
                        "bad": 24
                    },
                    "inverted_threshold": True,  # Lower is better
                    "color": color_scheme["primary"]
                }
            ],
            "responsive": True
        }
        
        # Return the dashboard configuration as JSON
        return json.dumps(dashboard_config, indent=2)
    
    async def create_scenario_chart(self, query: str) -> str:
        """
        Create a scenario comparison chart.
        
        Args:
            query: Query with scenario data or parameters
            
        Returns:
            Chart configuration in JSON format for the frontend
        """
        logger.info("Creating scenario comparison chart")
        
        # Parse scenario data from query
        scenario_data = None
        
        # Check if the query is a dictionary with scenario_data
        if isinstance(query, dict) and 'scenario_data' in query:
            scenario_data = query['scenario_data']
        else:
            # Try to parse JSON from the query string
            try:
                # Look for JSON block in the query
                import re
                json_match = re.search(r"```json\n([\s\S]*?)\n```", query)
                if json_match:
                    scenario_data = json.loads(json_match.group(1))
            except:
                # If we can't find valid JSON, we'll use simulated data
                pass
        
        # If we still don't have scenario data, use simulated data
        if not scenario_data:
            # Generate simulated data for demonstration
            years = list(range(1, 6))  # 5 years
            
            scenario_data = {
                "years": years,
                "revenue": {
                    "base": [100000, 200000, 350000, 500000, 750000],
                    "optimistic": [120000, 250000, 450000, 700000, 1000000],
                    "pessimistic": [80000, 150000, 250000, 350000, 500000]
                },
                "profit": {
                    "base": [0, 50000, 100000, 200000, 300000],
                    "optimistic": [20000, 80000, 180000, 300000, 450000],
                    "pessimistic": [-30000, 10000, 50000, 100000, 150000]
                }
            }
        
        # Extract color scheme from query (default to the default scheme)
        color_scheme = self.color_schemes["default"]
        if isinstance(query, dict) and "color_scheme" in query:
            scheme_name = query["color_scheme"]
            if scheme_name in self.color_schemes:
                color_scheme = self.color_schemes[scheme_name]
        
        # Create a chart configuration for revenue scenarios
        revenue_chart_config = {
            "type": "bar",
            "title": "Revenue Scenario Comparison",
            "subtitle": "Annual Revenue Projections by Scenario",
            "x_axis": {
                "title": "Year",
                "data": [f"Year {year}" for year in scenario_data["years"]]
            },
            "y_axis": {
                "title": "Revenue ($)",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Base Case",
                    "data": scenario_data["revenue"]["base"],
                    "color": color_scheme["primary"]
                },
                {
                    "name": "Optimistic Case",
                    "data": scenario_data["revenue"]["optimistic"],
                    "color": color_scheme["accent1"]
                },
                {
                    "name": "Pessimistic Case",
                    "data": scenario_data["revenue"]["pessimistic"],
                    "color": color_scheme["accent2"]
                }
            ],
            "colors": color_scheme,
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        # Create a chart configuration for profit scenarios
        profit_chart_config = {
            "type": "bar",
            "title": "Profit Scenario Comparison",
            "subtitle": "Annual Profit Projections by Scenario",
            "x_axis": {
                "title": "Year",
                "data": [f"Year {year}" for year in scenario_data["years"]]
            },
            "y_axis": {
                "title": "Profit ($)",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Base Case",
                    "data": scenario_data["profit"]["base"],
                    "color": color_scheme["primary"]
                },
                {
                    "name": "Optimistic Case",
                    "data": scenario_data["profit"]["optimistic"],
                    "color": color_scheme["accent1"]
                },
                {
                    "name": "Pessimistic Case",
                    "data": scenario_data["profit"]["pessimistic"],
                    "color": color_scheme["accent2"]
                }
            ],
            "colors": color_scheme,
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        # Combine the charts into a dashboard
        dashboard_config = {
            "title": "Scenario Analysis",
            "charts": [
                revenue_chart_config,
                profit_chart_config
            ],
            "layout": "vertical",
            "colors": color_scheme
        }
        
        # Return the dashboard configuration as JSON
        return json.dumps(dashboard_config, indent=2)
    
    async def create_dashboard(self, query: str) -> str:
        """
        Create a comprehensive financial dashboard with multiple charts and KPIs.
        
        Args:
            query: Query with financial model data or parameters
            
        Returns:
            Complete dashboard configuration in JSON format for the frontend
        """
        logger.info("Creating comprehensive financial dashboard")
        
        # Parse financial model data from query
        model_data = None
        white_label_config = None
        
        # Check if the query is a dictionary with the necessary data
        if isinstance(query, dict):
            if 'financial_model' in query:
                model_data = query['financial_model']
            if 'white_label_config' in query:
                white_label_config = query['white_label_config']
        
        # If we don't have model data, use simulated data
        if not model_data:
            # This is a simplified model for demonstration
            # In a real implementation, we would expect more complete data
            model_data = {
                "model_type": "Subscription",
                "timeframe_years": 5,
                "revenue_projections": {
                    "monthly": {
                        "customers": [100 + 10 * i for i in range(60)],
                        "revenue": [5000 + 500 * i for i in range(60)]
                    },
                    "annual": {
                        "revenue": [90000, 180000, 300000, 420000, 540000]
                    }
                },
                "expense_projections": {
                    "monthly": {
                        "total": [4000 + 300 * i for i in range(60)]
                    },
                    "annual": {
                        "total": [60000, 120000, 180000, 240000, 300000]
                    }
                },
                "key_financial_metrics": {
                    "cac": 300,
                    "clv": 1500,
                    "arpu": 50,
                    "roi": 5,
                    "payback_period": 6,
                    "gross_margin": 0.7,
                    "net_margin": 0.3,
                    "monthly_burn_rate": 25000,
                    "runway": 18,
                    "break_even_point": {
                        "month": 14,
                        "customers": 150
                    }
                },
                "scenarios": {
                    "base": [
                        {"year": 1, "revenue": 90000, "expenses": 60000, "profit": 30000},
                        {"year": 2, "revenue": 180000, "expenses": 120000, "profit": 60000},
                        {"year": 3, "revenue": 300000, "expenses": 180000, "profit": 120000},
                        {"year": 4, "revenue": 420000, "expenses": 240000, "profit": 180000},
                        {"year": 5, "revenue": 540000, "expenses": 300000, "profit": 240000}
                    ],
                    "optimistic": [
                        {"year": 1, "revenue": 108000, "expenses": 54000, "profit": 54000},
                        {"year": 2, "revenue": 216000, "expenses": 108000, "profit": 108000},
                        {"year": 3, "revenue": 360000, "expenses": 162000, "profit": 198000},
                        {"year": 4, "revenue": 504000, "expenses": 216000, "profit": 288000},
                        {"year": 5, "revenue": 648000, "expenses": 270000, "profit": 378000}
                    ],
                    "pessimistic": [
                        {"year": 1, "revenue": 72000, "expenses": 66000, "profit": 6000},
                        {"year": 2, "revenue": 144000, "expenses": 132000, "profit": 12000},
                        {"year": 3, "revenue": 240000, "expenses": 198000, "profit": 42000},
                        {"year": 4, "revenue": 336000, "expenses": 264000, "profit": 72000},
                        {"year": 5, "revenue": 432000, "expenses": 330000, "profit": 102000}
                    ]
                }
            }
        
        # Process white label configuration
        branding = self._process_white_label_config(white_label_config)
        
        # Create KPI metrics dashboard
        metrics_dashboard = self._create_metrics_component(model_data["key_financial_metrics"], branding)
        
        # Create revenue chart
        revenue_chart = self._create_revenue_chart_component(model_data, branding)
        
        # Create profit chart
        profit_chart = self._create_profit_chart_component(model_data, branding)
        
        # Create scenario chart
        scenario_chart = self._create_scenario_chart_component(model_data["scenarios"], branding)
        
        # Create the main dashboard layout
        dashboard_config = {
            "title": f"Financial Model: {model_data['model_type']}",
            "subtitle": f"{model_data['timeframe_years']} Year Financial Projection",
            "branding": branding,
            "layout": [
                {
                    "type": "row",
                    "height": "25%",
                    "components": [
                        {
                            "type": "metrics",
                            "component": metrics_dashboard,
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
                            "component": revenue_chart,
                            "width": "50%"
                        },
                        {
                            "type": "chart",
                            "component": profit_chart,
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
                            "component": scenario_chart,
                            "width": "100%"
                        }
                    ]
                }
            ],
            "filters": [
                {
                    "name": "Time Period",
                    "type": "range",
                    "default": [1, model_data['timeframe_years'] * 12],
                    "min": 1,
                    "max": model_data['timeframe_years'] * 12
                }
            ],
            "responsive": True,
            "export_options": ["pdf", "png", "csv"]
        }
        
        # Return the dashboard configuration as JSON
        return json.dumps(dashboard_config, indent=2)
    
    def _process_white_label_config(self, white_label_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Process white label configuration to create branding settings."""
        # Default branding settings
        branding = {
            "logo_url": None,
            "company_name": "Financial Model",
            "show_powered_by": True,
            "colors": self.color_schemes["default"],
            "font_family": "Roboto, sans-serif"
        }
        
        # Update with provided white label config if available
        if white_label_config:
            if "logo_url" in white_label_config:
                branding["logo_url"] = white_label_config["logo_url"]
            
            if "company_name" in white_label_config:
                branding["company_name"] = white_label_config["company_name"]
            
            if "show_powered_by" in white_label_config:
                branding["show_powered_by"] = white_label_config["show_powered_by"]
            
            if "font_family" in white_label_config:
                branding["font_family"] = white_label_config["font_family"]
            
            if "colors" in white_label_config:
                # Start with the default color scheme
                colors = self.color_schemes["default"].copy()
                
                # Update with provided colors
                for key, value in white_label_config["colors"].items():
                    if key in colors:
                        colors[key] = value
                
                branding["colors"] = colors
        
        return branding
    
    def _create_metrics_component(self, metrics_data: Dict[str, Any], branding: Dict[str, Any]) -> Dict[str, Any]:
        """Create a KPI metrics dashboard component."""
        metrics_component = {
            "type": "metrics",
            "title": "Key Financial Metrics",
            "layout": "grid",
            "colors": branding["colors"],
            "metrics": [
                {
                    "title": "Customer Acquisition Cost",
                    "value": metrics_data.get("cac", 0),
                    "format": "currency",
                    "description": "Average cost to acquire a new customer",
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Customer Lifetime Value",
                    "value": metrics_data.get("clv", 0),
                    "format": "currency",
                    "description": "Average revenue a customer generates",
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "LTV/CAC Ratio",
                    "value": metrics_data.get("roi", 0),
                    "format": "decimal",
                    "description": "Ratio of customer value to acquisition cost",
                    "threshold": {
                        "good": 3,
                        "warning": 2,
                        "bad": 1
                    },
                    "color": branding["colors"]["primary"]
                },
                {
                    "title": "Gross Margin",
                    "value": metrics_data.get("gross_margin", 0),
                    "format": "percentage",
                    "description": "Revenue minus cost of goods sold divided by revenue",
                    "threshold": {
                        "good": 0.6,
                        "warning": 0.4,
                        "bad": 0.2
                    },
                    "color": branding["colors"]["primary"]
                }
            ]
        }
        
        return metrics_component
    
    def _create_revenue_chart_component(self, model_data: Dict[str, Any], branding: Dict[str, Any]) -> Dict[str, Any]:
        """Create a revenue chart component."""
        # Extract monthly revenue data
        months = list(range(1, len(model_data["revenue_projections"]["monthly"]["revenue"]) + 1))
        revenue = model_data["revenue_projections"]["monthly"]["revenue"]
        
        revenue_chart = {
            "type": "line",
            "title": "Revenue Projection",
            "subtitle": "Monthly Revenue Growth",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {month}" for month in months]
            },
            "y_axis": {
                "title": "Revenue ($)",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Projected Revenue",
                    "data": revenue,
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
                },
                {
                    "x": 36,
                    "label": "Year 3",
                    "color": branding["colors"]["accent1"]
                },
                {
                    "x": 48,
                    "label": "Year 4",
                    "color": branding["colors"]["accent1"]
                }
            ],
            "colors": branding["colors"],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return revenue_chart
    
    def _create_profit_chart_component(self, model_data: Dict[str, Any], branding: Dict[str, Any]) -> Dict[str, Any]:
        """Create a profit chart component."""
        # Extract monthly revenue and expense data
        months = list(range(1, len(model_data["revenue_projections"]["monthly"]["revenue"]) + 1))
        revenue = model_data["revenue_projections"]["monthly"]["revenue"]
        expenses = model_data["expense_projections"]["monthly"]["total"]
        
        # Calculate profit
        profit = [r - e for r, e in zip(revenue, expenses)]
        
        profit_chart = {
            "type": "area",
            "title": "Profit Projection",
            "subtitle": "Monthly Profit Growth",
            "x_axis": {
                "title": "Month",
                "data": [f"Month {month}" for month in months]
            },
            "y_axis": {
                "title": "Profit ($)",
                "format": "currency"
            },
            "series": [
                {
                    "name": "Profit",
                    "data": profit,
                    "color": branding["colors"]["accent1"]
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
            "colors": branding["colors"],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return profit_chart
    
    def _create_scenario_chart_component(self, scenarios: Dict[str, List[Dict[str, Any]]], branding: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scenario chart component."""
        # Extract years and data from scenarios
        years = [scenario["year"] for scenario in scenarios["base"]]
        base_revenue = [scenario["revenue"] for scenario in scenarios["base"]]
        base_profit = [scenario["profit"] for scenario in scenarios["base"]]
        optimistic_revenue = [scenario["revenue"] for scenario in scenarios["optimistic"]]
        optimistic_profit = [scenario["profit"] for scenario in scenarios["optimistic"]]
        pessimistic_revenue = [scenario["revenue"] for scenario in scenarios["pessimistic"]]
        pessimistic_profit = [scenario["profit"] for scenario in scenarios["pessimistic"]]
        
        scenario_chart = {
            "type": "bar",
            "title": "Scenario Analysis",
            "subtitle": "Annual Profit Comparison by Scenario",
            "x_axis": {
                "title": "Year",
                "data": [f"Year {year}" for year in years]
            },
            "y_axis": {
                "title": "Profit ($)",
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
            "colors": branding["colors"],
            "tooltips": True,
            "legend": True,
            "grid": True,
            "responsive": True
        }
        
        return scenario_chart 