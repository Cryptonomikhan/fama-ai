"""
Revenue Modeling Tools for Financial Modeling.

This module provides tools for building financial models with different revenue structures
and projecting financial performance.
"""

import logging
import re
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RevenueModelingTools:
    """
    Tools for financial modeling and revenue projections.
    
    Provides methods for creating financial projections with different revenue models,
    such as subscription, pay-as-you-go, and one-time purchase.
    """
    
    def __init__(self):
        self.name = "RevenueModelingTools"
        self.description = "Tools for financial modeling and revenue projections"
    
    async def model_subscription_revenue(self, query: str) -> str:
        """
        Create a subscription revenue model with financial projections.
        
        Args:
            query: Query with parameters for the subscription model
            
        Returns:
            Subscription revenue projections with growth metrics
        """
        logger.info("Modeling subscription revenue")
        
        # Parse parameters from query
        # In a real implementation, this would be more sophisticated
        params = self._extract_model_parameters(query)
        
        # Set up default parameters if not provided
        initial_customers = params.get("initial_customers", 100)
        churn_rate = params.get("churn_rate", 0.05)  # 5% monthly churn
        acquisition_rate = params.get("acquisition_rate", 0.15)  # 15% monthly growth
        arpu = params.get("arpu", 50)  # Average Revenue Per User
        cac = params.get("cac", 300)  # Customer Acquisition Cost
        gross_margin = params.get("gross_margin", 0.7)  # 70% gross margin
        timeframe_months = params.get("timeframe_months", 60)  # 5 years
        starting_month = 1
        
        # Generate projections
        months = range(starting_month, starting_month + timeframe_months)
        customers = [initial_customers]
        new_customers = []
        churned_customers = []
        revenue = []
        cac_costs = []
        gross_profit = []
        
        for month in months:
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
            current_arpu = arpu * (1 + 0.002 * month)  # Small monthly increase
            monthly_revenue = end_month_customers * current_arpu
            revenue.append(monthly_revenue)
            
            # Calculate CAC costs
            monthly_cac = new_customer_count * cac
            cac_costs.append(monthly_cac)
            
            # Calculate gross profit
            monthly_gross_profit = monthly_revenue * gross_margin
            gross_profit.append(monthly_gross_profit)
        
        # Remove the initial customer count (it was just a starting point)
        customers.pop(0)
        
        # Format the model results for response
        response = "# Subscription Revenue Model\n\n"
        
        response += "## Model Parameters\n\n"
        response += f"- **Initial Customers:** {initial_customers}\n"
        response += f"- **Monthly Churn Rate:** {churn_rate:.1%}\n"
        response += f"- **Monthly Acquisition Rate:** {acquisition_rate:.1%}\n"
        response += f"- **Average Revenue Per User:** ${arpu:.2f}\n"
        response += f"- **Customer Acquisition Cost:** ${cac:.2f}\n"
        response += f"- **Gross Margin:** {gross_margin:.1%}\n"
        response += f"- **Timeframe:** {timeframe_months} months ({timeframe_months/12:.1f} years)\n\n"
        
        # Calculate key metrics
        response += "## Key Metrics\n\n"
        final_customers = customers[-1]
        total_acquired = sum(new_customers)
        customer_growth = (final_customers - initial_customers) / initial_customers
        clv = arpu * gross_margin * (1 / churn_rate)  # Simple CLV calculation
        payback_period = cac / (arpu * gross_margin)
        
        response += f"- **Final Customer Count:** {final_customers:.0f}\n"
        response += f"- **Total New Customers Acquired:** {total_acquired:.0f}\n"
        response += f"- **Customer Growth:** {customer_growth:.1%}\n"
        response += f"- **Customer Lifetime Value (CLV):** ${clv:.2f}\n"
        response += f"- **CAC Payback Period:** {payback_period:.1f} months\n"
        response += f"- **LTV/CAC Ratio:** {clv/cac:.2f}x\n\n"
        
        # Show annual summary
        response += "## Annual Summary\n\n"
        response += "| Year | Customers | Revenue | Gross Profit | CAC Costs | Net Contribution |\n"
        response += "|------|-----------|---------|--------------|-----------|------------------|\n"
        
        for year in range(int(timeframe_months / 12)):
            start_idx = year * 12
            end_idx = start_idx + 12
            
            year_customers = customers[end_idx - 1]
            year_revenue = sum(revenue[start_idx:end_idx])
            year_gross_profit = sum(gross_profit[start_idx:end_idx])
            year_cac = sum(cac_costs[start_idx:end_idx])
            year_contribution = year_gross_profit - year_cac
            
            response += f"| {year + 1} | {year_customers:.0f} | ${year_revenue:.0f} | ${year_gross_profit:.0f} | ${year_cac:.0f} | ${year_contribution:.0f} |\n"
        
        # Include chart data for visualization
        response += "\n## Chart Data\n\n"
        response += "```json\n"
        chart_data = {
            "months": list(months),
            "customers": customers,
            "revenue": revenue,
            "gross_profit": gross_profit,
            "cac_costs": cac_costs,
            "net_contribution": [gp - cac for gp, cac in zip(gross_profit, cac_costs)]
        }
        import json
        response += json.dumps(chart_data, indent=2)
        response += "\n```\n"
        
        return response
    
    async def model_pay_as_you_go_revenue(self, query: str) -> str:
        """
        Create a pay-as-you-go (usage-based) revenue model with financial projections.
        
        Args:
            query: Query with parameters for the usage-based model
            
        Returns:
            Pay-as-you-go revenue projections with usage metrics
        """
        logger.info("Modeling pay-as-you-go revenue")
        
        # Parse parameters from query
        params = self._extract_model_parameters(query)
        
        # Set up default parameters if not provided
        initial_customers = params.get("initial_customers", 100)
        churn_rate = params.get("churn_rate", 0.04)  # 4% monthly churn (typically lower than subscription)
        acquisition_rate = params.get("acquisition_rate", 0.12)  # 12% monthly growth
        avg_usage_per_customer = params.get("avg_usage", 100)  # Units per customer
        price_per_unit = params.get("price_per_unit", 0.05)  # $0.05 per unit
        cac = params.get("cac", 250)  # Customer Acquisition Cost
        variable_cost_per_unit = params.get("variable_cost", 0.02)  # $0.02 per unit
        timeframe_months = params.get("timeframe_months", 60)  # 5 years
        starting_month = 1
        
        # Calculate gross margin per unit
        gross_margin_per_unit = (price_per_unit - variable_cost_per_unit) / price_per_unit
        
        # Generate projections
        months = range(starting_month, starting_month + timeframe_months)
        customers = [initial_customers]
        new_customers = []
        churned_customers = []
        usage = []
        revenue = []
        variable_costs = []
        cac_costs = []
        gross_profit = []
        
        # Usage growth factor (users tend to use more over time)
        usage_growth_factor = 1.005  # 0.5% monthly usage growth per customer
        
        for month in months:
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
            
            # Calculate monthly usage (with growth over time)
            current_avg_usage = avg_usage_per_customer * (usage_growth_factor ** (month - 1))
            monthly_usage = end_month_customers * current_avg_usage
            usage.append(monthly_usage)
            
            # Calculate monthly revenue
            monthly_revenue = monthly_usage * price_per_unit
            revenue.append(monthly_revenue)
            
            # Calculate variable costs
            monthly_variable_costs = monthly_usage * variable_cost_per_unit
            variable_costs.append(monthly_variable_costs)
            
            # Calculate CAC costs
            monthly_cac = new_customer_count * cac
            cac_costs.append(monthly_cac)
            
            # Calculate gross profit
            monthly_gross_profit = monthly_revenue - monthly_variable_costs
            gross_profit.append(monthly_gross_profit)
        
        # Remove the initial customer count (it was just a starting point)
        customers.pop(0)
        
        # Format the model results for response
        response = "# Pay-As-You-Go Revenue Model\n\n"
        
        response += "## Model Parameters\n\n"
        response += f"- **Initial Customers:** {initial_customers}\n"
        response += f"- **Monthly Churn Rate:** {churn_rate:.1%}\n"
        response += f"- **Monthly Acquisition Rate:** {acquisition_rate:.1%}\n"
        response += f"- **Initial Avg Usage Per Customer:** {avg_usage_per_customer:.0f} units\n"
        response += f"- **Price Per Unit:** ${price_per_unit:.3f}\n"
        response += f"- **Variable Cost Per Unit:** ${variable_cost_per_unit:.3f}\n"
        response += f"- **Gross Margin Per Unit:** {gross_margin_per_unit:.1%}\n"
        response += f"- **Customer Acquisition Cost:** ${cac:.2f}\n"
        response += f"- **Timeframe:** {timeframe_months} months ({timeframe_months/12:.1f} years)\n\n"
        
        # Calculate key metrics
        response += "## Key Metrics\n\n"
        final_customers = customers[-1]
        total_acquired = sum(new_customers)
        customer_growth = (final_customers - initial_customers) / initial_customers
        final_avg_revenue = revenue[-1] / final_customers
        
        # Estimate CLV (more complex for usage-based)
        avg_monthly_revenue = final_avg_revenue
        clv = avg_monthly_revenue * gross_margin_per_unit * (1 / churn_rate)
        payback_period = cac / (avg_monthly_revenue * gross_margin_per_unit)
        
        response += f"- **Final Customer Count:** {final_customers:.0f}\n"
        response += f"- **Total New Customers Acquired:** {total_acquired:.0f}\n"
        response += f"- **Customer Growth:** {customer_growth:.1%}\n"
        response += f"- **Final Avg Monthly Revenue Per Customer:** ${final_avg_revenue:.2f}\n"
        response += f"- **Estimated Customer Lifetime Value (CLV):** ${clv:.2f}\n"
        response += f"- **CAC Payback Period:** {payback_period:.1f} months\n"
        response += f"- **LTV/CAC Ratio:** {clv/cac:.2f}x\n\n"
        
        # Show annual summary
        response += "## Annual Summary\n\n"
        response += "| Year | Customers | Total Usage | Revenue | Variable Costs | Gross Profit | CAC Costs | Net Contribution |\n"
        response += "|------|-----------|-------------|---------|----------------|--------------|-----------|------------------|\n"
        
        for year in range(int(timeframe_months / 12)):
            start_idx = year * 12
            end_idx = start_idx + 12
            
            year_customers = customers[end_idx - 1]
            year_usage = sum(usage[start_idx:end_idx])
            year_revenue = sum(revenue[start_idx:end_idx])
            year_variable_costs = sum(variable_costs[start_idx:end_idx])
            year_gross_profit = sum(gross_profit[start_idx:end_idx])
            year_cac = sum(cac_costs[start_idx:end_idx])
            year_contribution = year_gross_profit - year_cac
            
            response += f"| {year + 1} | {year_customers:.0f} | {year_usage:.0f} | ${year_revenue:.0f} | ${year_variable_costs:.0f} | ${year_gross_profit:.0f} | ${year_cac:.0f} | ${year_contribution:.0f} |\n"
        
        # Include chart data for visualization
        response += "\n## Chart Data\n\n"
        response += "```json\n"
        chart_data = {
            "months": list(months),
            "customers": customers,
            "usage": usage,
            "revenue": revenue,
            "variable_costs": variable_costs,
            "gross_profit": gross_profit,
            "cac_costs": cac_costs,
            "net_contribution": [gp - cac for gp, cac in zip(gross_profit, cac_costs)]
        }
        import json
        response += json.dumps(chart_data, indent=2)
        response += "\n```\n"
        
        return response
    
    async def model_one_time_purchase(self, query: str) -> str:
        """
        Create a one-time purchase revenue model with financial projections.
        
        Args:
            query: Query with parameters for the one-time purchase model
            
        Returns:
            One-time purchase revenue projections with sales metrics
        """
        logger.info("Modeling one-time purchase revenue")
        
        # Parse parameters from query
        params = self._extract_model_parameters(query)
        
        # Set up default parameters if not provided
        initial_monthly_sales = params.get("initial_sales", 50)
        sales_growth_rate = params.get("sales_growth", 0.08)  # 8% monthly growth
        price = params.get("price", 500)  # Price per unit
        cogs_per_unit = params.get("cogs", 150)  # Cost of goods sold per unit
        cac = params.get("cac", 200)  # Customer Acquisition Cost
        fixed_costs = params.get("fixed_costs", 20000)  # Monthly fixed costs
        timeframe_months = params.get("timeframe_months", 60)  # 5 years
        starting_month = 1
        
        # Calculate gross margin per unit
        gross_margin_per_unit = (price - cogs_per_unit) / price
        
        # Generate projections
        months = range(starting_month, starting_month + timeframe_months)
        unit_sales = []
        revenue = []
        cogs = []
        cac_costs = []
        fixed_cost_array = []
        gross_profit = []
        
        current_monthly_sales = initial_monthly_sales
        
        for month in months:
            # Calculate monthly sales (with slight randomness for realism)
            random_factor = 0.9 + 0.2 * random.random()  # 0.9 to 1.1
            
            # Add seasonality effect (higher in Q4, lower in Q1)
            month_of_year = ((month - 1) % 12) + 1
            if month_of_year in [10, 11, 12]:  # Q4
                seasonality = 1.2  # 20% boost
            elif month_of_year in [1, 2, 3]:  # Q1
                seasonality = 0.9  # 10% reduction
            else:
                seasonality = 1.0  # No effect
            
            monthly_sales = max(10, int(current_monthly_sales * random_factor * seasonality))
            unit_sales.append(monthly_sales)
            
            # Update the base sales for next month
            current_monthly_sales = current_monthly_sales * (1 + sales_growth_rate)
            
            # Calculate monthly revenue
            monthly_revenue = monthly_sales * price
            revenue.append(monthly_revenue)
            
            # Calculate COGS
            monthly_cogs = monthly_sales * cogs_per_unit
            cogs.append(monthly_cogs)
            
            # Calculate CAC costs
            monthly_cac = monthly_sales * cac
            cac_costs.append(monthly_cac)
            
            # Add fixed costs
            fixed_cost_array.append(fixed_costs)
            
            # Calculate gross profit
            monthly_gross_profit = monthly_revenue - monthly_cogs
            gross_profit.append(monthly_gross_profit)
        
        # Format the model results for response
        response = "# One-Time Purchase Revenue Model\n\n"
        
        response += "## Model Parameters\n\n"
        response += f"- **Initial Monthly Sales:** {initial_monthly_sales} units\n"
        response += f"- **Monthly Sales Growth Rate:** {sales_growth_rate:.1%}\n"
        response += f"- **Price Per Unit:** ${price:.2f}\n"
        response += f"- **COGS Per Unit:** ${cogs_per_unit:.2f}\n"
        response += f"- **Gross Margin Per Unit:** {gross_margin_per_unit:.1%}\n"
        response += f"- **Customer Acquisition Cost:** ${cac:.2f}\n"
        response += f"- **Monthly Fixed Costs:** ${fixed_costs:.2f}\n"
        response += f"- **Timeframe:** {timeframe_months} months ({timeframe_months/12:.1f} years)\n\n"
        
        # Calculate key metrics
        response += "## Key Metrics\n\n"
        total_sales = sum(unit_sales)
        total_revenue = sum(revenue)
        total_gross_profit = sum(gross_profit)
        total_cac = sum(cac_costs)
        total_fixed_costs = sum(fixed_cost_array)
        total_net_profit = total_gross_profit - total_cac - total_fixed_costs
        
        response += f"- **Total Units Sold:** {total_sales:.0f}\n"
        response += f"- **Total Revenue:** ${total_revenue:.0f}\n"
        response += f"- **Total Gross Profit:** ${total_gross_profit:.0f}\n"
        response += f"- **Total CAC Costs:** ${total_cac:.0f}\n"
        response += f"- **Total Fixed Costs:** ${total_fixed_costs:.0f}\n"
        response += f"- **Total Net Profit:** ${total_net_profit:.0f}\n"
        response += f"- **Profit Margin:** {(total_net_profit / total_revenue) if total_revenue > 0 else 0:.1%}\n\n"
        
        # Show annual summary
        response += "## Annual Summary\n\n"
        response += "| Year | Units Sold | Revenue | COGS | Gross Profit | CAC Costs | Fixed Costs | Net Profit |\n"
        response += "|------|------------|---------|------|--------------|-----------|-------------|------------|\n"
        
        for year in range(int(timeframe_months / 12)):
            start_idx = year * 12
            end_idx = start_idx + 12
            
            year_units = sum(unit_sales[start_idx:end_idx])
            year_revenue = sum(revenue[start_idx:end_idx])
            year_cogs = sum(cogs[start_idx:end_idx])
            year_gross_profit = sum(gross_profit[start_idx:end_idx])
            year_cac = sum(cac_costs[start_idx:end_idx])
            year_fixed_costs = sum(fixed_cost_array[start_idx:end_idx])
            year_net_profit = year_gross_profit - year_cac - year_fixed_costs
            
            response += f"| {year + 1} | {year_units:.0f} | ${year_revenue:.0f} | ${year_cogs:.0f} | ${year_gross_profit:.0f} | ${year_cac:.0f} | ${year_fixed_costs:.0f} | ${year_net_profit:.0f} |\n"
        
        # Include chart data for visualization
        response += "\n## Chart Data\n\n"
        response += "```json\n"
        chart_data = {
            "months": list(months),
            "unit_sales": unit_sales,
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "cac_costs": cac_costs,
            "fixed_costs": fixed_cost_array,
            "net_profit": [gp - cac - fc for gp, cac, fc in zip(gross_profit, cac_costs, fixed_cost_array)]
        }
        import json
        response += json.dumps(chart_data, indent=2)
        response += "\n```\n"
        
        return response
    
    async def perform_scenario_analysis(self, query: str) -> str:
        """
        Perform scenario analysis on different financial models.
        
        Args:
            query: Query with parameters for the scenario analysis
            
        Returns:
            Comparison of different scenarios (base, optimistic, pessimistic)
        """
        logger.info("Performing scenario analysis")
        
        # Parse parameters from query
        params = self._extract_model_parameters(query)
        
        # Set up default parameters if not provided
        business_type = params.get("business_type", "saas")
        revenue_model = params.get("revenue_model", "subscription")
        timeframe_years = params.get("timeframe_years", 5)
        
        # Create scenarios based on the revenue model
        if revenue_model.lower() in ["subscription", "saas"]:
            # Base case parameters
            base_params = {
                "initial_customers": 100,
                "churn_rate": 0.05,  # 5% monthly churn
                "acquisition_rate": 0.15,  # 15% monthly growth
                "arpu": 50,  # Average Revenue Per User
                "cac": 300,  # Customer Acquisition Cost
                "gross_margin": 0.7,  # 70% gross margin
                "timeframe_months": timeframe_years * 12
            }
            
            # Optimistic case (better metrics)
            optimistic_params = base_params.copy()
            optimistic_params.update({
                "churn_rate": 0.04,  # 4% monthly churn (better retention)
                "acquisition_rate": 0.18,  # 18% monthly growth (better acquisition)
                "arpu": 55,  # Higher ARPU
                "cac": 270,  # Lower CAC
                "gross_margin": 0.75  # Better gross margin
            })
            
            # Pessimistic case (worse metrics)
            pessimistic_params = base_params.copy()
            pessimistic_params.update({
                "churn_rate": 0.06,  # 6% monthly churn (worse retention)
                "acquisition_rate": 0.12,  # 12% monthly growth (worse acquisition)
                "arpu": 45,  # Lower ARPU
                "cac": 330,  # Higher CAC
                "gross_margin": 0.65  # Worse gross margin
            })
            
            # Run the models for each scenario
            # In a full implementation, we would call the actual model functions
            # Here we'll simulate the results for brevity
            
            # Generate key metrics for each scenario
            scenarios = {
                "base": self._simulate_subscription_scenario(base_params),
                "optimistic": self._simulate_subscription_scenario(optimistic_params),
                "pessimistic": self._simulate_subscription_scenario(pessimistic_params)
            }
            
            # Format the response
            response = "# Subscription Model Scenario Analysis\n\n"
            
            response += "## Parameter Comparison\n\n"
            response += "| Parameter | Base Case | Optimistic | Pessimistic |\n"
            response += "|-----------|-----------|------------|-------------|\n"
            response += f"| Churn Rate | {base_params['churn_rate']:.1%} | {optimistic_params['churn_rate']:.1%} | {pessimistic_params['churn_rate']:.1%} |\n"
            response += f"| Acquisition Rate | {base_params['acquisition_rate']:.1%} | {optimistic_params['acquisition_rate']:.1%} | {pessimistic_params['acquisition_rate']:.1%} |\n"
            response += f"| ARPU | ${base_params['arpu']:.2f} | ${optimistic_params['arpu']:.2f} | ${pessimistic_params['arpu']:.2f} |\n"
            response += f"| CAC | ${base_params['cac']:.2f} | ${optimistic_params['cac']:.2f} | ${pessimistic_params['cac']:.2f} |\n"
            response += f"| Gross Margin | {base_params['gross_margin']:.1%} | {optimistic_params['gross_margin']:.1%} | {pessimistic_params['gross_margin']:.1%} |\n\n"
            
            response += "## Results Comparison\n\n"
            response += "| Metric | Base Case | Optimistic | Pessimistic |\n"
            response += "|--------|-----------|------------|-------------|\n"
            response += f"| Final Customers | {scenarios['base']['final_customers']:,.0f} | {scenarios['optimistic']['final_customers']:,.0f} | {scenarios['pessimistic']['final_customers']:,.0f} |\n"
            response += f"| Year {timeframe_years} Revenue | ${scenarios['base']['final_year_revenue']:,.0f} | ${scenarios['optimistic']['final_year_revenue']:,.0f} | ${scenarios['pessimistic']['final_year_revenue']:,.0f} |\n"
            response += f"| Year {timeframe_years} Profit | ${scenarios['base']['final_year_profit']:,.0f} | ${scenarios['optimistic']['final_year_profit']:,.0f} | ${scenarios['pessimistic']['final_year_profit']:,.0f} |\n"
            response += f"| Cumulative Profit | ${scenarios['base']['cumulative_profit']:,.0f} | ${scenarios['optimistic']['cumulative_profit']:,.0f} | ${scenarios['pessimistic']['cumulative_profit']:,.0f} |\n"
            response += f"| Break-Even Month | {scenarios['base']['break_even_month']} | {scenarios['optimistic']['break_even_month']} | {scenarios['pessimistic']['break_even_month']} |\n"
            response += f"| LTV/CAC Ratio | {scenarios['base']['ltv_cac_ratio']:.2f}x | {scenarios['optimistic']['ltv_cac_ratio']:.2f}x | {scenarios['pessimistic']['ltv_cac_ratio']:.2f}x |\n\n"
            
            # Include chart data for visualization
            response += "## Annual Revenue Comparison\n\n"
            response += "| Year | Base Case | Optimistic | Pessimistic |\n"
            response += "|------|-----------|------------|-------------|\n"
            
            for year in range(timeframe_years):
                response += f"| {year + 1} | ${scenarios['base']['annual_revenue'][year]:,.0f} | ${scenarios['optimistic']['annual_revenue'][year]:,.0f} | ${scenarios['pessimistic']['annual_revenue'][year]:,.0f} |\n"
            
            response += "\n## Annual Profit Comparison\n\n"
            response += "| Year | Base Case | Optimistic | Pessimistic |\n"
            response += "|------|-----------|------------|-------------|\n"
            
            for year in range(timeframe_years):
                response += f"| {year + 1} | ${scenarios['base']['annual_profit'][year]:,.0f} | ${scenarios['optimistic']['annual_profit'][year]:,.0f} | ${scenarios['pessimistic']['annual_profit'][year]:,.0f} |\n"
            
            response += "\n## Scenario Analysis Chart Data\n\n"
            response += "```json\n"
            chart_data = {
                "years": list(range(1, timeframe_years + 1)),
                "revenue": {
                    "base": scenarios['base']['annual_revenue'],
                    "optimistic": scenarios['optimistic']['annual_revenue'],
                    "pessimistic": scenarios['pessimistic']['annual_revenue']
                },
                "profit": {
                    "base": scenarios['base']['annual_profit'],
                    "optimistic": scenarios['optimistic']['annual_profit'],
                    "pessimistic": scenarios['pessimistic']['annual_profit']
                }
            }
            import json
            response += json.dumps(chart_data, indent=2)
            response += "\n```\n"
            
            return response
        
        else:
            return f"Scenario analysis for {revenue_model} revenue model is not implemented yet. Please try subscription, pay-as-you-go, or one-time-purchase."
    
    def _extract_model_parameters(self, query: str) -> Dict[str, Any]:
        """Helper method to extract model parameters from a query string or dict."""
        if isinstance(query, dict):
            # If the query is already a dictionary, use it directly
            return query
        
        # Otherwise, parse parameters from the query string
        params = {}
        
        # Extract numerical parameters using regex
        param_patterns = [
            ("initial_customers", r"(?:initial|starting)\s+customers\s*(?::|=)\s*(\d+)"),
            ("churn_rate", r"churn\s+rate\s*(?::|=)\s*(0\.\d+|\d+%)"),
            ("acquisition_rate", r"(?:acquisition|growth)\s+rate\s*(?::|=)\s*(0\.\d+|\d+%)"),
            ("arpu", r"(?:arpu|average\s+revenue\s+per\s+user)\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("cac", r"(?:cac|customer\s+acquisition\s+cost)\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("gross_margin", r"gross\s+margin\s*(?::|=)\s*(0\.\d+|\d+%)"),
            ("timeframe_years", r"(?:timeframe|years)\s*(?::|=)\s*(\d+)"),
            ("timeframe_months", r"(?:months)\s*(?::|=)\s*(\d+)"),
            ("price", r"price\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("cogs", r"(?:cogs|cost\s+of\s+goods)\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("fixed_costs", r"fixed\s+costs\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("avg_usage", r"(?:avg|average)\s+usage\s*(?::|=)\s*(\d+(?:\.\d+)?)"),
            ("price_per_unit", r"price\s+per\s+unit\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)"),
            ("variable_cost", r"variable\s+cost\s*(?::|=)\s*\$?(\d+(?:\.\d+)?)")
        ]
        
        for param_name, pattern in param_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Convert percentage strings to floats
                if "%" in value:
                    value = float(value.strip("%")) / 100
                # Convert to appropriate type
                if param_name in ["initial_customers", "timeframe_years", "timeframe_months"]:
                    params[param_name] = int(value)
                else:
                    params[param_name] = float(value)
        
        # Extract string parameters
        string_patterns = [
            ("business_type", r"business\s+type\s*(?::|=)\s*(\w+)"),
            ("revenue_model", r"revenue\s+model\s*(?::|=)\s*(\w+)")
        ]
        
        for param_name, pattern in string_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                params[param_name] = match.group(1).lower()
        
        return params
    
    def _simulate_subscription_scenario(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to simulate subscription model scenario outcomes."""
        # Extract parameters
        initial_customers = params["initial_customers"]
        churn_rate = params["churn_rate"]
        acquisition_rate = params["acquisition_rate"]
        arpu = params["arpu"]
        cac = params["cac"]
        gross_margin = params["gross_margin"]
        timeframe_months = params["timeframe_months"]
        timeframe_years = timeframe_months // 12
        
        # Simplified model calculations
        customers = initial_customers
        monthly_customers = [customers]
        monthly_revenue = []
        monthly_costs = []
        monthly_profit = []
        cumulative_profit = 0
        break_even_month = None
        
        for month in range(1, timeframe_months + 1):
            # New and churned customers
            new_customers = customers * acquisition_rate
            churned_customers = customers * churn_rate
            customers = customers + new_customers - churned_customers
            monthly_customers.append(customers)
            
            # Revenue and costs
            revenue = customers * arpu
            cac_costs = new_customers * cac
            operating_costs = revenue * (1 - gross_margin)
            total_costs = cac_costs + operating_costs
            profit = revenue - total_costs
            
            monthly_revenue.append(revenue)
            monthly_costs.append(total_costs)
            monthly_profit.append(profit)
            
            # Cumulative profit for break-even calculation
            cumulative_profit += profit
            if cumulative_profit >= 0 and break_even_month is None:
                break_even_month = month
        
        # Calculate annual metrics
        annual_revenue = []
        annual_profit = []
        
        for year in range(timeframe_years):
            start_idx = year * 12
            end_idx = start_idx + 12
            
            annual_revenue.append(sum(monthly_revenue[start_idx:end_idx]))
            annual_profit.append(sum(monthly_profit[start_idx:end_idx]))
        
        # Calculate LTV/CAC ratio
        ltv = arpu * gross_margin * (1 / churn_rate)
        ltv_cac_ratio = ltv / cac
        
        # Compile results
        results = {
            "final_customers": monthly_customers[-1],
            "final_year_revenue": annual_revenue[-1],
            "final_year_profit": annual_profit[-1],
            "cumulative_profit": sum(monthly_profit),
            "break_even_month": break_even_month if break_even_month else "N/A",
            "ltv_cac_ratio": ltv_cac_ratio,
            "annual_revenue": annual_revenue,
            "annual_profit": annual_profit
        }
        
        return results 