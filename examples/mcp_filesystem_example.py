#!/usr/bin/env python3
"""
MCP Filesystem Integration Example

This example demonstrates how to use the Model Context Protocol (MCP) filesystem
integration with the Financial Modeling API to process local financial data files.

The script:
1. Creates a temporary directory with sample financial data files
2. Makes an API request with filesystem MCP enabled
3. Shows how the model can access and analyze local files
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
    
    # Create a CSV file with rental property data
    rental_data = """property_id,location,purchase_price,monthly_rent,annual_expenses,occupancy_rate
1,New York,850000,4200,12000,0.95
2,Chicago,420000,2800,8500,0.92
3,Miami,550000,3200,9200,0.88
4,Los Angeles,950000,4500,14000,0.96
5,Austin,480000,2900,7800,0.94
"""
    with open(os.path.join(temp_dir, "rental_properties.csv"), "w") as f:
        f.write(rental_data)
    
    # Create a JSON file with market analysis data
    market_data = {
        "market_trends": {
            "average_cap_rate": 0.055,
            "price_growth_forecast": 0.038,
            "rental_growth_forecast": 0.042,
            "interest_rates": {
                "current": 0.065,
                "forecast_6m": 0.062,
                "forecast_12m": 0.059
            }
        },
        "comparable_properties": [
            {"id": "comp1", "price_per_sqft": 425, "cap_rate": 0.058},
            {"id": "comp2", "price_per_sqft": 410, "cap_rate": 0.062},
            {"id": "comp3", "price_per_sqft": 440, "cap_rate": 0.051}
        ]
    }
    with open(os.path.join(temp_dir, "market_analysis.json"), "w") as f:
        json.dump(market_data, f, indent=2)
    
    # Create a text file with assumptions and guidelines
    assumptions = """# Investment Assumptions

## General Assumptions
- Holding period: 7 years
- Closing costs: 2% of purchase price
- Selling costs: 6% of sale price
- Renovation costs: Specified per property

## Financing Assumptions
- Loan-to-value ratio: 75%
- Interest rate: 6.5% fixed
- Amortization period: 30 years
- Loan term: 7 years

## Operating Assumptions
- Property management fee: 8% of gross rental income
- Vacancy rate: Per property (see rental_properties.csv)
- Maintenance reserve: 5% of gross rental income
- Capital expenditure reserve: 3% of gross rental income
- Property tax inflation: 2% per year
- Insurance inflation: 3% per year
"""
    with open(os.path.join(temp_dir, "investment_assumptions.md"), "w") as f:
        f.write(assumptions)
    
    console.print("Created sample financial data files:")
    console.print("  • [bold]rental_properties.csv[/bold]: Rental property details")
    console.print("  • [bold]market_analysis.json[/bold]: Market trend data")
    console.print("  • [bold]investment_assumptions.md[/bold]: Investment guidelines")
    console.print("\n")
    
    return temp_dir

def make_api_request(data_directory):
    """Make a request to the Financial Modeling API with filesystem MCP enabled"""
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        console.print("Please set your OpenAI API key with: export OPENAI_API_KEY=your-api-key")
        return None
    
    # Create request payload
    payload = {
        "task": "Analyze the rental property data in the provided directory. Create a financial model for the property in Chicago showing ROI, cash flow projections for 7 years, and IRR. Use the market_analysis.json data for market assumptions and refer to the investment_assumptions.md file for general guidelines.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory
    }
    
    # Display request information
    console.print(Panel(
        "Making API request with MCP filesystem access",
        title="API Request",
        subtitle=f"Directory: {data_directory}"
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
            subtitle="Using MCP to access local financial data",
            width=100
        ))

def main():
    """Run the MCP filesystem example"""
    console.print(Panel(
        "[bold]This example demonstrates how to use the Model Context Protocol (MCP) filesystem integration[/bold]\n"
        "The script will create sample financial data files and make an API request with filesystem MCP enabled",
        title="MCP Filesystem Example",
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