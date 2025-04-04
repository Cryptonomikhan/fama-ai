from agno.tools import Toolkit
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, List, Optional, Any
from agno.utils.log import logger
from src.tools.financial_calculations import FinancialCalculationTools

class ModelFormattingTools(Toolkit):
    """Tools for formatting and visualizing financial model outputs"""
    
    def __init__(self):
        super().__init__(name="model_formatting_tools")
        # Register all the functions
        self.register(self.generate_visualization)
        self.register(self.format_model_summary)
    
    def generate_visualization(self, 
                              data: str, 
                              chart_type: str = "line", 
                              title: str = "Financial Projection",
                              x_label: str = "Period",
                              y_label: str = "Value",
                              series_to_plot: Optional[List[str]] = None) -> str:
        """
        Generate a visualization of financial data.
        
        Args:
            data: JSON string containing financial data
            chart_type: Type of chart to generate ("line", "bar", "stacked_bar", "pie")
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            series_to_plot: List of data series keys to plot (if None, will try to determine automatically)
            
        Returns:
            Base64-encoded image data that can be embedded in markdown
        """
        logger.info(f"Generating {chart_type} visualization: {title}")
        
        # Parse the JSON string back to a dictionary
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return f"Error parsing data as JSON: {data}"
                
        plt.figure(figsize=(10, 6))
        
        if chart_type not in ["line", "bar", "stacked_bar", "pie"]:
            return "Unsupported chart type. Use 'line', 'bar', 'stacked_bar', or 'pie'."
            
        # Setup plot
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        
        # Determine what to plot based on data structure
        if "periods" in data:
            # Financial statement data
            periods = data["periods"]
            
            # Determine which series to plot
            if series_to_plot is None:
                # Automatically select important metrics
                possible_metrics = ["revenue", "net_income", "operating_income", "cash_flow", 
                                   "net_cash_flow", "cumulative_cash_flow"]
                series_to_plot = [metric for metric in possible_metrics if metric in data]
                
                # If none found, just use all numeric series
                if not series_to_plot:
                    series_to_plot = [key for key, values in data.items() 
                                     if key != "periods" and isinstance(values, list) 
                                     and all(isinstance(v, (int, float)) for v in values)]
            
            # Create DataFrame for plotting
            plot_data = {period: [] for period in periods}
            plot_data["Metric"] = []
            
            for metric in series_to_plot:
                if metric in data and isinstance(data[metric], list):
                    plot_data["Metric"].append(metric.replace('_', ' ').title())
                    for i, period in enumerate(periods):
                        if i < len(data[metric]):
                            plot_data[period].append(data[metric][i])
                        else:
                            plot_data[period].append(0)  # Handle missing data
            
            df = pd.DataFrame(plot_data)
            df = df.set_index("Metric")
            
            # Generate the appropriate chart
            if chart_type == "line":
                df.T.plot(kind='line', ax=plt.gca())
            elif chart_type == "bar":
                df.T.plot(kind='bar', ax=plt.gca())
            elif chart_type == "stacked_bar":
                df.T.plot(kind='bar', stacked=True, ax=plt.gca())
            elif chart_type == "pie" and len(periods) > 0:
                # For pie charts, we use the last period by default
                df[periods[-1]].plot(kind='pie', ax=plt.gca(), autopct='%1.1f%%')
                plt.ylabel('')  # Remove y-label for pie charts
                
        elif "scenario_names" in data and "profit_projections" in data:
            # Scenario analysis data
            scenarios = data["scenario_names"]
            periods = data["periods"]
            
            if chart_type == "line":
                # Line chart comparing scenarios over time
                for i, scenario in enumerate(scenarios):
                    plt.plot(periods, data["profit_projections"][i], label=scenario)
                plt.legend()
                
            elif chart_type == "bar":
                # Bar chart for final outcomes (NPV/IRR)
                if "npv_results" in data:
                    plt.bar(scenarios, data["npv_results"])
                    plt.title(f"{title} - NPV by Scenario")
                    
            elif chart_type == "pie":
                # Pie chart of NPV distribution
                if "npv_results" in data:
                    # Filter out negative values for pie chart
                    pos_scenarios = []
                    pos_values = []
                    for i, val in enumerate(data["npv_results"]):
                        if val is not None and val > 0:
                            pos_scenarios.append(scenarios[i])
                            pos_values.append(val)
                    
                    if pos_values:
                        plt.pie(pos_values, labels=pos_scenarios, autopct='%1.1f%%')
                        plt.title(f"{title} - NPV Distribution")
                    else:
                        return "No positive NPV values for pie chart"
        else:
            return "Data format not supported for visualization"
            
        # Add grid and formatting
        if chart_type != "pie":
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
        
        # Save the figure to a base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        # Return markdown-compatible image tag
        return f"![{title}](data:image/png;base64,{image_data})"
    
    def format_model_summary(self, 
                             model_name: str,
                             income_statement: str,
                             cash_flow_statement: str,
                             scenario_analysis: str,
                             key_metrics: str,
                             format_type: str = "markdown") -> str:
        """
        Format a comprehensive model summary.
        
        Args:
            model_name: Name of the financial model
            income_statement: Income statement data as JSON string
            cash_flow_statement: Cash flow statement data as JSON string
            scenario_analysis: Scenario analysis data as JSON string
            key_metrics: Dictionary of key metrics as JSON string
            format_type: Output format ("markdown", "json", or "csv")
            
        Returns:
            Formatted model summary
        """
        logger.info(f"Formatting model summary '{model_name}' as {format_type}")
        
        # Parse JSON strings to dictionaries
        try:
            income_statement = json.loads(income_statement) if isinstance(income_statement, str) else income_statement
            cash_flow_statement = json.loads(cash_flow_statement) if isinstance(cash_flow_statement, str) else cash_flow_statement
            scenario_analysis = json.loads(scenario_analysis) if isinstance(scenario_analysis, str) else scenario_analysis
            key_metrics = json.loads(key_metrics) if isinstance(key_metrics, str) else key_metrics
        except json.JSONDecodeError as e:
            return f"Error parsing input data as JSON: {e}"
        
        # Compile all data into a summary structure
        summary = {
            "model_name": model_name,
            "key_metrics": key_metrics,
            "income_statement": income_statement,
            "cash_flow_statement": cash_flow_statement,
            "scenario_analysis": scenario_analysis
        }
        
        if format_type == "json":
            return json.dumps(summary, indent=2)
            
        elif format_type == "csv":
            # For CSV, we'll create sections with blank rows between them
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Model header
            writer.writerow([model_name])
            writer.writerow([])  # Blank row
            
            # Key Metrics
            writer.writerow(["KEY METRICS"])
            for key, value in key_metrics.items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])  # Blank row
            
            # Income Statement
            if "periods" in income_statement:
                writer.writerow(["INCOME STATEMENT"])
                writer.writerow(["Metric"] + income_statement["periods"])
                for key, values in income_statement.items():
                    if key != "periods" and isinstance(values, list):
                        writer.writerow([key.replace('_', ' ').title()] + values)
                writer.writerow([])  # Blank row
            
            # Cash Flow Statement
            if "periods" in cash_flow_statement:
                writer.writerow(["CASH FLOW STATEMENT"])
                writer.writerow(["Metric"] + cash_flow_statement["periods"])
                for key, values in cash_flow_statement.items():
                    if key != "periods" and isinstance(values, list):
                        writer.writerow([key.replace('_', ' ').title()] + values)
                writer.writerow([])  # Blank row
            
            # Scenario Analysis
            if "scenario_names" in scenario_analysis:
                writer.writerow(["SCENARIO ANALYSIS"])
                writer.writerow(["Metric"] + scenario_analysis["scenario_names"])
                
                if "npv_results" in scenario_analysis:
                    writer.writerow(["NPV"] + scenario_analysis["npv_results"])
                if "irr_results" in scenario_analysis:
                    writer.writerow(["IRR (%)"] + scenario_analysis["irr_results"])
                
                writer.writerow([])  # Blank row
                
            return output.getvalue()
            
        else:  # Default to markdown
            md_output = f"# {model_name}\n\n"
            
            # Key Metrics
            md_output += "## Key Metrics\n\n"
            metrics_table = "| Metric | Value |\n| --- | --- |\n"
            for key, value in key_metrics.items():
                if key.lower() == "irr":
                    # Format IRR as percentage
                    metrics_table += f"| {key.upper()} | {value:.2%} |\n"
                elif isinstance(value, (int, float)):
                    # Format monetary values with $ and commas
                    metrics_table += f"| {key.upper()} | ${value:,.2f} |\n"
                else:
                    metrics_table += f"| {key.upper()} | {value} |\n"
            md_output += metrics_table + "\n"
            
            # Income Statement
            if "periods" in income_statement:
                md_output += "\n## Income Statement\n\n"
                headers = ["Item"] + income_statement["periods"]
                md_output += "| " + " | ".join(headers) + " |\n"
                md_output += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                # Include important metrics first
                key_income_metrics = ["revenue", "gross_profit", "operating_income", "net_income", 
                                    "gross_margin_percent", "operating_margin_percent", "net_margin_percent"]
                
                for metric in key_income_metrics:
                    if metric in income_statement:
                        values = income_statement[metric]
                        if all(isinstance(v, (int, float)) for v in values):
                            md_output += f"| {metric.replace('_', ' ').title()} | " + " | ".join([f"${v:,.2f}" for v in values]) + " |\n"
                        else:
                            md_output += f"| {metric.replace('_', ' ').title()} | " + " | ".join([str(v) for v in values]) + " |\n"
                
                # Include remaining metrics
                for key, values in income_statement.items():
                    if key != "periods" and isinstance(values, list) and key not in key_income_metrics:
                        if all(isinstance(v, (int, float)) for v in values):
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([f"${v:,.2f}" for v in values]) + " |\n"
                        else:
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([str(v) for v in values]) + " |\n"
            
            # Cash Flow Statement
            if "periods" in cash_flow_statement:
                md_output += "\n## Cash Flow Statement\n\n"
                headers = ["Item"] + cash_flow_statement["periods"]
                md_output += "| " + " | ".join(headers) + " |\n"
                md_output += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                # Include important metrics first
                key_cf_metrics = ["operating_cash_flow", "investing_cash_flow", "financing_cash_flows", 
                                "net_cash_flow", "cumulative_cash_flow"]
                
                for metric in key_cf_metrics:
                    if metric in cash_flow_statement:
                        values = cash_flow_statement[metric]
                        if all(isinstance(v, (int, float)) for v in values):
                            md_output += f"| {metric.replace('_', ' ').title()} | " + " | ".join([f"${v:,.2f}" for v in values]) + " |\n"
                        else:
                            md_output += f"| {metric.replace('_', ' ').title()} | " + " | ".join([str(v) for v in values]) + " |\n"
                
                # Include remaining metrics
                for key, values in cash_flow_statement.items():
                    if key != "periods" and isinstance(values, list) and key not in key_cf_metrics:
                        if all(isinstance(v, (int, float)) for v in values):
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([f"${v:,.2f}" for v in values]) + " |\n"
                        else:
                            md_output += f"| {key.replace('_', ' ').title()} | " + " | ".join([str(v) for v in values]) + " |\n"
            
            # Scenario Analysis
            if "scenario_names" in scenario_analysis:
                md_output += "\n## Scenario Analysis\n\n"
                
                # Create a table for scenario metrics
                md_output += "| Metric | " + " | ".join(scenario_analysis["scenario_names"]) + " |\n"
                md_output += "| --- | " + " | ".join(["---"] * len(scenario_analysis["scenario_names"])) + " |\n"
                
                # NPV and IRR
                if "npv_results" in scenario_analysis:
                    npv_values = [f"${v:,.2f}" if v is not None else "N/A" for v in scenario_analysis["npv_results"]]
                    md_output += f"| NPV | " + " | ".join(npv_values) + " |\n"
                    
                if "irr_results" in scenario_analysis:
                    irr_values = [f"{v:.2%}" if v is not None else "N/A" for v in scenario_analysis["irr_results"]]
                    md_output += f"| IRR | " + " | ".join(irr_values) + " |\n"
                    
                if "payback_periods" in scenario_analysis:
                    pb_values = [f"{v} years" if v is not None else "N/A" for v in scenario_analysis["payback_periods"]]
                    md_output += f"| Payback Period | " + " | ".join(pb_values) + " |\n"
                
                # Net income projections by year
                if "net_income_projections" in scenario_analysis and "periods" in scenario_analysis:
                    for i, period in enumerate(scenario_analysis["periods"]):
                        if i < len(scenario_analysis["net_income_projections"][0]):  # Make sure we have this period
                            income_values = [f"${incomes[i]:,.2f}" if isinstance(incomes[i], (int, float)) else incomes[i] 
                                             for incomes in scenario_analysis["net_income_projections"]]
                            md_output += f"| Net Income {period} | " + " | ".join(income_values) + " |\n"
            
            return md_output 