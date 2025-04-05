from agno.agent import Agent
from agno.tools import tool
import numpy_financial as npf
import json
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, List, Optional, Any
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Simple logging for tool execution
def log_tool_execution(fc):
    """Simple log function that runs before tool execution"""
    print(f"Executing tool: {fc.function.__name__} with args: {fc.arguments}")

@tool(pre_hook=log_tool_execution)
def calculate_dcf(cash_flows: List[float], discount_rate: float) -> Dict:
    """
    Calculate Discounted Cash Flow analysis.
    
    Args:
        cash_flows: List of projected cash flows, starting with initial investment (negative)
        discount_rate: Annual discount rate (decimal, e.g., 0.08 for 8%)
        
    Returns:
        Dictionary containing the DCF analysis results
    """
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
    
    return result

@tool(pre_hook=log_tool_execution)
def calculate_irr(cash_flows: List[float]) -> Dict:
    """
    Calculate Internal Rate of Return.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        
    Returns:
        Dictionary containing the IRR analysis results
    """
    try:
        irr = npf.irr(cash_flows)
        return {
            "inputs": {"cash_flows": cash_flows},
            "irr": round(irr * 100, 2),  # Convert to percentage
            "success": True
        }
    except Exception as e:
        return {
            "inputs": {"cash_flows": cash_flows},
            "irr": None,
            "success": False,
            "error": str(e)
        }

@tool(
    name="visualize_cash_flows",
    description="Generate a visualization of cash flows",
    pre_hook=log_tool_execution
)
def generate_cash_flow_visualization(
    cash_flows: List[float], 
    discounted_cash_flows: Optional[List[float]] = None,
    title: str = "Cash Flow Analysis"
) -> str:
    """
    Generate a bar chart visualization of cash flows.
    
    Args:
        cash_flows: Original cash flows
        discounted_cash_flows: Discounted cash flows (optional)
        title: Chart title
        
    Returns:
        Base64-encoded image data that can be embedded in markdown
    """
    plt.figure(figsize=(10, 6))
    plt.title(title)
    
    x = range(len(cash_flows))
    years = [f"Year {i}" for i in range(len(cash_flows))]
    
    plt.bar(x, cash_flows, alpha=0.7, label="Cash Flows")
    
    if discounted_cash_flows:
        plt.bar([i + 0.3 for i in x], discounted_cash_flows, alpha=0.7, label="Discounted Cash Flows")
    
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    plt.xticks(x, years)
    plt.ylabel("Amount")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the figure to a base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_data = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    # Return markdown-compatible image tag
    return f"![{title}](data:image/png;base64,{image_data})"

@tool(
    name="payback_period_calculator",
    description="Calculate the payback period for an investment",
    pre_hook=log_tool_execution,
    cache_results=True  # Enable caching for this function
)
def calculate_payback_period(cash_flows: List[float]) -> Dict:
    """
    Calculate the payback period for an investment.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        
    Returns:
        Dictionary with payback period information
    """
    if cash_flows[0] >= 0:
        return {"error": "First cash flow should be negative (initial investment)"}
        
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
                
            return {
                "payback_period": round(payback, 2),
                "cumulative_cash_flows": [round(sum(cash_flows[:i+1]), 2) for i in range(len(cash_flows))]
            }
            
    # If we never reach a positive cumulative cash flow
    return {
        "payback_period": None,
        "cumulative_cash_flows": [round(sum(cash_flows[:i+1]), 2) for i in range(len(cash_flows))],
        "message": "Investment does not reach payback within the given time period"
    }

@tool(
    stop_after_tool_call=True  # Stop agent execution after this tool call
)
def format_investment_summary(
    npv: float, 
    irr: float, 
    payback_period: float, 
    format_type: str = "markdown"
) -> str:
    """
    Format an investment summary in the requested format.
    
    Args:
        npv: Net Present Value
        irr: Internal Rate of Return (percentage)
        payback_period: Payback period in years
        format_type: Output format type ("json", "markdown")
        
    Returns:
        Formatted investment summary
    """
    summary = {
        "npv": npv,
        "irr": irr,
        "payback_period": payback_period,
        "recommendation": "Invest" if npv > 0 and irr > 10 else "Do not invest"
    }
    
    if format_type == "json":
        return json.dumps(summary, indent=2)
    elif format_type == "markdown":
        md = "# Investment Summary\n\n"
        md += f"- **NPV**: ${npv}\n"
        md += f"- **IRR**: {irr}%\n"
        md += f"- **Payback Period**: {payback_period} years\n"
        md += f"- **Recommendation**: {summary['recommendation']}\n"
        return md
    else:
        return f"Unsupported format type: {format_type}"

def main():
    print("Financial Function Tools Example")
    print("================================\n")
    
    # Example 1: Using the tools directly
    print("Example 1: Using the tools directly")
    cash_flows = [-100000, 25000, 35000, 45000, 50000, 60000]
    discount_rate = 0.08
    
    dcf_result = calculate_dcf(cash_flows, discount_rate)
    print(f"NPV: ${dcf_result['npv']}")
    
    irr_result = calculate_irr(cash_flows)
    print(f"IRR: {irr_result['irr']}%")
    
    payback_result = calculate_payback_period(cash_flows)
    print(f"Payback Period: {payback_result['payback_period']} years\n")
    
    # Generate visualization
    viz = generate_cash_flow_visualization(
        cash_flows, 
        dcf_result['discounted_cash_flows'],
        "Cash Flow Analysis"
    )
    print(viz)
    
    # Format summary
    summary = format_investment_summary(
        dcf_result['npv'],
        irr_result['irr'],
        payback_result['payback_period']
    )
    print(summary)
    
    # Example 2: Using the tools with an Agent
    print("\nExample 2: Using the tools with an Agent")
    agent = Agent(
        tools=[
            calculate_dcf, 
            calculate_irr, 
            calculate_payback_period, 
            generate_cash_flow_visualization,
            format_investment_summary
        ],
        show_tool_calls=True,
        markdown=True
    )
    
    query = """
    Given the following financial data:
    - Initial investment: $100,000
    - Cash flows for 5 years: $25,000, $35,000, $45,000, $50,000, $60,000
    - Discount rate: 8%
    
    Calculate the NPV, IRR, and payback period. Then create a visualization 
    of the cash flows and format a summary report in markdown.
    """
    
    print("Query:", query)
    response = agent.run(query)
    print("\nAgent response:")
    print(response.content)


if __name__ == "__main__":
    main() 