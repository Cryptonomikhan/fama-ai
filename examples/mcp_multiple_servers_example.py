#!/usr/bin/env python3
"""
Multiple MCP Servers Integration Example

This example demonstrates how to use multiple Model Context Protocol (MCP) servers
simultaneously with the Financial Modeling API. It shows how to configure both
filesystem access and custom MCP servers for enhanced AI capabilities.

The script:
1. Creates a temporary directory with sample financial data files
2. Makes an API request with both filesystem MCP and a custom MCP server
3. Shows how the model can leverage multiple MCP tools together
"""

import os
import sys
import json
import tempfile
import requests
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

# Create a console for pretty output
console = Console()

# API endpoint
API_URL = "http://localhost:8000/task/submit"

def create_sample_financial_data():
    """Create a temporary directory with sample financial data files"""
    temp_dir = tempfile.mkdtemp(prefix="financial_data_")
    console.print(f"Created temporary directory: [bold cyan]{temp_dir}[/bold cyan]\n")
    
    # Create a CSV file with income statement data
    income_data = """year,revenue,cogs,operating_expenses,interest_expense,tax_rate
2023,2500000,1250000,750000,120000,0.21
2024,2750000,1375000,787500,115000,0.21
2025,3025000,1512500,826875,110000,0.21
2026,3327500,1663750,868219,105000,0.21
2027,3660250,1830125,911630,100000,0.21
"""
    with open(os.path.join(temp_dir, "income_statement.csv"), "w") as f:
        f.write(income_data)
    
    # Create a JSON file with company information
    company_data = {
        "company_info": {
            "name": "TechGrowth Inc.",
            "industry": "Software Development",
            "founding_year": 2018,
            "employees": 86,
            "headquarters": "Austin, TX"
        },
        "growth_metrics": {
            "historical_cagr": 0.12,
            "projected_cagr": 0.15,
            "market_share": 0.023,
            "market_share_growth": 0.03
        },
        "investment_rounds": [
            {"year": 2018, "round": "Seed", "amount": 1500000},
            {"year": 2020, "round": "Series A", "amount": 7500000},
            {"year": 2022, "round": "Series B", "amount": 25000000}
        ]
    }
    with open(os.path.join(temp_dir, "company_data.json"), "w") as f:
        json.dump(company_data, f, indent=2)
    
    # Create a text file with analysis requirements
    requirements = """# Financial Modeling Requirements

## Key Metrics to Calculate
- Current company valuation
- Projected valuation in 5 years
- EBITDA margins and trends
- Return on investment for Series B investors
- Burn rate and runway analysis

## Modeling Approaches
- DCF Valuation (primary method)
- Comparable company analysis (secondary validation)
- Venture capital method for early-stage assessment

## Required Outputs
1. Executive summary with key findings
2. 5-year financial projections
3. Valuation range with sensitivity analysis
4. Investment recommendation
"""
    with open(os.path.join(temp_dir, "analysis_requirements.md"), "w") as f:
        f.write(requirements)
    
    console.print("Created sample financial data files:")
    console.print("  • [bold]income_statement.csv[/bold]: Historical financial performance")
    console.print("  • [bold]company_data.json[/bold]: Company and growth information")
    console.print("  • [bold]analysis_requirements.md[/bold]: Analysis guidelines")
    console.print("\n")
    
    return temp_dir

def make_api_request(data_directory):
    """Make a request to the Financial Modeling API with multiple MCP servers"""
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        console.print("Please set your OpenAI API key with: export OPENAI_API_KEY=your-api-key")
        return None
    
    # Create request payload with multiple MCP servers
    payload = {
        "task": "Analyze the company data in the provided directory and create a comprehensive financial model. Include DCF valuation, growth projections, and investment analysis. Use the market data server for industry benchmarks and the financial calculation server for complex calculations.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        # Enable filesystem MCP
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory,
        # Configure custom MCP servers
        "mcp_servers": [
            {
                "command": "npx",
                "args": ["-y", "@financialtools/mcp-server"],
                "env": {
                    "API_KEY": "test-financial-tools-key",
                    "MODE": "financial-analysis"
                }
            },
            {
                "command": "npx -y @marketdata/mcp-server",
                "env": {
                    "API_KEY": "test-market-data-key",
                    "DATA_SOURCE": "premium"
                }
            }
        ]
    }
    
    # Display request information
    console.print(Panel(
        "Making API request with multiple MCP servers",
        title="API Request",
        subtitle="Filesystem MCP + 2 Custom MCP Servers"
    ))
    
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    console.print("\n")
    
    try:
        # Make the API request
        console.print("Sending request to API... This may take some time depending on the complexity of the analysis.")
        start_time = time.time()
        
        response = requests.post(API_URL, json=payload)
        
        elapsed_time = time.time() - start_time
        console.print(f"Received response in {elapsed_time:.2f} seconds")
        
        # Check response
        if response.status_code == 200:
            return response.text
        else:
            console.print(f"[bold red]Error {response.status_code}:[/bold red] {response.text}")
            return None
    except Exception as e:
        console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
        return None

def display_results(response_text):
    """Display the results from the API response"""
    if response_text:
        console.print(Panel(
            Markdown(response_text),
            title="Financial Analysis Results",
            subtitle="Using Multiple MCP Servers",
            width=100
        ))

def main():
    """Run the multiple MCP servers example"""
    console.print(Panel(
        "[bold]This example demonstrates how to use multiple MCP servers simultaneously[/bold]\n"
        "The script will create sample financial data files and make an API request with:\n"
        "1. Filesystem MCP access to local files\n"
        "2. Financial tools MCP server for calculations\n"
        "3. Market data MCP server for industry benchmarks",
        title="Multiple MCP Servers Example",
        style="green"
    ))
    
    # Create temporary directory with sample data
    data_directory = create_sample_financial_data()
    
    try:
        # Make API request
        response = make_api_request(data_directory)
        
        # Display results
        if response:
            display_results(response)
    finally:
        # Clean up
        console.print(f"\nCleaning up temporary directory: {data_directory}")
        import shutil
        shutil.rmtree(data_directory)
        console.print("Cleanup complete")

if __name__ == "__main__":
    main() 