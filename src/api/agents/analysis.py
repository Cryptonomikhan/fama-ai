"""
Analysis Agent for Financial Modeling.
This agent is responsible for constructing comprehensive financial models
based on research data and financial information from various sources.
"""

import logging
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime
import random
import math
import re
from textwrap import dedent

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

class AnalysisAgent(Agent):
    """
    Agent specializing in financial analysis and model construction.
    
    This agent builds comprehensive financial models by analyzing research data
    and integrating financial information from various sources.
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        tools: Optional[List[Union[ToolSpec, callable]]] = None,
        **kwargs: Any,
    ):
        """Initialize the analysis agent with necessary tools and models."""
        _model = model or get_llm_model()
        _tools = tools or [
            # Add specialized financial analysis tools here if needed
        ]
        
        super().__init__(
            model=_model,
            tools=_tools,
            name="FinancialAnalyst",
            description="Expert AI agent specialized in financial modeling and investment analysis across various asset classes.",
            instructions=dedent("""\
                You are a financial modeling expert with deep expertise in various investment types.
                
                When analyzing investments:
                1. Adapt your analysis approach based on the investment type
                2. Consider the stage, industry, and unique characteristics of the investment
                3. Use appropriate financial metrics and benchmarks for each investment type
                4. Provide realistic financial projections based on industry standards
                5. Support your recommendations with data and logical reasoning
                
                For startups and early-stage businesses, focus on:
                - Customer acquisition dynamics, growth rates, and unit economics
                - Realistic CAC, LTV, churn rates based on stage and business model
                
                For established businesses, focus on:
                - Historical performance analysis and growth trajectories
                - Industry-specific margins and operational metrics
                
                For real estate investments, focus on:
                - Rental yields, occupancy rates, and property appreciation
                - Operating expense ratios and financing structures
                
                For tokenized assets, focus on:
                - Token economics, adoption metrics, and liquidity measures
                - Governance structures and value creation mechanisms
            """),
            add_datetime_to_instructions=True,
            show_tool_calls=kwargs.pop('show_tool_calls', True),
            markdown=kwargs.pop('markdown', True),
            **kwargs,
        )
        
        logger.info("Initialized Analysis Agent with model and tools")
        
        # Load any additional resources needed for financial modeling
        # (e.g., financial ratios, benchmarks, etc.)
        self.investment_type_benchmarks = {
            "saas": {
                "gross_margin": 0.7,
                "churn_rate": 0.05,
                "cac_ltv_ratio_target": 3.0
            },
            "real_estate": {
                "cap_rate": 0.06,
                "occupancy_rate": 0.92,
                "operating_expense_ratio": 0.4
            },
            "tokenized_asset": {
                "token_velocity": 4.0,  # Annual
                "platform_fee": 0.025,
                "user_growth_rate": 0.5  # Annual
            }
        }
    
    async def build_model(
        self,
        research_results: Dict[str, Any],
        financial_data_sources: Optional[Dict[str, Any]] = None,
        plaid_access_token: Optional[str] = None,
        timeframe_years: int = 5
    ) -> Dict[str, Any]:
        """
        Build a comprehensive financial model based on research and financial data.
        
        Args:
            research_results: Deep research findings about the business and market
            financial_data_sources: Information about connected financial data sources
            plaid_access_token: Token for accessing Plaid API if available
            timeframe_years: Number of years to project in the financial model
            
        Returns:
            Complete financial model with projections and analysis
        """
        logger.info("Starting financial model construction")
        
        # Extract key information from research results
        business_profile = research_results["business_profile"]
        market_analysis = research_results["market_analysis"]
        kpis = research_results["key_performance_indicators"]
        revenue_model = research_results["recommended_revenue_models"]["primary_recommendation"]
        
        # Extract investment type for use throughout the model
        investment_type = business_profile.get("investment_type", "business")
        
        # In production, we would connect to real data sources
        # If Plaid token is provided, fetch real financial data
        financial_data = await self._fetch_financial_data(plaid_access_token, financial_data_sources)
        
        # Identify starting metrics for the projections
        starting_metrics = await self._determine_starting_metrics(
            business_profile,
            financial_data,
            revenue_model
        )
        
        # Build the financial projections
        revenue_projections = await self._project_revenue(
            starting_metrics,
            revenue_model,
            market_analysis,
            timeframe_years,
            investment_type
        )
        
        expense_projections = await self._project_expenses(
            starting_metrics,
            revenue_projections,
            timeframe_years,
            investment_type
        )
        
        # Calculate key financial statements
        income_statement = self._generate_income_statement(
            revenue_projections,
            expense_projections,
            timeframe_years,
            investment_type
        )
        
        cash_flow = self._generate_cash_flow_statement(
            income_statement,
            starting_metrics,
            timeframe_years,
            investment_type
        )
        
        balance_sheet = self._generate_balance_sheet(
            income_statement,
            cash_flow,
            starting_metrics,
            timeframe_years,
            investment_type
        )
        
        # Calculate key financial metrics
        financial_metrics = self._calculate_financial_metrics(
            income_statement,
            cash_flow,
            balance_sheet,
            kpis["financial_kpis"],
            investment_type
        )
        
        # Perform scenario analysis
        scenarios = self._perform_scenario_analysis(
            revenue_projections,
            expense_projections,
            market_analysis,
            timeframe_years,
            investment_type
        )
        
        # Combine all elements into the final financial model
        financial_model = {
            "model_type": revenue_model["model"],
            "investment_type": investment_type,
            "timeframe_years": timeframe_years,
            "currency": "USD",  # Would be configurable in production
            "starting_metrics": starting_metrics,
            "revenue_projections": revenue_projections,
            "expense_projections": expense_projections,
            "financial_statements": {
                "income_statement": income_statement,
                "cash_flow": cash_flow,
                "balance_sheet": balance_sheet
            },
            "key_financial_metrics": financial_metrics,
            "scenarios": scenarios,
            "model_assumptions": {
                "market_growth_rate": market_analysis["growth_rate"],
                "customer_acquisition_rate": starting_metrics.get("customer_acquisition_rate"),
                "churn_rate": starting_metrics.get("churn_rate"),
                "expense_growth_rate": "3.5% annually"  # Would be variable in production
            },
            "model_timestamp": datetime.now().isoformat()
        }
        
        logger.info("Completed financial model construction")
        return financial_model
    
    def generate_recommendations(
        self,
        research_results: Dict[str, Any],
        financial_model: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate business recommendations based on research and financial model.
        
        Args:
            research_results: Deep research findings
            financial_model: Constructed financial model
            
        Returns:
            List of strategic recommendations with supporting data
        """
        logger.info("Generating strategic recommendations")
        
        # Prepare context for the LLM to generate recommendations
        investment_type = financial_model.get("investment_type", "business")
        investment_stage = research_results.get("business_profile", {}).get("stage", "growth")
        model_type = financial_model.get("model_type", "generic")
        
        # Extract key financial metrics
        metrics = financial_model.get("key_financial_metrics", {})
        
        # Prepare prompt for LLM to generate recommendations
        prompt = f"""
        Based on the following information about the {investment_type} investment opportunity, 
        generate 3-5 strategic recommendations with supporting metrics:
        
        Investment Type: {investment_type}
        Stage: {investment_stage}
        Revenue Model: {model_type}
        
        Key Financial Metrics:
        """
        
        # Add metrics to the prompt
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                prompt += f"- {key.upper()}: {value}\n"
            elif isinstance(value, dict):
                prompt += f"- {key.upper()}: {str(value)}\n"
        
        # Add research insights to the prompt
        prompt += "\nKey Research Insights:\n"
        if "market_analysis" in research_results:
            prompt += f"- Market Growth Rate: {research_results['market_analysis'].get('growth_rate', 'Unknown')}\n"
            prompt += f"- Market Size: {research_results['market_analysis'].get('market_size', 'Unknown')}\n"
        
        prompt += "\nFor each recommendation, please provide:\n"
        prompt += "1. A clear title\n"
        prompt += "2. A detailed description\n"
        prompt += "3. The expected impact (quantified if possible)\n"
        prompt += "4. Implementation difficulty (low, medium, high)\n"
        prompt += "5. Supporting metrics with specific numbers\n"
        
        # Different prompts based on investment type
        if investment_type.lower() in ["startup", "early stage", "seed"]:
            prompt += "\nFocus on growth, product-market fit, and extending runway.\n"
        elif investment_type.lower() in ["real estate", "reit"]:
            prompt += "\nFocus on occupancy rates, rental yield, and property appreciation.\n"
        elif investment_type.lower() in ["tokenized asset", "digital asset"]:
            prompt += "\nFocus on token economics, liquidity, and market adoption.\n"
        elif investment_type.lower() in ["private credit", "debt"]:
            prompt += "\nFocus on risk mitigation, interest coverage, and default rates.\n"
        
        # Call the LLM to generate recommendations if available
        if self.has_models:
            try:
                recommendations_text = self.reasoning_model.generate(prompt, system_prompt=self.system_prompt)
                return self._parse_recommendations(recommendations_text)
            except Exception as e:
                logger.error(f"Error generating recommendations with LLM: {e}")
                logger.info("Falling back to generic recommendations")
                
        # If LLM is not available or fails, use a simpler approach with the general model
        try:
            if self.has_models:
                recommendations_text = self.general_model.generate(prompt, system_prompt=self.system_prompt)
                return self._parse_recommendations(recommendations_text)
        except Exception as e:
            logger.error(f"Error generating recommendations with fallback model: {e}")
            logger.info("Using default recommendations")
        
        # If all else fails, use simple defaults based on investment type
        return self._generate_default_recommendations(investment_type, metrics)
    
    def _generate_default_recommendations(self, investment_type: str, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic default recommendations when LLM is unavailable."""
        logger.info(f"Generating default recommendations for {investment_type}")
        
        if investment_type.lower() in ["startup", "business", "saas"]:
            return [
                {
                    "title": "Optimize Customer Acquisition Strategy",
                    "description": "Current CAC is too high relative to CLV, suggesting a need to refine acquisition channels.",
                    "expected_impact": "25% reduction in CAC within 6 months",
                    "implementation_difficulty": "medium",
                    "supporting_metrics": {
                        "current_cac": metrics.get("cac", 800),
                        "target_cac": metrics.get("cac", 800) * 0.75,
                        "current_clv": metrics.get("clv", 3500)
                    }
                },
                {
                    "title": "Introduce Tiered Pricing Strategy",
                    "description": "Implement 3-tier pricing to capture different market segments and increase average revenue per user.",
                    "expected_impact": "15-20% increase in revenue within first year",
                    "implementation_difficulty": "low",
                    "supporting_metrics": {
                        "current_arpu": metrics.get("arpu", 50),
                        "projected_arpu_increase": "15-20%",
                        "estimated_implementation_cost": "$5,000-$10,000"
                    }
                }
            ]
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            return [
                {
                    "title": "Diversify Property Portfolio",
                    "description": "The current portfolio is heavily weighted towards residential properties. Adding commercial properties would reduce risk exposure.",
                    "expected_impact": "15% increase in total yield with 20% reduction in volatility",
                    "implementation_difficulty": "medium",
                    "supporting_metrics": {
                        "current_portfolio_composition": "80% residential, 20% commercial",
                        "target_composition": "60% residential, 40% commercial"
                    }
                }
            ]
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            return [
                {
                    "title": "Enhance Token Utility",
                    "description": "Add additional use cases for the token to increase holder value and drive adoption.",
                    "expected_impact": "40% increase in token velocity, 25% growth in holder base",
                    "implementation_difficulty": "medium",
                    "supporting_metrics": {
                        "current_token_utility": "Single use case (ownership)",
                        "proposed_utilities": "Governance, revenue sharing, special access"
                    }
                }
            ]
        else:
            return [
                {
                    "title": "Optimize Cost Structure",
                    "description": "Analysis shows opportunities to streamline operations and reduce unnecessary costs.",
                    "expected_impact": "15% reduction in operating expenses within 1 year",
                    "implementation_difficulty": "medium",
                    "supporting_metrics": {
                        "current_expense_ratio": metrics.get("expense_ratio", 0.6),
                        "target_expense_ratio": metrics.get("expense_ratio", 0.6) * 0.85
                    }
                }
            ]
    
    # Add a helper method to parse LLM-generated recommendations
    def _parse_recommendations(self, recommendations_text: str) -> List[Dict[str, Any]]:
        """
        Parse recommendations from LLM response into structured format.
        
        Args:
            recommendations_text: Raw text response from LLM
            
        Returns:
            Structured list of recommendation objects
        """
        # This would need to be implemented to parse the LLM's response
        # Example implementation that could be expanded:
        recommendations = []
        
        # Split by recommendation (assuming the LLM uses "Recommendation: " as a delimiter)
        raw_recommendations = recommendations_text.split("Recommendation:")
        
        for i, raw_rec in enumerate(raw_recommendations[1:]):  # Skip the first split which is before first recommendation
            try:
                lines = raw_rec.strip().split("\n")
                title = lines[0].strip()
                
                # Extract description (assuming it comes after the title)
                description = ""
                for line in lines[1:]:
                    if line.lower().startswith(("expected impact:", "implementation difficulty:", "supporting metrics:")):
                        break
                    description += line + " "
                description = description.strip()
                
                # Extract expected impact
                expected_impact = ""
                for line in lines:
                    if line.lower().startswith("expected impact:"):
                        expected_impact = line.replace("Expected Impact:", "").replace("expected impact:", "").strip()
                        break
                
                # Extract implementation difficulty
                difficulty = "medium"  # default
                for line in lines:
                    if line.lower().startswith("implementation difficulty:"):
                        difficulty_text = line.replace("Implementation Difficulty:", "").replace("implementation difficulty:", "").strip().lower()
                        if difficulty_text in ["low", "medium", "high"]:
                            difficulty = difficulty_text
                        break
                
                # For supporting metrics, we'd need a more sophisticated parser
                # This is a simplified version
                supporting_metrics = {}
                metrics_section = False
                for line in lines:
                    if line.lower().startswith("supporting metrics:"):
                        metrics_section = True
                        continue
                    if metrics_section and line.strip() and ":" in line:
                        key, value = line.split(":", 1)
                        supporting_metrics[key.strip().lower().replace(" ", "_")] = value.strip()
                
                recommendations.append({
                    "title": title,
                    "description": description,
                    "expected_impact": expected_impact,
                    "implementation_difficulty": difficulty,
                    "supporting_metrics": supporting_metrics
                })
            except Exception as e:
                logger.error(f"Error parsing recommendation {i+1}: {e}")
                # Skip this recommendation if parsing fails
                continue
        
        return recommendations
    
    async def _fetch_financial_data(
        self,
        plaid_access_token: Optional[str],
        financial_data_sources: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fetch financial data from connected sources like Plaid or bookkeeping software.
        
        In production, this would connect to Plaid API and other financial data sources.
        For this demonstration, we'll use simulated data.
        """
        logger.info("Fetching financial data from connected sources")
        
        # Simulate a delay that would occur when fetching real financial data
        await asyncio.sleep(0.5)
        
        # In production: if plaid_access_token:
        #     plaid_data = await plaid_connector.fetch_transactions(plaid_access_token)
        #     plaid_balance = await plaid_connector.fetch_balance(plaid_access_token)
        
        # Simulated financial data
        return {
            "current_cash_balance": 250000,
            "monthly_revenue": 42000,
            "monthly_expenses": 35000,
            "avg_customer_value": 1200,
            "active_customers": 35,
            "customer_acquisition_cost": 800,
            "operating_costs": {
                "salaries": 20000,
                "software": 3000,
                "marketing": 5000,
                "office": 2000,
                "other": 5000
            },
            "assets": {
                "cash": 250000,
                "accounts_receivable": 15000,
                "equipment": 50000
            },
            "liabilities": {
                "accounts_payable": 10000,
                "loans": 100000
            }
        }
    
    async def _determine_starting_metrics(
        self,
        business_profile: Dict[str, Any],
        financial_data: Dict[str, Any],
        revenue_model: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine starting metrics for financial projections."""
        logger.info("Determining starting metrics for projections")
        
        # Extract key information for the LLM
        investment_type = business_profile.get("investment_type", "business")
        investment_stage = business_profile.get("stage", "growth")
        revenue_model_type = revenue_model.get("model", "subscription")
        
        # Check if we have existing financial data or need to estimate
        has_existing_financials = bool(financial_data) and len(financial_data) > 1
        
        # Prepare a prompt for the LLM to determine appropriate starting metrics
        prompt = f"""
        Determine appropriate starting metrics for financial projections based on the following information:
        
        Investment Type: {investment_type}
        Stage: {investment_stage}
        Revenue Model: {revenue_model_type}
        
        """
        
        # Add existing financial data if available
        if has_existing_financials:
            prompt += "Existing Financial Data:\n"
            for key, value in financial_data.items():
                if key not in ["has_existing_financials"] and not isinstance(value, dict):
                    prompt += f"- {key}: {value}\n"
                elif isinstance(value, dict):
                    prompt += f"- {key}:\n"
                    for subkey, subvalue in value.items():
                        prompt += f"  - {subkey}: {subvalue}\n"
            
            prompt += "\nBased on this existing financial data, determine appropriate starting metrics for projections."
            prompt += "\nUse the provided values where available, and estimate where necessary."
        else:
            prompt += "No existing financial data is available. Please estimate appropriate starting metrics based on:"
            prompt += f"\n- Industry benchmarks for {investment_type} at {investment_stage} stage"
            prompt += f"\n- Typical metrics for {revenue_model_type} revenue model"
            prompt += "\n- Market conditions and competitive landscape"
        
        # Customize prompt based on investment type
        if investment_type.lower() in ["startup", "early stage", "seed"]:
            prompt += "\n\nFor a startup, consider typical customer acquisition rates, churn rates, and CAC benchmarks."
            prompt += "\nEstimate realistic initial customer counts and growth rates."
        elif investment_type.lower() in ["real estate", "reit"]:
            prompt += "\n\nFor real estate investments, consider typical occupancy rates, rental yields, and property appreciation rates."
            prompt += "\nEstimate realistic vacancy rates and operating expense ratios."
        elif investment_type.lower() in ["tokenized asset", "digital asset"]:
            prompt += "\n\nFor tokenized assets, consider token supply, initial pricing, liquidity metrics, and adoption rates."
            prompt += "\nEstimate realistic token velocity and holder growth rates."
        elif investment_type.lower() in ["private credit", "debt"]:
            prompt += "\n\nFor debt investments, consider interest rates, default risks, and recovery rates."
            prompt += "\nEstimate realistic origination volumes and servicing costs."
        
        prompt += "\n\nPlease provide the following metrics (with values):"
        
        if investment_type.lower() in ["startup", "business", "saas"]:
            prompt += """
            - initial_customers: Number of customers at the start of projections
            - churn_rate: Monthly customer churn rate (as a decimal)
            - customer_acquisition_rate: Monthly growth rate of new customers (as a decimal)
            - average_revenue_per_customer: Monthly revenue per customer
            - gross_margin: Gross margin percentage (as a decimal)
            - operating_expenses: Monthly operating expenses
            - customer_acquisition_cost: Average cost to acquire a new customer
            - starting_cash: Initial cash balance
            """
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            prompt += """
            - initial_properties: Number of properties in portfolio
            - occupancy_rate: Current occupancy rate (as a decimal)
            - average_rental_yield: Annual rental yield (as a decimal)
            - property_appreciation_rate: Annual property value growth rate (as a decimal)
            - operating_expense_ratio: Operating expenses as percentage of revenue (as a decimal)
            - property_acquisition_cost: Average cost to acquire new properties
            - starting_cash: Initial cash balance
            - loan_to_value_ratio: Debt as percentage of property value (as a decimal)
            """
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            prompt += """
            - initial_token_supply: Number of tokens at launch
            - initial_token_price: Starting price per token
            - token_issuance_rate: New tokens issued per month (as a decimal)
            - token_adoption_rate: Monthly growth in token holders (as a decimal)
            - platform_fee_rate: Fees collected per transaction (as a decimal)
            - operating_expenses: Monthly platform operating expenses
            - marketing_cost_per_user: Cost to acquire a new token holder
            - starting_treasury: Initial treasury balance
            """
        else:
            # Generic metrics for other investment types
            prompt += """
            - initial_revenue: Monthly revenue at start of projections
            - revenue_growth_rate: Monthly revenue growth rate (as a decimal)
            - gross_margin: Gross margin percentage (as a decimal)
            - operating_expenses: Monthly operating expenses
            - marketing_expenses: Monthly marketing expenses
            - starting_cash: Initial cash balance
            """
        
        # Call the LLM to determine the starting metrics if available
        if self.has_models:
            try:
                metrics_text = self.reasoning_model.generate(prompt, system_prompt=self.system_prompt)
                starting_metrics = self._parse_starting_metrics(metrics_text)
                
                if starting_metrics and len(starting_metrics) > 3:  # Ensure we have a reasonable response
                    logger.info(f"Successfully generated {len(starting_metrics)} starting metrics using LLM")
                    return starting_metrics
            except Exception as e:
                logger.error(f"Error generating starting metrics with LLM: {e}")
                logger.info("Falling back to simplified approach")
                
            # Try with general model if reasoning model fails
            try:
                metrics_text = self.general_model.generate(prompt, system_prompt=self.system_prompt)
                starting_metrics = self._parse_starting_metrics(metrics_text)
                
                if starting_metrics and len(starting_metrics) > 3:
                    logger.info(f"Successfully generated {len(starting_metrics)} starting metrics using fallback model")
                    return starting_metrics
            except Exception as e:
                logger.error(f"Error generating starting metrics with fallback model: {e}")
                logger.info("Using default metrics")
        
        # If LLM is not available or fails, use reasonable defaults based on investment type
        logger.info(f"Using default starting metrics for {investment_type}")
        return self._get_default_starting_metrics(investment_type, financial_data)
    
    def _get_default_starting_metrics(
        self,
        investment_type: str,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get default starting metrics when LLM generation fails."""
        # Use the financial data as a basis when available, otherwise use reasonable defaults
        if investment_type.lower() in ["startup", "business", "saas"]:
            return {
                "initial_customers": financial_data.get("active_customers", 30),
                "churn_rate": 0.05,  # 5% monthly churn
                "customer_acquisition_rate": 0.15,  # 15% monthly growth in new customers
                "average_revenue_per_customer": financial_data.get("avg_customer_value", 1000),
                "gross_margin": 0.7,  # 70% gross margin
                "operating_expenses": sum(financial_data.get("operating_costs", {}).values()) if isinstance(financial_data.get("operating_costs"), dict) else 20000,
                "customer_acquisition_cost": financial_data.get("customer_acquisition_cost", 750),
                "starting_cash": financial_data.get("current_cash_balance", 200000)
            }
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            return {
                "initial_properties": 10,
                "occupancy_rate": 0.92,  # 92% occupancy
                "average_rental_yield": 0.065,  # 6.5% annual yield
                "property_appreciation_rate": 0.035,  # 3.5% annual appreciation
                "operating_expense_ratio": 0.4,  # 40% of revenue
                "property_acquisition_cost": 1000000,  # $1M per property
                "starting_cash": financial_data.get("current_cash_balance", 2000000),
                "loan_to_value_ratio": 0.6  # 60% LTV
            }
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            return {
                "initial_token_supply": 10000000,
                "initial_token_price": 1.00,
                "token_issuance_rate": 0.01,  # 1% monthly
                "token_adoption_rate": 0.08,  # 8% monthly
                "platform_fee_rate": 0.025,  # 2.5% fee
                "operating_expenses": 35000,  # $35K monthly
                "marketing_cost_per_user": 5,  # $5 per user
                "starting_treasury": financial_data.get("current_cash_balance", 1000000)
            }
        else:
            # Generic metrics for other investment types
            monthly_revenue = financial_data.get("monthly_revenue", 50000)
            return {
                "initial_revenue": monthly_revenue,
                "revenue_growth_rate": 0.05,  # 5% monthly
                "gross_margin": 0.6,  # 60% margin
                "operating_expenses": financial_data.get("monthly_expenses", monthly_revenue * 0.8),
                "marketing_expenses": financial_data.get("marketing_expenses", monthly_revenue * 0.2),
                "starting_cash": financial_data.get("current_cash_balance", 500000)
            }
    
    def _parse_starting_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """
        Parse starting metrics from LLM response.
        
        Args:
            metrics_text: Raw text response from LLM containing metrics
            
        Returns:
            Dictionary of parsed metrics with appropriate data types
        """
        metrics = {}
        
        # Simple parsing logic - in production this would be more robust
        lines = metrics_text.strip().split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_").replace("-", "_")
                
                try:
                    # Try to convert to appropriate data type
                    value = value.strip()
                    if "%" in value:
                        # Convert percentage to decimal
                        metrics[key] = float(value.replace("%", "")) / 100
                    elif "$" in value:
                        # Remove currency symbol and any commas
                        metrics[key] = float(value.replace("$", "").replace(",", ""))
                    elif value.replace(".", "").isdigit():
                        # It's a number
                        if "." in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    else:
                        # Keep as string
                        metrics[key] = value
                except ValueError:
                    # If conversion fails, keep as string
                    metrics[key] = value.strip()
        
        return metrics
    
    async def _project_revenue(
        self,
        starting_metrics: Dict[str, Any],
        revenue_model: Dict[str, Any],
        market_analysis: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Project revenue over the specified timeframe."""
        logger.info("Projecting revenue streams")
        
        # Extract growth rate from market analysis (convert from string to number if needed)
        growth_rate = market_analysis.get("growth_rate")
        if isinstance(growth_rate, str) and "CAGR" in growth_rate:
            try:
                growth_rate = float(growth_rate.replace("% CAGR", "")) / 100
            except ValueError:
                growth_rate = 0.05  # Default to 5% if parsing fails
        elif not isinstance(growth_rate, (int, float)):
            growth_rate = 0.05  # Default value
            
        # Generate monthly projections for the specified timeframe
        months = timeframe_years * 12
        
        # Different projection logic based on investment type
        if investment_type.lower() in ["startup", "business", "saas"]:
            # Use subscription/customer-based model
            return self._project_subscription_revenue(starting_metrics, revenue_model, growth_rate, months)
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            # Use property/rental-based model
            return self._project_real_estate_revenue(starting_metrics, revenue_model, growth_rate, months)
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            # Use token-based model
            return self._project_tokenized_asset_revenue(starting_metrics, revenue_model, growth_rate, months)
        else:
            # Default to generic revenue projection
            return self._project_generic_revenue(starting_metrics, revenue_model, growth_rate, months)
    
    def _project_subscription_revenue(
        self,
        starting_metrics: Dict[str, Any],
        revenue_model: Dict[str, Any],
        growth_rate: float,
        months: int
    ) -> Dict[str, Any]:
        """Project revenue for subscription-based businesses."""
        # Initialize variables for projection
        initial_customers = starting_metrics.get("initial_customers", 100)
        churn_rate = starting_metrics.get("churn_rate", 0.05)
        acquisition_rate = starting_metrics.get("customer_acquisition_rate", 0.15)
        arpu = starting_metrics.get("average_revenue_per_customer", 50)
        
        # Prepare arrays to store projection data
        customers = [initial_customers]
        new_customers = []
        churned_customers = []
        revenue = []
        
        for month in range(1, months + 1):
            # Calculate new customers (with slight randomness for realism)
            random_factor = 0.9 + 0.2 * random.random()  # 0.9 to 1.1
            new_customer_count = max(5, int(customers[-1] * acquisition_rate * random_factor))
            new_customers.append(new_customer_count)
            
            # Calculate churned customers (with slight randomness for realism)
            random_factor = 0.9 + 0.2 * random.random()  # 0.9 to 1.1
            churned_customer_count = int(customers[-1] * churn_rate * random_factor)
            churned_customers.append(churned_customer_count)
            
            # Calculate end-of-month customer count
            end_month_customers = customers[-1] + new_customer_count - churned_customer_count
            customers.append(end_month_customers)
            
            # Calculate monthly revenue
            # Adjust ARPU over time to account for expansion revenue and price changes
            current_arpu = arpu * (1 + 0.003 * month)  # Small monthly increase
            monthly_revenue = end_month_customers * current_arpu
            revenue.append(monthly_revenue)
        
        # Remove the initial customer count (it was just a starting point)
        customers.pop(0)
        
        # Aggregate into quarterly and annual data
        quarterly_revenue = [sum(revenue[i:i+3]) for i in range(0, len(revenue), 3)]
        annual_revenue = [sum(revenue[i:i+12]) for i in range(0, len(revenue), 12)]
        
        revenue_projections = {
            "monthly": {
                "customers": customers,
                "new_customers": new_customers,
                "churned_customers": churned_customers,
                "revenue": revenue
            },
            "quarterly": {
                "revenue": quarterly_revenue
            },
            "annual": {
                "revenue": annual_revenue
            }
        }
        
        return revenue_projections
    
    def _project_real_estate_revenue(
        self,
        starting_metrics: Dict[str, Any],
        revenue_model: Dict[str, Any],
        growth_rate: float,
        months: int
    ) -> Dict[str, Any]:
        """Project revenue for real estate investments."""
        # Initialize variables for projection
        initial_properties = starting_metrics.get("initial_properties", 10)
        occupancy_rate = starting_metrics.get("occupancy_rate", 0.92)
        avg_rental_yield = starting_metrics.get("average_rental_yield", 0.06)
        property_growth_rate = starting_metrics.get("property_acquisition_rate", 0.02)  # Monthly growth in properties
        property_value = starting_metrics.get("average_property_value", 1000000)
        rental_growth_rate = starting_metrics.get("rental_growth_rate", 0.003)  # Monthly rental price growth
        
        # Prepare arrays to store projection data
        properties = []
        occupancy = []
        rental_revenue = []
        property_value_revenue = []  # For property appreciation
        total_revenue = []
        
        current_properties = initial_properties
        current_property_value = property_value
        current_rental_rate = (avg_rental_yield / 12) * property_value  # Monthly rental per property
        
        for month in range(1, months + 1):
            # Calculate property growth (with slight randomness)
            random_factor = 0.9 + 0.2 * random.random()
            new_properties = max(0, current_properties * property_growth_rate * random_factor)
            current_properties += new_properties
            properties.append(current_properties)
            
            # Calculate occupancy (with seasonal fluctuations)
            season_factor = 1 + 0.02 * math.sin(month * math.pi / 6)  # Seasonal variation
            current_occupancy = min(0.99, occupancy_rate * season_factor)
            occupancy.append(current_occupancy)
            
            # Increase rental rates over time
            current_rental_rate *= (1 + rental_growth_rate)
            
            # Calculate monthly rental revenue
            monthly_rental = current_properties * current_occupancy * current_rental_rate
            rental_revenue.append(monthly_rental)
            
            # Calculate property appreciation (assuming annual appreciation spread monthly)
            # Only count this as "revenue" if the model includes capital gains
            property_appreciation_rate = starting_metrics.get("property_appreciation_rate", 0.035) / 12
            current_property_value *= (1 + property_appreciation_rate)
            monthly_appreciation = current_properties * current_property_value * property_appreciation_rate
            property_value_revenue.append(monthly_appreciation)
            
            # Total revenue (rental + appreciation if included)
            include_appreciation = revenue_model.get("include_appreciation", False)
            monthly_total = monthly_rental + (monthly_appreciation if include_appreciation else 0)
            total_revenue.append(monthly_total)
        
        # Aggregate into quarterly and annual data
        quarterly_revenue = [sum(total_revenue[i:i+3]) for i in range(0, len(total_revenue), 3)]
        annual_revenue = [sum(total_revenue[i:i+12]) for i in range(0, len(total_revenue), 12)]
        
        revenue_projections = {
            "monthly": {
                "properties": properties,
                "occupancy": occupancy,
                "rental_revenue": rental_revenue,
                "property_value_revenue": property_value_revenue,
                "revenue": total_revenue
            },
            "quarterly": {
                "revenue": quarterly_revenue
            },
            "annual": {
                "revenue": annual_revenue
            }
        }
        
        return revenue_projections
    
    def _project_tokenized_asset_revenue(
        self,
        starting_metrics: Dict[str, Any],
        revenue_model: Dict[str, Any],
        growth_rate: float,
        months: int
    ) -> Dict[str, Any]:
        """Project revenue for tokenized asset investments."""
        # Initialize variables for projection
        initial_token_supply = starting_metrics.get("initial_token_supply", 10000000)
        initial_token_price = starting_metrics.get("initial_token_price", 1.00)
        token_issuance_rate = starting_metrics.get("token_issuance_rate", 0.01)
        token_adoption_rate = starting_metrics.get("token_adoption_rate", 0.08)
        platform_fee_rate = starting_metrics.get("platform_fee_rate", 0.025)
        initial_holders = starting_metrics.get("initial_token_holders", 1000)
        initial_transaction_volume = starting_metrics.get("initial_transaction_volume", initial_token_supply * initial_token_price * 0.05)
        
        # Prepare arrays to store projection data
        token_supply = [initial_token_supply]
        token_price = [initial_token_price]
        token_holders = [initial_holders]
        transaction_volume = [initial_transaction_volume]
        fee_revenue = []
        appreciation_revenue = []
        total_revenue = []
        
        for month in range(1, months + 1):
            # Calculate token supply growth
            new_tokens = token_supply[-1] * token_issuance_rate
            current_supply = token_supply[-1] + new_tokens
            token_supply.append(current_supply)
            
            # Calculate token holder growth (with randomness)
            random_factor = 0.9 + 0.2 * random.random()
            new_holders = token_holders[-1] * token_adoption_rate * random_factor
            current_holders = token_holders[-1] + new_holders
            token_holders.append(current_holders)
            
            # Calculate token price change (based on adoption and market conditions)
            # Simple model: price grows with holder growth but is diluted by token issuance
            price_growth_factor = (1 + token_adoption_rate) / (1 + token_issuance_rate)
            price_volatility = 0.1  # 10% monthly volatility
            random_price_factor = 1 + (random.random() - 0.5) * price_volatility
            current_price = token_price[-1] * price_growth_factor * random_price_factor
            token_price.append(current_price)
            
            # Calculate transaction volume (as a percentage of market cap with growth)
            market_cap = current_supply * current_price
            velocity_factor = 0.05 * (1 + 0.01 * month)  # Increasing velocity over time
            current_volume = market_cap * velocity_factor
            transaction_volume.append(current_volume)
            
            # Calculate fee revenue
            monthly_fees = current_volume * platform_fee_rate
            fee_revenue.append(monthly_fees)
            
            # Calculate appreciation revenue (if token is held by the platform)
            platform_token_holdings = starting_metrics.get("platform_token_holdings", initial_token_supply * 0.2)
            monthly_appreciation = platform_token_holdings * (current_price - token_price[-2]) / token_price[-2]
            appreciation_revenue.append(monthly_appreciation)
            
            # Total revenue calculation depends on revenue model
            include_appreciation = revenue_model.get("include_appreciation", False)
            monthly_total = monthly_fees + (monthly_appreciation if include_appreciation else 0)
            total_revenue.append(monthly_total)
        
        # Aggregate into quarterly and annual data
        quarterly_revenue = [sum(total_revenue[i:i+3]) for i in range(0, len(total_revenue), 3)]
        annual_revenue = [sum(total_revenue[i:i+12]) for i in range(0, len(total_revenue), 12)]
        
        revenue_projections = {
            "monthly": {
                "token_supply": token_supply[1:],  # Remove initial value
                "token_price": token_price[1:],    # Remove initial value
                "token_holders": token_holders[1:],  # Remove initial value
                "transaction_volume": transaction_volume[1:],  # Remove initial value
                "fee_revenue": fee_revenue,
                "appreciation_revenue": appreciation_revenue,
                "revenue": total_revenue
            },
            "quarterly": {
                "revenue": quarterly_revenue
            },
            "annual": {
                "revenue": annual_revenue
            }
        }
        
        return revenue_projections
    
    def _project_generic_revenue(
        self,
        starting_metrics: Dict[str, Any],
        revenue_model: Dict[str, Any],
        growth_rate: float,
        months: int
    ) -> Dict[str, Any]:
        """Project revenue for generic business models."""
        # Initialize variables for projection
        initial_revenue = starting_metrics.get("initial_revenue", 50000)
        revenue_growth_rate = starting_metrics.get("revenue_growth_rate", 0.05)
        
        # Prepare arrays to store projection data
        revenue = []
        
        current_revenue = initial_revenue
        
        for month in range(1, months + 1):
            # Add seasonal variation (if applicable)
            month_of_year = ((month - 1) % 12) + 1
            seasonal_factor = 1.0
            
            # Example: retail businesses might have higher revenue in Q4
            if revenue_model.get("has_seasonality", False):
                if month_of_year in [10, 11, 12]:  # Q4
                    seasonal_factor = 1.2
                elif month_of_year in [1, 2]:  # Post-holiday slump
                    seasonal_factor = 0.9
            
            # Add some randomness
            random_factor = 0.95 + 0.1 * random.random()  # 0.95 to 1.05
            
            # Calculate monthly revenue
            monthly_revenue = current_revenue * seasonal_factor * random_factor
            revenue.append(monthly_revenue)
            
            # Update base revenue for next month
            current_revenue = current_revenue * (1 + revenue_growth_rate)
        
        # Aggregate into quarterly and annual data
        quarterly_revenue = [sum(revenue[i:i+3]) for i in range(0, len(revenue), 3)]
        annual_revenue = [sum(revenue[i:i+12]) for i in range(0, len(revenue), 12)]
        
        revenue_projections = {
            "monthly": {
                "revenue": revenue
            },
            "quarterly": {
                "revenue": quarterly_revenue
            },
            "annual": {
                "revenue": annual_revenue
            }
        }
        
        return revenue_projections
    
    async def _project_expenses(
        self,
        starting_metrics: Dict[str, Any],
        revenue_projections: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Project expenses over the specified timeframe."""
        logger.info("Projecting expense streams")
        
        # Different expense projection logic based on investment type
        if investment_type.lower() in ["startup", "business", "saas"]:
            # Use subscription/customer-based expense model
            return self._project_subscription_expenses(starting_metrics, revenue_projections, timeframe_years)
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            # Use property/rental-based expense model
            return self._project_real_estate_expenses(starting_metrics, revenue_projections, timeframe_years)
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            # Use token-based expense model
            return self._project_tokenized_asset_expenses(starting_metrics, revenue_projections, timeframe_years)
        else:
            # Default to generic expense projection
            return self._project_generic_expenses(starting_metrics, revenue_projections, timeframe_years)
    
    def _project_subscription_expenses(
        self,
        starting_metrics: Dict[str, Any],
        revenue_projections: Dict[str, Any],
        timeframe_years: int
    ) -> Dict[str, Any]:
        """Project expenses for subscription-based businesses."""
        # Initialize variables for projection
        cac = starting_metrics.get("customer_acquisition_cost", 800)
        initial_operating_expenses = starting_metrics.get("operating_expenses", 20000)
        gross_margin = starting_metrics.get("gross_margin", 0.7)
        
        # Generate monthly projections
        months = timeframe_years * 12
        
        # Prepare arrays to store projection data
        marketing_expenses = []
        operating_expenses = []
        cogs = []  # Cost of Goods Sold
        total_expenses = []
        
        for month in range(months):
            # Calculate marketing expenses based on new customer acquisition
            monthly_marketing = revenue_projections["monthly"]["new_customers"][month] * cac
            marketing_expenses.append(monthly_marketing)
            
            # Calculate COGS based on revenue and gross margin
            monthly_revenue = revenue_projections["monthly"]["revenue"][month]
            monthly_cogs = monthly_revenue * (1 - gross_margin)
            cogs.append(monthly_cogs)
            
            # Calculate operating expenses (growing slightly over time)
            monthly_opex = initial_operating_expenses * (1 + 0.005 * (month // 3))  # Small quarterly increase
            operating_expenses.append(monthly_opex)
            
            # Calculate total expenses
            total_expenses.append(monthly_marketing + monthly_cogs + monthly_opex)
        
        # Aggregate into quarterly and annual data
        quarterly_expenses = [sum(total_expenses[i:i+3]) for i in range(0, len(total_expenses), 3)]
        annual_expenses = [sum(total_expenses[i:i+12]) for i in range(0, len(total_expenses), 12)]
        
        expense_projections = {
            "monthly": {
                "marketing": marketing_expenses,
                "cogs": cogs,
                "operating": operating_expenses,
                "total": total_expenses
            },
            "quarterly": {
                "total": quarterly_expenses
            },
            "annual": {
                "total": annual_expenses
            }
        }
        
        return expense_projections
    
    def _project_real_estate_expenses(
        self,
        starting_metrics: Dict[str, Any],
        revenue_projections: Dict[str, Any],
        timeframe_years: int
    ) -> Dict[str, Any]:
        """Project expenses for real estate investments."""
        # Initialize variables for projection
        operating_expense_ratio = starting_metrics.get("operating_expense_ratio", 0.4)
        property_acquisition_cost = starting_metrics.get("property_acquisition_cost", 1000000)
        maintenance_reserve_rate = starting_metrics.get("maintenance_reserve_rate", 0.05)  # % of rental income
        property_tax_rate = starting_metrics.get("property_tax_rate", 0.01)  # Annual rate, divided by 12 for monthly
        interest_rate = starting_metrics.get("interest_rate", 0.05)  # Annual rate, divided by 12 for monthly
        loan_to_value_ratio = starting_metrics.get("loan_to_value_ratio", 0.6)
        
        # Generate monthly projections
        months = timeframe_years * 12
        
        # Prepare arrays to store projection data
        operating_expenses = []  # Regular property operating expenses
        maintenance_reserves = []  # Funds set aside for maintenance/capex
        property_taxes = []  # Property tax expenses
        interest_expenses = []  # Interest on property loans
        acquisition_expenses = []  # Expenses for acquiring new properties
        total_expenses = []
        
        # Extract property data from revenue projections
        properties = revenue_projections["monthly"]["properties"]
        rental_revenue = revenue_projections["monthly"]["rental_revenue"]
        
        # Calculate initial loan balance (for existing properties)
        initial_properties = properties[0]
        initial_property_value = property_acquisition_cost * initial_properties
        loan_balance = initial_property_value * loan_to_value_ratio
        
        for month in range(months):
            # Operating expenses (property management, utilities, insurance, etc.)
            monthly_opex = rental_revenue[month] * operating_expense_ratio
            operating_expenses.append(monthly_opex)
            
            # Maintenance reserves
            monthly_maintenance = rental_revenue[month] * maintenance_reserve_rate
            maintenance_reserves.append(monthly_maintenance)
            
            # Property taxes (annual rate divided by 12)
            monthly_property_tax = properties[month] * property_acquisition_cost * (property_tax_rate / 12)
            property_taxes.append(monthly_property_tax)
            
            # Interest expense on property loans
            monthly_interest = loan_balance * (interest_rate / 12)
            interest_expenses.append(monthly_interest)
            
            # New property acquisition costs
            if month > 0:
                new_properties = properties[month] - properties[month-1]
                acquisition_cost = new_properties * property_acquisition_cost
                # Assume only down payment (1 - LTV) is expensed, rest is financed
                acquisition_expense = acquisition_cost * (1 - loan_to_value_ratio)
                # Update loan balance for new properties
                loan_balance += acquisition_cost * loan_to_value_ratio
            else:
                acquisition_expense = 0
            
            acquisition_expenses.append(acquisition_expense)
            
            # Principal payment (simplification - amortize over 30 years = 360 months)
            if loan_balance > 0:
                amortization_period = 360
                principal_payment = loan_balance / amortization_period
                loan_balance -= principal_payment
            else:
                principal_payment = 0
            
            # Calculate total expenses - note we don't include principal payments as expense
            # as they're balance sheet transactions, not income statement
            total_expenses.append(monthly_opex + monthly_maintenance + monthly_property_tax + 
                                monthly_interest + acquisition_expense)
        
        # Aggregate into quarterly and annual data
        quarterly_expenses = [sum(total_expenses[i:i+3]) for i in range(0, len(total_expenses), 3)]
        annual_expenses = [sum(total_expenses[i:i+12]) for i in range(0, len(total_expenses), 12)]
        
        expense_projections = {
            "monthly": {
                "operating": operating_expenses,
                "maintenance": maintenance_reserves,
                "property_taxes": property_taxes,
                "interest": interest_expenses,
                "acquisition": acquisition_expenses,
                "total": total_expenses
            },
            "quarterly": {
                "total": quarterly_expenses
            },
            "annual": {
                "total": annual_expenses
            }
        }
        
        return expense_projections
    
    def _project_tokenized_asset_expenses(
        self,
        starting_metrics: Dict[str, Any],
        revenue_projections: Dict[str, Any],
        timeframe_years: int
    ) -> Dict[str, Any]:
        """Project expenses for tokenized asset investments."""
        # Initialize variables for projection
        operating_expenses = starting_metrics.get("operating_expenses", 35000)
        marketing_cost_per_user = starting_metrics.get("marketing_cost_per_user", 5)
        platform_maintenance_cost = starting_metrics.get("platform_maintenance_cost", 15000)  # Monthly
        compliance_cost = starting_metrics.get("compliance_cost", 10000)  # Monthly
        transaction_cost_ratio = starting_metrics.get("transaction_cost_ratio", 0.005)  # Cost per transaction volume
        
        # Generate monthly projections
        months = timeframe_years * 12
        
        # Prepare arrays to store projection data
        platform_expenses = []  # Development and maintenance costs
        marketing_expenses = []  # User acquisition costs
        compliance_expenses = []  # Regulatory and compliance costs
        transaction_expenses = []  # Costs related to processing transactions
        total_expenses = []
        
        # Extract token data from revenue projections
        token_holders = revenue_projections["monthly"]["token_holders"]
        transaction_volume = revenue_projections["monthly"]["transaction_volume"]
        
        for month in range(months):
            # Calculate platform expenses (growing modestly over time for upgrades)
            monthly_platform = platform_maintenance_cost * (1 + 0.01 * (month // 6))  # Small increase every 6 months
            platform_expenses.append(monthly_platform)
            
            # Calculate marketing expenses based on new user acquisition
            if month > 0:
                new_holders = token_holders[month] - token_holders[month-1]
                monthly_marketing = new_holders * marketing_cost_per_user
            else:
                monthly_marketing = token_holders[0] * marketing_cost_per_user * 0.1  # Only 10% of initial are "new" in first month
            
            marketing_expenses.append(monthly_marketing)
            
            # Calculate compliance costs (growing with user base and transaction volume)
            user_scaling_factor = 1 + 0.1 * (token_holders[month] / token_holders[0] - 1)
            monthly_compliance = compliance_cost * user_scaling_factor
            compliance_expenses.append(monthly_compliance)
            
            # Calculate transaction expenses
            monthly_transaction_expense = transaction_volume[month] * transaction_cost_ratio
            transaction_expenses.append(monthly_transaction_expense)
            
            # Calculate total expenses
            total_expenses.append(monthly_platform + monthly_marketing + 
                                 monthly_compliance + monthly_transaction_expense)
        
        # Aggregate into quarterly and annual data
        quarterly_expenses = [sum(total_expenses[i:i+3]) for i in range(0, len(total_expenses), 3)]
        annual_expenses = [sum(total_expenses[i:i+12]) for i in range(0, len(total_expenses), 12)]
        
        expense_projections = {
            "monthly": {
                "platform": platform_expenses,
                "marketing": marketing_expenses,
                "compliance": compliance_expenses,
                "transaction": transaction_expenses,
                "total": total_expenses
            },
            "quarterly": {
                "total": quarterly_expenses
            },
            "annual": {
                "total": annual_expenses
            }
        }
        
        return expense_projections
    
    def _project_generic_expenses(
        self,
        starting_metrics: Dict[str, Any],
        revenue_projections: Dict[str, Any],
        timeframe_years: int
    ) -> Dict[str, Any]:
        """Project expenses for generic business models."""
        # Initialize variables for projection
        operating_expenses = starting_metrics.get("operating_expenses", 30000)
        marketing_expenses = starting_metrics.get("marketing_expenses", 10000)
        cogs_ratio = 1.0 - starting_metrics.get("gross_margin", 0.6)
        
        # Generate monthly projections
        months = timeframe_years * 12
        
        # Prepare arrays to store projection data
        opex = []
        marketing = []
        cogs = []
        total_expenses = []
        
        # Extract revenue data
        monthly_revenue = revenue_projections["monthly"]["revenue"]
        
        for month in range(months):
            # Operating expenses grow slightly over time
            monthly_opex = operating_expenses * (1 + 0.004 * (month // 3))  # Small quarterly increase
            opex.append(monthly_opex)
            
            # Marketing expenses scale somewhat with revenue
            revenue_factor = monthly_revenue[month] / monthly_revenue[0] if monthly_revenue[0] > 0 else 1
            monthly_marketing = marketing_expenses * (0.7 + 0.3 * revenue_factor)  # Partial scaling
            marketing.append(monthly_marketing)
            
            # COGS is directly tied to revenue
            monthly_cogs = monthly_revenue[month] * cogs_ratio
            cogs.append(monthly_cogs)
            
            # Calculate total expenses
            total_expenses.append(monthly_opex + monthly_marketing + monthly_cogs)
        
        # Aggregate into quarterly and annual data
        quarterly_expenses = [sum(total_expenses[i:i+3]) for i in range(0, len(total_expenses), 3)]
        annual_expenses = [sum(total_expenses[i:i+12]) for i in range(0, len(total_expenses), 12)]
        
        expense_projections = {
            "monthly": {
                "operating": opex,
                "marketing": marketing,
                "cogs": cogs,
                "total": total_expenses
            },
            "quarterly": {
                "total": quarterly_expenses
            },
            "annual": {
                "total": annual_expenses
            }
        }
        
        return expense_projections
    
    def _generate_income_statement(
        self,
        revenue_projections: Dict[str, Any],
        expense_projections: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Generate income statement projections."""
        logger.info("Generating income statement projections")
        
        # Prepare data structures for income statement
        monthly_revenue = revenue_projections["monthly"]["revenue"]
        monthly_cogs = expense_projections["monthly"]["cogs"]
        monthly_opex = expense_projections["monthly"]["operating"]
        monthly_marketing = expense_projections["monthly"]["marketing"]
        
        # Calculate monthly gross profit
        monthly_gross_profit = [r - c for r, c in zip(monthly_revenue, monthly_cogs)]
        
        # Calculate monthly operating income
        monthly_operating_income = [gp - (op + mkt) for gp, op, mkt in 
                                  zip(monthly_gross_profit, monthly_opex, monthly_marketing)]
        
        # Simple tax calculation (30% of operating income if positive)
        monthly_taxes = [max(0, oi * 0.3) for oi in monthly_operating_income]
        
        # Calculate monthly net income
        monthly_net_income = [oi - tax for oi, tax in zip(monthly_operating_income, monthly_taxes)]
        
        # Aggregate to annual
        months = timeframe_years * 12
        annual_data = []
        
        for year in range(timeframe_years):
            start_month = year * 12
            end_month = start_month + 12
            
            annual_data.append({
                "year": year + 1,
                "revenue": sum(monthly_revenue[start_month:end_month]),
                "cogs": sum(monthly_cogs[start_month:end_month]),
                "gross_profit": sum(monthly_gross_profit[start_month:end_month]),
                "operating_expenses": sum(monthly_opex[start_month:end_month]),
                "marketing_expenses": sum(monthly_marketing[start_month:end_month]),
                "operating_income": sum(monthly_operating_income[start_month:end_month]),
                "taxes": sum(monthly_taxes[start_month:end_month]),
                "net_income": sum(monthly_net_income[start_month:end_month])
            })
        
        income_statement = {
            "monthly": {
                "revenue": monthly_revenue,
                "cogs": monthly_cogs,
                "gross_profit": monthly_gross_profit,
                "operating_expenses": monthly_opex,
                "marketing_expenses": monthly_marketing,
                "operating_income": monthly_operating_income,
                "taxes": monthly_taxes,
                "net_income": monthly_net_income
            },
            "annual": annual_data
        }
        
        return income_statement
    
    def _generate_cash_flow_statement(
        self,
        income_statement: Dict[str, Any],
        starting_metrics: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Generate cash flow statement projections."""
        logger.info("Generating cash flow statement projections")
        
        # Prepare data structures for cash flow
        monthly_net_income = income_statement["monthly"]["net_income"]
        starting_cash = starting_metrics["starting_cash"]
        
        # Initialize cash flow variables
        months = timeframe_years * 12
        monthly_cash_flow = []
        monthly_ending_cash = [starting_cash]
        
        # Simplified cash flow calculation
        for month in range(months):
            # Net income is the core of cash flow
            # In a real model, we'd adjust for non-cash expenses like depreciation
            # and changes in working capital
            
            # For simplicity, we'll add a small random adjustment to simulate these effects
            adjustment = random.uniform(-0.1, 0.1) * monthly_net_income[month]
            
            # Calculate cash flow for the month
            cash_flow = monthly_net_income[month] + adjustment
            monthly_cash_flow.append(cash_flow)
            
            # Update ending cash balance
            ending_cash = monthly_ending_cash[-1] + cash_flow
            monthly_ending_cash.append(ending_cash)
        
        # Remove the initial cash balance (it was just a starting point)
        monthly_ending_cash.pop(0)
        
        # Aggregate to annual
        annual_data = []
        
        for year in range(timeframe_years):
            start_month = year * 12
            end_month = start_month + 12
            
            annual_data.append({
                "year": year + 1,
                "net_income": sum(monthly_net_income[start_month:end_month]),
                "cash_flow": sum(monthly_cash_flow[start_month:end_month]),
                "ending_cash": monthly_ending_cash[end_month - 1]  # Last month of the year
            })
        
        cash_flow_statement = {
            "monthly": {
                "net_income": monthly_net_income,
                "cash_flow": monthly_cash_flow,
                "ending_cash": monthly_ending_cash
            },
            "annual": annual_data
        }
        
        return cash_flow_statement
    
    def _generate_balance_sheet(
        self,
        income_statement: Dict[str, Any],
        cash_flow: Dict[str, Any],
        starting_metrics: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Generate balance sheet projections."""
        logger.info("Generating balance sheet projections")
        
        # Prepare data structures for balance sheet
        monthly_ending_cash = cash_flow["monthly"]["ending_cash"]
        
        # For simplicity, we'll create a basic balance sheet with minimal detail
        # In a real model, this would include detailed asset and liability projections
        
        # Initialize variables
        starting_assets = starting_metrics.get("starting_cash", 200000) + 50000  # Cash + Other assets
        starting_liabilities = 100000  # Initial loans/liabilities
        starting_equity = starting_assets - starting_liabilities
        
        # Generate annual balance sheets
        annual_data = []
        
        for year in range(timeframe_years):
            end_month = (year + 1) * 12 - 1  # Last month of the year
            
            # Simple balance sheet calculations
            cash = monthly_ending_cash[end_month]
            
            # For simplicity, other assets grow slightly each year
            other_assets = 50000 * (1 + 0.1 * year)
            
            # Total assets
            total_assets = cash + other_assets
            
            # Liabilities decrease slightly each year (paying down debt)
            liabilities = max(0, starting_liabilities * (1 - 0.1 * year))
            
            # Equity is assets minus liabilities
            equity = total_assets - liabilities
            
            annual_data.append({
                "year": year + 1,
                "assets": {
                    "cash": cash,
                    "other_assets": other_assets,
                    "total_assets": total_assets
                },
                "liabilities": liabilities,
                "equity": equity
            })
        
        balance_sheet = {
            "annual": annual_data
        }
        
        return balance_sheet
    
    def _calculate_financial_metrics(
        self,
        income_statement: Dict[str, Any],
        cash_flow: Dict[str, Any],
        balance_sheet: Dict[str, Any],
        kpis: List[Dict[str, Any]],
        investment_type: str = "business"
    ) -> Dict[str, Any]:
        """Calculate key financial metrics and KPIs."""
        logger.info("Calculating key financial metrics")
        
        # Extract data from financial statements
        annual_income = income_statement["annual"]
        annual_cash_flow = cash_flow["annual"]
        annual_balance = balance_sheet["annual"]
        
        # Calculate metrics for the most recent year
        latest_year = annual_income[-1]
        
        # Extract customer data if available
        monthly_customers = income_statement.get("monthly", {}).get("customers", [0])
        
        # Basic financial metrics
        gross_margin = latest_year["gross_profit"] / latest_year["revenue"] if latest_year["revenue"] > 0 else 0
        net_margin = latest_year["net_income"] / latest_year["revenue"] if latest_year["revenue"] > 0 else 0
        
        # Create basic metrics dictionary with calculated values
        metrics = {
            "gross_margin": gross_margin,
            "net_margin": net_margin
        }
        
        # Try to calculate detailed metrics using LLM
        if self.has_models:
            try:
                # Create a context dictionary with financial data for the LLM
                context = {
                    "latest_year_revenue": latest_year["revenue"],
                    "latest_year_gross_profit": latest_year["gross_profit"],
                    "latest_year_net_income": latest_year["net_income"],
                    "latest_year_cash_flow": annual_cash_flow[-1]["cash_flow"],
                    "latest_year_ending_cash": annual_cash_flow[-1]["ending_cash"],
                    "latest_year_assets": annual_balance[-1]["assets"]["total_assets"],
                    "latest_year_liabilities": annual_balance[-1]["liabilities"],
                    "latest_year_equity": annual_balance[-1]["equity"],
                    "customer_count": monthly_customers[-1] if len(monthly_customers) > 0 else 0
                }
                
                # Create prompt for the LLM
                prompt = f"""
                Calculate key financial metrics for a {investment_type} investment based on the following financial data:
                
                Financial Data:
                - Revenue: ${context['latest_year_revenue']:,.2f}
                - Gross Profit: ${context['latest_year_gross_profit']:,.2f}
                - Net Income: ${context['latest_year_net_income']:,.2f}
                - Cash Flow: ${context['latest_year_cash_flow']:,.2f}
                - Ending Cash: ${context['latest_year_ending_cash']:,.2f}
                - Total Assets: ${context['latest_year_assets']:,.2f}
                - Liabilities: ${context['latest_year_liabilities']:,.2f}
                - Equity: ${context['latest_year_equity']:,.2f}
                - Customer Count: {context['customer_count']}
                
                Calculated Basic Metrics:
                - Gross Margin: {gross_margin:.2%}
                - Net Margin: {net_margin:.2%}
                
                Based on this data, calculate additional metrics that are important for a {investment_type} investment.
                """
                
                # Add specific metrics based on investment type
                if investment_type.lower() in ["startup", "business", "saas"]:
                    prompt += """
                    Please calculate the following SaaS/business metrics:
                    1. Customer Acquisition Cost (CAC)
                    2. Customer Lifetime Value (CLV)
                    3. Average Revenue Per User (ARPU)
                    4. ROI (calculated as CLV/CAC)
                    5. Payback Period (months to recoup CAC)
                    6. Monthly Burn Rate
                    7. Runway (months of cash remaining)
                    8. Break-even Point (month and customer count)
                    
                    Use reasonable estimates based on typical values in this industry where specific data isn't available.
                    """
                elif investment_type.lower() in ["real estate", "reit", "property"]:
                    prompt += """
                    Please calculate the following real estate metrics:
                    1. Cap Rate
                    2. Cash-on-Cash Return
                    3. Debt Service Coverage Ratio
                    4. Gross Rent Multiplier
                    5. Net Operating Income (NOI)
                    6. Return on Investment
                    7. Vacancy Rate
                    
                    Use reasonable estimates based on typical values in this industry where specific data isn't available.
                    """
                elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
                    prompt += """
                    Please calculate the following tokenized asset metrics:
                    1. Token Velocity
                    2. Daily Active Users to Monthly Active Users Ratio
                    3. Transaction Volume Growth Rate
                    4. Network Value to Transactions Ratio
                    5. Return on Investment
                    6. Platform Growth Rate
                    7. Token Holder Retention Rate
                    
                    Use reasonable estimates based on typical values in this industry where specific data isn't available.
                    """
                else:
                    prompt += """
                    Please calculate the following general business metrics:
                    1. Return on Assets (ROA)
                    2. Return on Equity (ROE)
                    3. Debt-to-Equity Ratio
                    4. Operating Cash Flow Ratio
                    5. Current Ratio
                    6. Working Capital
                    7. Asset Turnover Ratio
                    
                    Use reasonable estimates based on typical values in this industry where specific data isn't available.
                    """
                
                prompt += """
                Format your response as a JSON object where each key is the metric name (in snake_case) and the value is the calculated metric as a numeric value.
                For metrics that have multiple components (like break_even_point), use a nested object.
                Do not include explanations in the JSON - only the metric names and values.
                """
                
                # Call LLM to generate financial metrics
                response = self.reasoning_model.generate(prompt, system_prompt=self.system_prompt)
                
                # Parse the response to extract metrics
                import re
                import json
                
                # Find JSON object in the response
                json_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
                if json_match:
                    additional_metrics = json.loads(json_match.group(0))
                    
                    # Merge calculated metrics with additional metrics from LLM
                    metrics.update(additional_metrics)
                    logger.info(f"Successfully calculated additional metrics using LLM")
                    return metrics
                
                # If parsing fails, try with general model
                logger.info("Trying with general model for metrics calculation")
                response = self.general_model.generate(prompt, system_prompt=self.system_prompt)
                
                # Find JSON object in the response
                json_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
                if json_match:
                    additional_metrics = json.loads(json_match.group(0))
                    
                    # Merge calculated metrics with additional metrics from LLM
                    metrics.update(additional_metrics)
                    logger.info(f"Successfully calculated additional metrics using general model")
                    return metrics
                
            except Exception as e:
                logger.error(f"Error calculating metrics with LLM: {e}")
                logger.info("Falling back to default metrics")
        
        # Fallback: Return default metrics if LLM is not available or fails
        logger.info(f"Using default metrics for {investment_type}")
        
        # Return industry-specific default metrics
        if investment_type.lower() in ["startup", "business", "saas"]:
            metrics.update({
                "cac": 800,  # Customer Acquisition Cost
                "clv": 3500,  # Customer Lifetime Value
                "arpu": 1200,  # Average Revenue Per User
                "roi": 4.375,  # Return on Investment (CLV/CAC)
                "payback_period": 8,  # Months to recoup CAC
                "monthly_burn_rate": 35000,  # Monthly cash burn
                "runway": 7.1,  # Months of runway at current burn rate
                "break_even_point": {
                    "month": 14,
                    "customers": 150
                }
            })
        elif investment_type.lower() in ["real estate", "reit", "property"]:
            metrics.update({
                "cap_rate": 0.065,  # Capitalization Rate
                "cash_on_cash_return": 0.082,  # Cash-on-Cash Return
                "debt_service_coverage_ratio": 1.35,  # DSCR
                "gross_rent_multiplier": 8.5,  # GRM
                "noi": latest_year["operating_income"],  # Net Operating Income
                "roi": 0.094,  # Return on Investment
                "vacancy_rate": 0.06  # Vacancy Rate
            })
        elif investment_type.lower() in ["tokenized asset", "digital asset", "crypto"]:
            metrics.update({
                "token_velocity": 4.2,  # Token Velocity
                "dau_mau_ratio": 0.25,  # Daily Active Users / Monthly Active Users
                "transaction_volume_growth": 0.15,  # Transaction Volume Growth Rate
                "nvt_ratio": 12.5,  # Network Value to Transactions Ratio
                "roi": 0.18,  # Return on Investment
                "platform_growth_rate": 0.085,  # Platform Growth Rate
                "token_holder_retention": 0.72  # Token Holder Retention Rate
            })
        else:
            metrics.update({
                "roa": 0.08,  # Return on Assets
                "roe": 0.12,  # Return on Equity
                "debt_to_equity": 1.2,  # Debt-to-Equity Ratio
                "operating_cash_flow_ratio": 1.5,  # Operating Cash Flow Ratio
                "current_ratio": 1.8,  # Current Ratio
                "working_capital": 120000,  # Working Capital
                "asset_turnover": 0.7  # Asset Turnover Ratio
            })
        
        return metrics
    
    def _perform_scenario_analysis(
        self,
        revenue_projections: Dict[str, Any],
        expense_projections: Dict[str, Any],
        market_analysis: Dict[str, Any],
        timeframe_years: int,
        investment_type: str = "business"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform scenario analysis on the financial model."""
        logger.info("Performing scenario analysis")
        
        # Extract key information for the LLM
        growth_rate = market_analysis.get("growth_rate", "5% CAGR")
        if isinstance(growth_rate, str) and "CAGR" in growth_rate:
            try:
                growth_rate = float(growth_rate.replace("% CAGR", "")) / 100
            except ValueError:
                growth_rate = 0.05
        
        # Get base revenue and expenses
        base_annual_revenue = revenue_projections["annual"]["revenue"]
        base_annual_expenses = expense_projections["annual"]["total"]
        
        # Prepare prompt for the LLM to determine scenario parameters
        prompt = f"""
        Design a comprehensive scenario analysis for a {investment_type} investment over {timeframe_years} years.
        
        Current Assumptions:
        - Market growth rate: {growth_rate * 100:.1f}% annually
        
        Base case financial data:
        - Year 1 revenue: ${base_annual_revenue[0]:,.2f}
        - Year {timeframe_years} revenue: ${base_annual_revenue[-1]:,.2f}
        - Year 1 expenses: ${base_annual_expenses[0]:,.2f}
        - Year {timeframe_years} expenses: ${base_annual_expenses[-1]:,.2f}
        
        Please determine appropriate scenario parameters:
        
        1. For the Optimistic Case (what positive factors might occur and their impact)
           - What would cause this scenario?
           - How much higher would revenue be (as a percentage increase from base)?
           - How would expenses be affected (as a percentage change from base)?
        
        2. For the Pessimistic Case (what negative factors might occur and their impact)
           - What would cause this scenario?
           - How much lower would revenue be (as a percentage decrease from base)?
           - How would expenses be affected (as a percentage change from base)?
        
        Format your response as:
        
        Optimistic Scenario:
        Description: [1-2 sentences describing this scenario]
        Revenue Factor: [number, e.g. 1.3 for 30% higher]
        Expense Factor: [number, e.g. 0.9 for 10% lower]
        
        Pessimistic Scenario:
        Description: [1-2 sentences describing this scenario]
        Revenue Factor: [number, e.g. 0.7 for 30% lower]
        Expense Factor: [number, e.g. 1.2 for 20% higher]
        """
        
        # Customize the prompt based on investment type
        if investment_type.lower() in ["startup", "early stage", "seed"]:
            prompt += """
            For startups, consider:
            - Customer acquisition rates
            - Churn rates
            - Pricing power
            - Market adoption speed
            - Competitive landscape changes
            """
        elif investment_type.lower() in ["real estate", "reit"]:
            prompt += """
            For real estate investments, consider:
            - Occupancy rate fluctuations
            - Rental rate changes
            - Property value appreciation/depreciation
            - Interest rate impacts
            - Operating expense variations
            """
        elif investment_type.lower() in ["tokenized asset", "digital asset"]:
            prompt += """
            For tokenized assets, consider:
            - Token adoption rates
            - Market liquidity changes
            - Regulatory impacts
            - Competition from other tokens
            - Technology risks
            """
        elif investment_type.lower() in ["private credit", "debt"]:
            prompt += """
            For debt investments, consider:
            - Interest rate changes
            - Default rate variations
            - Early repayment risks
            - Credit quality shifts
            - Origination volume changes
            """
        
        # Call the LLM to determine scenario parameters if available
        if self.has_models:
            try:
                scenario_text = self.reasoning_model.generate(prompt, system_prompt=self.system_prompt)
                scenarios = self._parse_scenario_params(scenario_text, revenue_projections, expense_projections)
                
                if scenarios and "optimistic" in scenarios and "pessimistic" in scenarios:
                    logger.info("Successfully generated scenario analysis using LLM")
                    return scenarios
            except Exception as e:
                logger.error(f"Error generating scenarios with LLM: {e}")
                logger.info("Falling back to simplified approach")
                
            # Try with general model if reasoning model fails
            try:
                scenario_text = self.general_model.generate(prompt, system_prompt=self.system_prompt)
                scenarios = self._parse_scenario_params(scenario_text, revenue_projections, expense_projections)
                
                if scenarios and "optimistic" in scenarios and "pessimistic" in scenarios:
                    logger.info("Successfully generated scenario analysis using fallback model")
                    return scenarios
            except Exception as e:
                logger.error(f"Error generating scenarios with fallback model: {e}")
                logger.info("Using default scenarios")
        
        # If LLM is not available or fails, use default scenarios based on investment type
        logger.info(f"Using default scenarios for {investment_type}")
        return self._generate_default_scenarios(investment_type, revenue_projections, expense_projections)
    
    def _generate_default_scenarios(
        self, 
        investment_type: str, 
        revenue_projections: Dict[str, Any],
        expense_projections: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate default scenarios when LLM generation fails."""
        base_annual_revenue = revenue_projections["annual"]["revenue"]
        base_annual_expenses = expense_projections["annual"]["total"]
        
        # Calculate profit for base scenario
        base_profit = [r - e for r, e in zip(base_annual_revenue, base_annual_expenses)]
        
        # Set scenario parameters based on investment type
        if investment_type.lower() in ["startup", "early stage", "seed"]:
            # Startups tend to have higher volatility
            optimistic_revenue_factor = 1.3  # 30% better
            optimistic_expense_factor = 0.9  # 10% lower
            pessimistic_revenue_factor = 0.7  # 30% worse
            pessimistic_expense_factor = 1.2  # 20% higher
            optimistic_scenario_desc = "Faster market adoption, lower customer acquisition costs, and better retention rates."
            pessimistic_scenario_desc = "Slower market adoption, higher acquisition costs, and increased competition."
        elif investment_type.lower() in ["real estate", "reit"]:
            # Real estate tends to be more stable
            optimistic_revenue_factor = 1.15  # 15% better
            optimistic_expense_factor = 0.95  # 5% lower
            pessimistic_revenue_factor = 0.85  # 15% worse
            pessimistic_expense_factor = 1.1  # 10% higher
            optimistic_scenario_desc = "Higher occupancy rates, rental growth, and property appreciation."
            pessimistic_scenario_desc = "Lower occupancy rates, rental decline, and property value stagnation."
        elif investment_type.lower() in ["tokenized asset", "digital asset"]:
            # Digital assets tend to be highly volatile
            optimistic_revenue_factor = 1.5  # 50% better
            optimistic_expense_factor = 0.9  # 10% lower
            pessimistic_revenue_factor = 0.5  # 50% worse
            pessimistic_expense_factor = 1.2  # 20% higher
            optimistic_scenario_desc = "Rapid token adoption, increased liquidity, and favorable regulatory environment."
            pessimistic_scenario_desc = "Slow token adoption, liquidity challenges, and unfavorable regulatory changes."
        elif investment_type.lower() in ["private credit", "debt"]:
            # Debt investments tend to have lower upside but defined downside
            optimistic_revenue_factor = 1.1  # 10% better
            optimistic_expense_factor = 0.95  # 5% lower
            pessimistic_revenue_factor = 0.8  # 20% worse
            pessimistic_expense_factor = 1.15  # 15% higher
            optimistic_scenario_desc = "Lower default rates, higher quality borrowers, and favorable interest rates."
            pessimistic_scenario_desc = "Higher default rates, difficulty in origination, and unfavorable interest rates."
        else:
            # Default/generic business
            optimistic_revenue_factor = 1.2  # 20% better
            optimistic_expense_factor = 0.95  # 5% lower
            pessimistic_revenue_factor = 0.8  # 20% worse
            pessimistic_expense_factor = 1.1  # 10% higher
            optimistic_scenario_desc = "Favorable market conditions, higher growth, and operational efficiencies."
            pessimistic_scenario_desc = "Challenging market conditions, lower growth, and operational challenges."
        
        # Create optimistic scenario
        optimistic_revenue = [r * optimistic_revenue_factor for r in base_annual_revenue]
        optimistic_expenses = [e * optimistic_expense_factor for e in base_annual_expenses]
        optimistic_profit = [r - e for r, e in zip(optimistic_revenue, optimistic_expenses)]
        
        # Create pessimistic scenario
        pessimistic_revenue = [r * pessimistic_revenue_factor for r in base_annual_revenue]
        pessimistic_expenses = [e * pessimistic_expense_factor for e in base_annual_expenses]
        pessimistic_profit = [r - e for r, e in zip(pessimistic_revenue, pessimistic_expenses)]
        
        # Generate scenario descriptions based on investment type
        base_scenario_desc = "Continuation of current trends and assumptions."
        
        if investment_type.lower() in ["startup", "early stage", "seed"]:
            optimistic_scenario_desc = "Faster market adoption, lower customer acquisition costs, and better retention rates."
            pessimistic_scenario_desc = "Slower market adoption, higher acquisition costs, and increased competition."
        elif investment_type.lower() in ["real estate", "reit"]:
            optimistic_scenario_desc = "Higher occupancy rates, rental growth, and property appreciation."
            pessimistic_scenario_desc = "Lower occupancy rates, rental decline, and property value stagnation."
        elif investment_type.lower() in ["tokenized asset", "digital asset"]:
            optimistic_scenario_desc = "Rapid token adoption, increased liquidity, and favorable regulatory environment."
            pessimistic_scenario_desc = "Slow token adoption, liquidity challenges, and unfavorable regulatory changes."
        elif investment_type.lower() in ["private credit", "debt"]:
            optimistic_scenario_desc = "Lower default rates, higher quality borrowers, and favorable interest rates."
            pessimistic_scenario_desc = "Higher default rates, difficulty in origination, and unfavorable interest rates."
        else:
            optimistic_scenario_desc = "Favorable market conditions, higher growth, and operational efficiencies."
            pessimistic_scenario_desc = "Challenging market conditions, lower growth, and operational challenges."
        
        # Construct scenarios with descriptions and assumptions
        scenarios = {
            "base": [
                {
                    "year": i+1, 
                    "revenue": r, 
                    "expenses": e, 
                    "profit": p,
                    "description": base_scenario_desc if i == 0 else ""
                }
                for i, (r, e, p) in enumerate(zip(base_annual_revenue, base_annual_expenses, base_profit))
            ],
            "optimistic": [
                {
                    "year": i+1, 
                    "revenue": r, 
                    "expenses": e, 
                    "profit": p,
                    "description": optimistic_scenario_desc if i == 0 else ""
                }
                for i, (r, e, p) in enumerate(zip(optimistic_revenue, optimistic_expenses, optimistic_profit))
            ],
            "pessimistic": [
                {
                    "year": i+1, 
                    "revenue": r, 
                    "expenses": e, 
                    "profit": p,
                    "description": pessimistic_scenario_desc if i == 0 else ""
                }
                for i, (r, e, p) in enumerate(zip(pessimistic_revenue, pessimistic_expenses, pessimistic_profit))
            ]
        }
        
        # Add scenario assumptions
        scenarios["assumptions"] = {
            "base": {
                "revenue_factor": 1.0,
                "expense_factor": 1.0,
                "description": base_scenario_desc
            },
            "optimistic": {
                "revenue_factor": optimistic_revenue_factor,
                "expense_factor": optimistic_expense_factor,
                "description": optimistic_scenario_desc
            },
            "pessimistic": {
                "revenue_factor": pessimistic_revenue_factor,
                "expense_factor": pessimistic_expense_factor,
                "description": pessimistic_scenario_desc
            }
        }
        
       
        return scenarios
        
    def _parse_scenario_params(
        self, 
        scenario_text: str, 
        revenue_projections: Dict[str, Any],
        expense_projections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse scenario parameters from LLM response and generate scenarios.
        
        Args:
            scenario_text: Raw text from LLM with scenario parameters
            revenue_projections: Original revenue projections
            expense_projections: Original expense projections
            
        Returns:
            Complete scenario analysis with all scenarios
        """
        logger.info("Parsing scenario parameters from LLM response")
        
        base_annual_revenue = revenue_projections["annual"]["revenue"]
        base_annual_expenses = expense_projections["annual"]["total"]
        
        # Parse the LLM's response to extract scenario parameters
        # Default parameters in case parsing fails
        scenario_params = {
            "base": {
                "revenue_factor": 1.0,
                "expense_factor": 1.0,
                "description": "Base case scenario using current assumptions."
            },
            "optimistic": {
                "revenue_factor": 1.2,  # Default until parsed
                "expense_factor": 0.95,  # Default until parsed
                "description": "Optimistic case with favorable conditions."
            },
            "pessimistic": {
                "revenue_factor": 0.8,  # Default until parsed
                "expense_factor": 1.1,  # Default until parsed
                "description": "Pessimistic case with challenging conditions."
            }
        }
        
        # Extract optimistic scenario parameters
        optimistic_match = re.search(
            r"Optimistic Scenario:.*?Description:\s*(.*?)(?:\n|\r\n).*?Revenue Factor:\s*([0-9.]+).*?Expense Factor:\s*([0-9.]+)",
            scenario_text,
            re.DOTALL
        )
        
        if optimistic_match:
            try:
                desc = optimistic_match.group(1).strip()
                rev_factor = float(optimistic_match.group(2).strip())
                exp_factor = float(optimistic_match.group(3).strip())
                
                # Validate the values
                if 1.0 <= rev_factor <= 3.0 and 0.5 <= exp_factor <= 1.5:
                    scenario_params["optimistic"]["description"] = desc
                    scenario_params["optimistic"]["revenue_factor"] = rev_factor
                    scenario_params["optimistic"]["expense_factor"] = exp_factor
                    logger.info(f"Parsed optimistic scenario: revenue factor {rev_factor}, expense factor {exp_factor}")
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing optimistic scenario: {e}")
        
        # Extract pessimistic scenario parameters
        pessimistic_match = re.search(
            r"Pessimistic Scenario:.*?Description:\s*(.*?)(?:\n|\r\n).*?Revenue Factor:\s*([0-9.]+).*?Expense Factor:\s*([0-9.]+)",
            scenario_text,
            re.DOTALL
        )
        
        if pessimistic_match:
            try:
                desc = pessimistic_match.group(1).strip()
                rev_factor = float(pessimistic_match.group(2).strip())
                exp_factor = float(pessimistic_match.group(3).strip())
                
                # Validate the values
                if 0.1 <= rev_factor <= 1.0 and 1.0 <= exp_factor <= 2.0:
                    scenario_params["pessimistic"]["description"] = desc
                    scenario_params["pessimistic"]["revenue_factor"] = rev_factor
                    scenario_params["pessimistic"]["expense_factor"] = exp_factor
                    logger.info(f"Parsed pessimistic scenario: revenue factor {rev_factor}, expense factor {exp_factor}")
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing pessimistic scenario: {e}")
        
        # Calculate scenarios based on the parameters
        scenarios = {}
        
        # Calculate base case scenario
        base_profit = [r - e for r, e in zip(base_annual_revenue, base_annual_expenses)]
        
        scenarios["base"] = [
            {
                "year": i+1, 
                "revenue": r, 
                "expenses": e, 
                "profit": p,
                "description": scenario_params["base"]["description"] if i == 0 else ""
            }
            for i, (r, e, p) in enumerate(zip(base_annual_revenue, base_annual_expenses, base_profit))
        ]
        
        # Calculate optimistic scenario
        optimistic_revenue = [r * scenario_params["optimistic"]["revenue_factor"] for r in base_annual_revenue]
        optimistic_expenses = [e * scenario_params["optimistic"]["expense_factor"] for e in base_annual_expenses]
        optimistic_profit = [r - e for r, e in zip(optimistic_revenue, optimistic_expenses)]
        
        scenarios["optimistic"] = [
            {
                "year": i+1, 
                "revenue": r, 
                "expenses": e, 
                "profit": p,
                "description": scenario_params["optimistic"]["description"] if i == 0 else ""
            }
            for i, (r, e, p) in enumerate(zip(optimistic_revenue, optimistic_expenses, optimistic_profit))
        ]
        
        # Calculate pessimistic scenario
        pessimistic_revenue = [r * scenario_params["pessimistic"]["revenue_factor"] for r in base_annual_revenue]
        pessimistic_expenses = [e * scenario_params["pessimistic"]["expense_factor"] for e in base_annual_expenses]
        pessimistic_profit = [r - e for r, e in zip(pessimistic_revenue, pessimistic_expenses)]
        
        scenarios["pessimistic"] = [
            {
                "year": i+1, 
                "revenue": r, 
                "expenses": e, 
                "profit": p,
                "description": scenario_params["pessimistic"]["description"] if i == 0 else ""
            }
            for i, (r, e, p) in enumerate(zip(pessimistic_revenue, pessimistic_expenses, pessimistic_profit))
        ]
        
        # Add the original parameters
        scenarios["assumptions"] = scenario_params
        
        return scenarios