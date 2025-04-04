from agno.tools import Toolkit
import numpy_financial as npf
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Union, Any
from agno.utils.log import logger

class FinancialCalculationTools(Toolkit):
    """Tools for performing financial calculations"""
    
    def __init__(self):
        super().__init__(name="financial_calculation_tools")
        # Register all the functions
        self.register(self.calculate_dcf)
        self.register(self.calculate_irr)
        self.register(self.calculate_payback_period)
        self.register(self.build_income_statement)
        self.register(self.build_cash_flow_statement)
        self.register(self.sensitivity_analysis)
        self.register(self.scenario_analysis)
        self.register(self.format_financial_data)
        self.register(self.validate_model_consistency)

    def calculate_dcf(self, cash_flows: List[float], discount_rate: float) -> str:
        """
        Calculate Discounted Cash Flow analysis.
        
        Args:
            cash_flows: List of projected cash flows, starting with initial investment (negative)
            discount_rate: Annual discount rate (decimal, e.g., 0.08 for 8%)
            
        Returns:
            JSON string containing the DCF analysis results
        """
        logger.info(f"Calculating DCF with cash flows: {cash_flows} and discount rate: {discount_rate}")
        result = {
            "inputs": {
                "cash_flows": cash_flows,
                "discount_rate": discount_rate
            },
            "discounted_cash_flows": [],
            "cumulative_dcf": [],
            "npv": 0
        }
        
        # Calculate discounted cash flows
        for i, cf in enumerate(cash_flows):
            discounted_cf = cf / ((1 + discount_rate) ** i)
            result["discounted_cash_flows"].append(round(discounted_cf, 2))
            
        # Calculate cumulative DCF
        cumulative = 0
        for dcf in result["discounted_cash_flows"]:
            cumulative += dcf
            result["cumulative_dcf"].append(round(cumulative, 2))
            
        # Calculate NPV
        result["npv"] = round(npf.npv(discount_rate, cash_flows), 2)
        
        return json.dumps(result)
    
    def calculate_irr(self, cash_flows: List[float]) -> str:
        """
        Calculate Internal Rate of Return.
        
        Args:
            cash_flows: List of cash flows, starting with initial investment (negative)
            
        Returns:
            JSON string containing the IRR analysis results
        """
        logger.info(f"Calculating IRR with cash flows: {cash_flows}")
        try:
            irr = npf.irr(cash_flows)
            result = {
                "inputs": {"cash_flows": cash_flows},
                "irr": round(irr * 100, 2),  # Convert to percentage
                "success": True
            }
        except Exception as e:
            logger.warning(f"IRR calculation failed: {e}")
            result = {
                "inputs": {"cash_flows": cash_flows},
                "irr": None,
                "success": False,
                "error": str(e)
            }
        
        return json.dumps(result)
    
    def calculate_payback_period(self, cash_flows: List[float]) -> str:
        """
        Calculate the payback period for an investment.
        
        Args:
            cash_flows: List of cash flows, starting with initial investment (negative)
            
        Returns:
            JSON string with payback period information
        """
        logger.info(f"Calculating payback period with cash flows: {cash_flows}")
        if cash_flows[0] >= 0:
            result = {"error": "First cash flow should be negative (initial investment)"}
            return json.dumps(result)
            
        cumulative = 0
        for i, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= 0:
                # Calculate exact payback period with interpolation if needed
                if i > 0 and cumulative - cf < 0:
                    # Calculate fraction of year
                    previous_cf = cumulative - cf
                    fraction = abs(previous_cf) / cf
                    payback = i - 1 + fraction
                else:
                    payback = i
                    
                result = {
                    "payback_period": round(payback, 2),
                    "cumulative_cash_flows": [round(sum(cash_flows[:i+1]), 2) for i in range(len(cash_flows))]
                }
                return json.dumps(result)
                
        # If we never reach a positive cumulative cash flow
        result = {
            "payback_period": None,
            "cumulative_cash_flows": [round(sum(cash_flows[:i+1]), 2) for i in range(len(cash_flows))],
            "message": "Investment does not reach payback within the given time period"
        }
        return json.dumps(result)
    
    def build_income_statement(self, 
                              revenue: List[float], 
                              cogs: List[float], 
                              operating_expenses: List[float],
                              taxes: List[float],
                              periods: List[str]) -> str:
        """
        Build a structured income statement.
        
        Args:
            revenue: List of revenue figures for each period
            cogs: List of cost of goods sold for each period
            operating_expenses: List of operating expenses for each period
            taxes: List of taxes for each period
            periods: List of period labels (e.g., "Year 1", "Year 2", etc.)
            
        Returns:
            JSON string containing the income statement data
        """
        logger.info(f"Building income statement for {len(periods)} periods")
        # Validate that all lists have the same length
        if not (len(revenue) == len(cogs) == len(operating_expenses) == len(taxes) == len(periods)):
            result = {"error": "All input lists must have the same length"}
            return json.dumps(result)
            
        income_statement = {
            "periods": periods,
            "revenue": [round(r, 2) for r in revenue],
            "cogs": [round(c, 2) for c in cogs],
            "gross_profit": [round(r - c, 2) for r, c in zip(revenue, cogs)],
            "gross_margin_percent": [round((r - c) / r * 100, 2) if r > 0 else 0 for r, c in zip(revenue, cogs)],
            "operating_expenses": [round(e, 2) for e in operating_expenses],
            "operating_income": [round(r - c - e, 2) for r, c, e in zip(revenue, cogs, operating_expenses)],
            "operating_margin_percent": [round((r - c - e) / r * 100, 2) if r > 0 else 0 for r, c, e in zip(revenue, cogs, operating_expenses)],
            "taxes": [round(t, 2) for t in taxes],
            "net_income": [round(r - c - e - t, 2) for r, c, e, t in zip(revenue, cogs, operating_expenses, taxes)],
            "net_margin_percent": [round((r - c - e - t) / r * 100, 2) if r > 0 else 0 for r, c, e, t in zip(revenue, cogs, operating_expenses, taxes)]
        }
        
        return json.dumps(income_statement)
    
    def build_cash_flow_statement(self,
                                 net_income: List[float],
                                 depreciation: List[float],
                                 changes_in_working_capital: List[float],
                                 capital_expenditures: List[float],
                                 financing_cash_flows: List[float],
                                 periods: List[str]) -> str:
        """
        Build a structured cash flow statement.
        
        Args:
            net_income: List of net income figures for each period
            depreciation: List of depreciation figures for each period
            changes_in_working_capital: List of changes in working capital
            capital_expenditures: List of capital expenditures (negative values)
            financing_cash_flows: List of financing cash flows
            periods: List of period labels
            
        Returns:
            JSON string containing the cash flow statement data
        """
        logger.info(f"Building cash flow statement for {len(periods)} periods")
        # Validate that all lists have the same length
        if not (len(net_income) == len(depreciation) == len(changes_in_working_capital) == 
                len(capital_expenditures) == len(financing_cash_flows) == len(periods)):
            result = {"error": "All input lists must have the same length"}
            return json.dumps(result)
            
        cash_flow_statement = {
            "periods": periods,
            "net_income": [round(ni, 2) for ni in net_income],
            "depreciation": [round(d, 2) for d in depreciation],
            "changes_in_working_capital": [round(wc, 2) for wc in changes_in_working_capital],
            "operating_cash_flow": [round(ni + d + wc, 2) for ni, d, wc in zip(net_income, depreciation, changes_in_working_capital)],
            "capital_expenditures": [round(capex, 2) for capex in capital_expenditures],
            "investing_cash_flow": [round(capex, 2) for capex in capital_expenditures],
            "financing_cash_flows": [round(fcf, 2) for fcf in financing_cash_flows],
            "net_cash_flow": [round(ni + d + wc + capex + fcf, 2) for ni, d, wc, capex, fcf in 
                             zip(net_income, depreciation, changes_in_working_capital, capital_expenditures, financing_cash_flows)]
        }
        
        # Calculate cumulative cash flow
        cumulative = 0
        cash_flow_statement["cumulative_cash_flow"] = []
        for ncf in cash_flow_statement["net_cash_flow"]:
            cumulative += ncf
            cash_flow_statement["cumulative_cash_flow"].append(round(cumulative, 2))
            
        return json.dumps(cash_flow_statement)
    
    def sensitivity_analysis(self, 
                            base_case_npv: float,
                            variables: List[str],
                            change_percentages: List[int],
                            npv_results: List[List[float]]) -> str:
        """
        Format sensitivity analysis results.
        
        Args:
            base_case_npv: The NPV of the base case
            variables: List of variable names that were modified
            change_percentages: List of percentage changes applied (e.g., [-20, -10, 0, 10, 20])
            npv_results: 2D list of NPV results for each variable and each percentage change
            
        Returns:
            JSON string containing the sensitivity analysis results
        """
        logger.info(f"Performing sensitivity analysis on {len(variables)} variables")
        if len(variables) != len(npv_results):
            result = {"error": "Number of variables must match number of NPV result rows"}
            return json.dumps(result)
            
        for row in npv_results:
            if len(row) != len(change_percentages):
                result = {"error": "Each NPV result row must have the same length as change_percentages"}
                return json.dumps(result)
                
        sensitivity = {
            "base_case_npv": base_case_npv,
            "variables": variables,
            "change_percentages": change_percentages,
            "npv_results": npv_results,
            "percentage_changes": []
        }
        
        # Calculate percentage changes from base case
        for var_idx, variable_results in enumerate(npv_results):
            var_changes = []
            for res in variable_results:
                if base_case_npv != 0:
                    pct_change = round((res - base_case_npv) / abs(base_case_npv) * 100, 2)
                else:
                    pct_change = float('inf') if res > 0 else float('-inf') if res < 0 else 0
                var_changes.append(pct_change)
            sensitivity["percentage_changes"].append(var_changes)
            
        return json.dumps(sensitivity)
    
    def scenario_analysis(self,
                         scenario_names: List[str], 
                         revenue_projections: List[List[float]],
                         cost_projections: List[List[float]],
                         operating_expenses_projections: List[List[float]],
                         tax_projections: List[List[float]],
                         discount_rates: List[float],
                         periods: List[str],
                         initial_investment: float = 0) -> str:
        """
        Compare different scenarios (e.g., bull, bear, baseline).
        
        Args:
            scenario_names: Names of the scenarios
            revenue_projections: List of revenue projections for each scenario
            cost_projections: List of cost projections for each scenario (COGS)
            operating_expenses_projections: List of operating expenses for each scenario
            tax_projections: List of tax expenses for each scenario
            discount_rates: List of discount rates for each scenario
            periods: List of period labels
            initial_investment: Optional initial investment amount (negative number)
            
        Returns:
            JSON string containing the scenario analysis results
        """
        logger.info(f"Analyzing {len(scenario_names)} scenarios over {len(periods)} periods")
        if not (len(scenario_names) == len(revenue_projections) == len(cost_projections) == 
                len(operating_expenses_projections) == len(tax_projections) == len(discount_rates)):
            result = {"error": "Number of scenarios must be consistent across all inputs"}
            return json.dumps(result)
            
        for rev_proj in revenue_projections:
            if len(rev_proj) != len(periods):
                result = {"error": "Each revenue projection must match the number of periods"}
                return json.dumps(result)
                
        for cost_proj in cost_projections:
            if len(cost_proj) != len(periods):
                result = {"error": "Each cost projection must match the number of periods"}
                return json.dumps(result)
                
        for opex_proj in operating_expenses_projections:
            if len(opex_proj) != len(periods):
                result = {"error": "Each operating expense projection must match the number of periods"}
                return json.dumps(result)
                
        for tax_proj in tax_projections:
            if len(tax_proj) != len(periods):
                result = {"error": "Each tax projection must match the number of periods"}
                return json.dumps(result)
                
        scenarios = {
            "scenario_names": scenario_names,
            "periods": periods,
            "revenue_projections": revenue_projections,
            "cost_projections": cost_projections,
            "operating_expense_projections": operating_expenses_projections,
            "tax_projections": tax_projections,
            "gross_profit_projections": [],  # Revenue - COGS
            "net_income_projections": [],    # Revenue - COGS - OpEx - Taxes = Net Income
            "discount_rates": discount_rates,
            "npv_results": [],
            "irr_results": [],
            "cash_flows": [],  # Store complete cash flows including initial investment
            "payback_periods": []
        }
        
        # Calculate profit projections for each scenario
        for i, scenario in enumerate(scenario_names):
            # Calculate Gross Profit (Revenue - COGS)
            gross_profits = [round(rev - cost, 2) for rev, cost in zip(revenue_projections[i], cost_projections[i])]
            scenarios["gross_profit_projections"].append(gross_profits)
            
            # Calculate Net Income (Revenue - COGS - OpEx - Taxes)
            net_income = [
                round(rev - cost - opex - tax, 2) 
                for rev, cost, opex, tax in zip(
                    revenue_projections[i], 
                    cost_projections[i], 
                    operating_expenses_projections[i],
                    tax_projections[i]
                )
            ]
            scenarios["net_income_projections"].append(net_income)
            
            # Create full cash flow including initial investment
            # We use net_income as the annual cash flows (this is a simplification)
            cash_flow = [initial_investment] + net_income
            scenarios["cash_flows"].append(cash_flow)
            
            # Calculate NPV
            try:
                # Calculate using the full cash flows
                npv = round(npf.npv(discount_rates[i], cash_flow[1:]), 2) + cash_flow[0]
                scenarios["npv_results"].append(npv)
            except Exception as e:
                logger.warning(f"NPV calculation failed for scenario {scenario}: {e}")
                scenarios["npv_results"].append(None)
                
            # Calculate IRR
            try:
                # Use the full cash flow for IRR
                irr = round(npf.irr(cash_flow) * 100, 2)  # Convert to percentage
                scenarios["irr_results"].append(irr)
            except Exception as e:
                logger.warning(f"IRR calculation failed for scenario {scenario}: {e}")
                scenarios["irr_results"].append(None)
                
            # Calculate payback period
            try:
                cumulative = 0
                payback_period = None
                for j, cf in enumerate(cash_flow):
                    cumulative += cf
                    if cumulative >= 0:
                        # Calculate exact payback period with interpolation if needed
                        if j > 0 and cumulative - cf < 0:
                            # Calculate fraction of year
                            previous_cf = cumulative - cf
                            fraction = abs(previous_cf) / cf
                            payback_period = j - 1 + fraction
                        else:
                            payback_period = j
                        break
                
                if payback_period is not None:
                    scenarios["payback_periods"].append(round(payback_period, 2))
                else:
                    scenarios["payback_periods"].append(None)
            except Exception as e:
                logger.warning(f"Payback period calculation failed for scenario {scenario}: {e}")
                scenarios["payback_periods"].append(None)
                
        return json.dumps(scenarios)
    
    def format_financial_data(self, data: str, format_type: str = "json") -> str:
        """
        Format financial data in the requested format.
        
        Args:
            data: JSON string containing financial data
            format_type: Output format type ("json", "csv", or "markdown")
            
        Returns:
            Formatted string representation of the financial data
        """
        logger.info(f"Formatting financial data as {format_type}")
        
        # Parse the JSON string back to a dictionary
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return f"Error parsing data as JSON: {data}"
                
        if format_type == "json":
            return json.dumps(data, indent=2)
            
        elif format_type == "markdown":
            # Create a markdown table
            md_output = ""
            
            # Handle different types of data structures
            if "periods" in data:
                # Financial statement style data
                headers = ["Metric"] + data["periods"]
                md_output += "| " + " | ".join(headers) + " |\n"
                md_output += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                for key, values in data.items():
                    if key != "periods" and isinstance(values, list):
                        if all(isinstance(v, (int, float)) for v in values):
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([f"${v:,.2f}" for v in values]) + " |\n"
                        else:
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([str(v) for v in values]) + " |\n"
                        
            elif "scenario_names" in data:
                # Scenario analysis data
                headers = ["Metric"] + data["scenario_names"]
                md_output += "| " + " | ".join(headers) + " |\n"
                md_output += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                # Add NPV and IRR rows
                if "npv_results" in data:
                    npv_values = [f"${v:,.2f}" if v is not None else "N/A" for v in data["npv_results"]]
                    md_output += f"| NPV | " + " | ".join(npv_values) + " |\n"
                    
                if "irr_results" in data:
                    irr_values = [f"{v:.2%}" if v is not None else "N/A" for v in data["irr_results"]]
                    md_output += f"| IRR (%) | " + " | ".join(irr_values) + " |\n"
                
                # Add payback periods if available
                if "payback_periods" in data:
                    pb_values = [f"{v} years" if v is not None else "N/A" for v in data["payback_periods"]]
                    md_output += f"| Payback Period (years) | " + " | ".join(pb_values) + " |\n"
                
                # Add period-by-period net income projections
                if "net_income_projections" in data and "periods" in data:
                    for i, period in enumerate(data["periods"]):
                        if i < len(data["net_income_projections"][0]):  # Make sure we have this period
                            income_values = [f"${incomes[i]:,.2f}" if isinstance(incomes[i], (int, float)) else str(incomes[i]) 
                                            for incomes in data["net_income_projections"]]
                            md_output += f"| Net Income {period} | " + " | ".join(income_values) + " |\n"
                # Fall back to profit_projections for backward compatibility        
                elif "profit_projections" in data and "periods" in data:
                    for i, period in enumerate(data["periods"]):
                        if i < len(data["profit_projections"][0]):  # Make sure we have this period
                            profit_values = [f"${profits[i]:,.2f}" if isinstance(profits[i], (int, float)) else str(profits[i])
                                            for profits in data["profit_projections"]]
                            md_output += f"| Profit {period} | " + " | ".join(profit_values) + " |\n"
                    
            else:
                # Generic data
                for key, value in data.items():
                    if isinstance(value, list):
                        md_output += f"\n### {key.replace('_', ' ').title()}\n\n"
                        if all(isinstance(x, (int, float)) for x in value):
                            md_output += ", ".join([f"${v:,.2f}" if isinstance(v, (int, float)) else str(v) for v in value]) + "\n"
                        else:
                            for v in value:
                                md_output += f"- {v}\n"
                    elif isinstance(value, dict):
                        md_output += f"\n### {key.replace('_', ' ').title()}\n\n"
                        for k, v in value.items():
                            if isinstance(v, (int, float)):
                                md_output += f"- **{k.replace('_', ' ').title()}**: ${v:,.2f}\n"
                            else:
                                md_output += f"- **{k.replace('_', ' ').title()}**: {v}\n"
                    else:
                        if isinstance(value, (int, float)):
                            md_output += f"\n### {key.replace('_', ' ').title()}\n\n${value:,.2f}\n"
                        else:
                            md_output += f"\n### {key.replace('_', ' ').title()}\n\n{value}\n"
                
            return md_output
                
        elif format_type == "csv":
            # Create CSV-formatted string
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Handle different types of data structures
            if "periods" in data:
                # Financial statement style data
                writer.writerow(["Metric"] + data["periods"])
                for key, values in data.items():
                    if key != "periods" and isinstance(values, list):
                        writer.writerow([key.replace('_', ' ').title()] + values)
                        
            elif "scenario_names" in data:
                # Scenario analysis data
                writer.writerow(["Metric"] + data["scenario_names"])
                writer.writerow(["NPV"] + data["npv_results"])
                writer.writerow(["IRR (%)"] + data["irr_results"])
                
                # Add payback periods if available
                if "payback_periods" in data:
                    writer.writerow(["Payback Period (years)"] + data["payback_periods"])
                
                # Add period-by-period net income projections
                if "net_income_projections" in data and "periods" in data:
                    for i, period in enumerate(data["periods"]):
                        income_values = [incomes[i] for incomes in data["net_income_projections"]]
                        writer.writerow([f"Net Income {period}"] + income_values)
                # Fall back to profit_projections for backward compatibility        
                elif "profit_projections" in data and "periods" in data:
                    for i, period in enumerate(data["periods"]):
                        profit_values = [profits[i] for profits in data["profit_projections"]]
                        writer.writerow([f"Profit {period}"] + profit_values)
                
            else:
                # Generic data
                for key, value in data.items():
                    if isinstance(value, list):
                        if all(isinstance(x, (int, float)) for x in value):
                            writer.writerow([key.replace('_', ' ').title()] + value)
                        else:
                            writer.writerow([key.replace('_', ' ').title()])
                            for v in value:
                                writer.writerow(["", v])
                    elif isinstance(value, dict):
                        writer.writerow([key.replace('_', ' ').title()])
                        for k, v in value.items():
                            writer.writerow(["", k.replace('_', ' ').title(), v])
                    else:
                        writer.writerow([key.replace('_', ' ').title(), value])
                
            return output.getvalue()
            
        else:
            return f"Unsupported format type: {format_type}"
            
    def validate_model_consistency(self, 
                                  income_statement: str, 
                                  cash_flow_statement: str, 
                                  scenario_analysis: str,
                                  baseline_scenario_index: int = 1) -> str:
        """
        Validate that the model is internally consistent across statements and scenarios.
        
        Args:
            income_statement: Income statement JSON string
            cash_flow_statement: Cash flow statement JSON string
            scenario_analysis: Scenario analysis JSON string
            baseline_scenario_index: Index of the baseline scenario (default: 1, usually the middle scenario)
            
        Returns:
            A report of consistency checks
        """
        logger.info("Validating model consistency")
        
        try:
            # Parse the JSON strings
            income_data = json.loads(income_statement) if isinstance(income_statement, str) else income_statement
            cash_flow_data = json.loads(cash_flow_statement) if isinstance(cash_flow_statement, str) else cash_flow_statement
            scenario_data = json.loads(scenario_analysis) if isinstance(scenario_analysis, str) else scenario_analysis
            
            # Prepare results
            validation_results = {
                "consistent": True,
                "issues": [],
                "warnings": [],
                "recommended_key_metrics": {}
            }
            
            # Check 1: Net income consistency between income statement and cash flow statement
            if ("net_income" in income_data and "net_income" in cash_flow_data and 
                len(income_data["net_income"]) == len(cash_flow_data["net_income"])):
                
                for i, (income_ni, cash_flow_ni) in enumerate(zip(income_data["net_income"], cash_flow_data["net_income"])):
                    if abs(income_ni - cash_flow_ni) > 0.01:  # Allow for minor rounding differences
                        validation_results["consistent"] = False
                        validation_results["issues"].append(
                            f"Net income mismatch between income statement (${income_ni}) and "
                            f"cash flow statement (${cash_flow_ni}) for period {i+1}"
                        )
            else:
                validation_results["warnings"].append("Could not compare net income between statements")
            
            # Check 2: Net income consistency between income statement and scenario analysis (baseline)
            if ("net_income" in income_data and "net_income_projections" in scenario_data and 
                "scenario_names" in scenario_data and baseline_scenario_index < len(scenario_data["scenario_names"])):
                
                baseline_net_income = scenario_data["net_income_projections"][baseline_scenario_index]
                income_statement_net_income = income_data["net_income"]
                
                # Check if lengths match
                if len(baseline_net_income) == len(income_statement_net_income):
                    for i, (baseline_ni, income_ni) in enumerate(zip(baseline_net_income, income_statement_net_income)):
                        if abs(baseline_ni - income_ni) > 0.01:  # Allow for minor rounding differences
                            validation_results["consistent"] = False
                            validation_results["issues"].append(
                                f"Net income mismatch between income statement (${income_ni}) and "
                                f"baseline scenario (${baseline_ni}) for period {i+1}"
                            )
                else:
                    validation_results["warnings"].append(
                        f"Net income periods mismatch: Income statement has {len(income_statement_net_income)} periods, "
                        f"but baseline scenario has {len(baseline_net_income)} periods"
                    )
            elif "profit_projections" in scenario_data:  # Backward compatibility
                validation_results["warnings"].append(
                    "Using 'profit_projections' in scenario analysis instead of 'net_income_projections'. "
                    "Make sure these values represent net income, not gross profit."
                )
            
            # Check 3: Scenario analysis vs cash flow statement
            if "scenario_names" in scenario_data and baseline_scenario_index < len(scenario_data["scenario_names"]):
                baseline_name = scenario_data["scenario_names"][baseline_scenario_index]
                
                # Get NPV, IRR for baseline scenario
                baseline_npv = scenario_data["npv_results"][baseline_scenario_index] if "npv_results" in scenario_data else None
                baseline_irr = scenario_data["irr_results"][baseline_scenario_index] if "irr_results" in scenario_data else None
                
                # Add recommended key metrics
                validation_results["recommended_key_metrics"] = {
                    "npv": baseline_npv,
                    "irr": baseline_irr
                }
                
                # Get payback period if available directly from scenarios
                if "payback_periods" in scenario_data and len(scenario_data["payback_periods"]) > baseline_scenario_index:
                    baseline_payback = scenario_data["payback_periods"][baseline_scenario_index]
                    if baseline_payback is not None:
                        validation_results["recommended_key_metrics"]["payback_period"] = baseline_payback
                
                # Otherwise calculate payback from cash flows   
                elif "cash_flows" in scenario_data and len(scenario_data["cash_flows"]) > baseline_scenario_index:
                    baseline_cash_flows = scenario_data["cash_flows"][baseline_scenario_index]
                    try:
                        cumulative = 0
                        payback_period = None
                        for i, cf in enumerate(baseline_cash_flows):
                            cumulative += cf
                            if cumulative >= 0:
                                # Calculate exact payback period with interpolation if needed
                                if i > 0 and cumulative - cf < 0:
                                    # Calculate fraction of year
                                    previous_cf = cumulative - cf
                                    fraction = abs(previous_cf) / cf
                                    payback_period = i - 1 + fraction
                                else:
                                    payback_period = i
                                break
                        
                        if payback_period is not None:
                            validation_results["recommended_key_metrics"]["payback_period"] = round(payback_period, 2)
                    except Exception as e:
                        validation_results["warnings"].append(f"Could not calculate payback period: {e}")
                        
                # Check if cash flows can be derived from cash flow statement
                if "net_cash_flow" in cash_flow_data:
                    cash_flow_statement_flows = cash_flow_data["net_cash_flow"]
                    
                    # Check if cash flows from scenario analysis match net cash flows from statement
                    if ("cash_flows" in scenario_data and 
                        len(scenario_data["cash_flows"]) > baseline_scenario_index and 
                        len(scenario_data["cash_flows"][baseline_scenario_index]) > 1):
                        
                        # Skip the initial investment in scenario cash flows
                        scenario_flows = scenario_data["cash_flows"][baseline_scenario_index][1:]
                        
                        # Compare only if we have the same number of periods
                        if len(scenario_flows) == len(cash_flow_statement_flows):
                            for i, (scenario_cf, statement_cf) in enumerate(zip(scenario_flows, cash_flow_statement_flows)):
                                if abs(scenario_cf - statement_cf) > 0.01:  # Allow for minor rounding differences
                                    validation_results["warnings"].append(
                                        f"Cash flow mismatch between scenario analysis (${scenario_cf}) and "
                                        f"cash flow statement (${statement_cf}) for period {i+1}"
                                    )
                        else:
                            validation_results["warnings"].append(
                                f"Cash flow periods mismatch: Cash flow statement has {len(cash_flow_statement_flows)} periods, "
                                f"but scenario analysis has {len(scenario_flows)} periods"
                            )
            else:
                validation_results["warnings"].append("Could not identify baseline scenario")
                
            # Check 4: Ensure scenarios have proper relationships (bull > baseline > bear)
            if ("scenario_names" in scenario_data and "npv_results" in scenario_data and 
                len(scenario_data["scenario_names"]) >= 3 and len(scenario_data["npv_results"]) >= 3):
                
                # Check NPV relationships
                if (scenario_data["npv_results"][0] is not None and 
                    scenario_data["npv_results"][1] is not None and 
                    scenario_data["npv_results"][2] is not None):
                    
                    bear_npv = scenario_data["npv_results"][0]
                    baseline_npv = scenario_data["npv_results"][1]
                    bull_npv = scenario_data["npv_results"][2]
                    
                    if not (bull_npv > baseline_npv > bear_npv):
                        validation_results["warnings"].append(
                            f"Scenario NPVs have unexpected relationship: Bull (${bull_npv}), "
                            f"Baseline (${baseline_npv}), Bear (${bear_npv})"
                        )
                        
            # Summarize validation results
            if validation_results["consistent"]:
                if not validation_results["warnings"]:
                    validation_results["summary"] = "Model is internally consistent. All checks passed."
                else:
                    validation_results["summary"] = "Model appears consistent, but with warnings. See details."
            else:
                validation_results["summary"] = "Model has consistency issues. See details for correction."
                
            return json.dumps(validation_results)
            
        except Exception as e:
            error_result = {
                "consistent": False,
                "error": str(e),
                "summary": "Error occurred during validation."
            }
            return json.dumps(error_result) 