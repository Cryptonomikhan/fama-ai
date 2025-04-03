#!/usr/bin/env python3
"""
Example usage of the Modeling Agent.

This script demonstrates how to use the Modeling Agent to create
financial models for investment vehicles based on research data.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.modeling import ModelingAgent
from agents.research import ResearchAgent

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to demonstrate Modeling Agent usage.
    """
    print("Initializing agents...")
    
    # Check if we have required API keys
    formation_api_key = os.environ.get("FORMATION_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Select provider based on available API keys
    if formation_api_key:
        provider = "formation"
        print("Using Formation as model provider")
    elif openai_api_key:
        provider = "openai"
        print("Using OpenAI as model provider")
    else:
        print("Error: No API keys found for model providers")
        print("Please set FORMATION_API_KEY or OPENAI_API_KEY in your .env file")
        return
    
    # Initialize the Research Agent first to gather data
    research_agent = ResearchAgent(provider=provider)
    
    # Initialize the Modeling Agent
    modeling_agent = ModelingAgent(provider=provider)
    
    # Example investment vehicle description
    description = """
    A tokenized GPU asset model where investors purchase fractional ownership of GPU compute 
    resources that are leased to AI companies for training and inference, with revenue derived 
    from hourly usage fees.
    """
    
    # Set time horizon and risk profile
    time_horizon = 5
    risk_factors = "moderate"
    
    print("\nGathering research data...")
    # First, get research data using the Research Agent
    research_data = research_agent.research_investment_vehicle(
        description=description,
        time_horizon=time_horizon,
        additional_context={
            "focus_areas": "AI industry growth, GPU demand trends, leasing market dynamics",
            "specific_interests": "Pricing models, maintenance costs, depreciation factors"
        }
    )
    
    # Get additional market conditions
    market_conditions = research_agent.get_market_conditions()
    
    # Get yield data for similar investments
    yield_data = research_agent.get_yield_data(
        vehicle_type="GPU compute resources and data center assets",
        time_period=f"last {time_horizon} years"
    )
    
    print("\nCreating financial model...")
    # Now, create a financial model using the Modeling Agent
    financial_model = modeling_agent.create_financial_model(
        description=description,
        research_data=research_data,
        market_conditions=market_conditions,
        yield_data=yield_data,
        time_horizon=time_horizon,
        risk_factors=risk_factors
    )
    
    print("\nGenerating financial metrics...")
    # Generate financial metrics
    financial_metrics = modeling_agent.generate_metrics(
        financial_model=financial_model,
        time_horizon=time_horizon,
        discount_rate=0.12  # Higher discount rate for tech assets
    )
    
    # Print the financial model and metrics
    print("\n" + "=" * 80)
    print("FINANCIAL MODEL SUMMARY:")
    print("=" * 80)
    
    # Print key assumptions
    if "assumptions" in financial_model and "raw" in financial_model["assumptions"]:
        print("\nKEY ASSUMPTIONS:")
        print("-" * 40)
        print(financial_model["assumptions"]["raw"][:500] + "..." if len(financial_model["assumptions"]["raw"]) > 500 else financial_model["assumptions"]["raw"])
    
    # Print income statement summary
    if "income_statement" in financial_model and "raw" in financial_model["income_statement"]:
        print("\nINCOME STATEMENT SUMMARY:")
        print("-" * 40)
        print(financial_model["income_statement"]["raw"][:500] + "..." if len(financial_model["income_statement"]["raw"]) > 500 else financial_model["income_statement"]["raw"])
    
    # Print cash flow summary
    if "cash_flow" in financial_model and "raw" in financial_model["cash_flow"]:
        print("\nCASH FLOW SUMMARY:")
        print("-" * 40)
        print(financial_model["cash_flow"]["raw"][:500] + "..." if len(financial_model["cash_flow"]["raw"]) > 500 else financial_model["cash_flow"]["raw"])
    
    # Print metrics
    print("\n" + "=" * 80)
    print("FINANCIAL METRICS:")
    print("=" * 80)
    if financial_metrics["irr"]:
        print(f"IRR: {financial_metrics['irr']}")
    if financial_metrics["npv"]:
        print(f"NPV: {financial_metrics['npv']}")
    if financial_metrics["payback_period"]:
        print(f"Payback Period: {financial_metrics['payback_period']}")
    if financial_metrics["roi"]:
        print(f"ROI: {financial_metrics['roi']}")
    if financial_metrics["cash_on_cash"]:
        print(f"Cash on Cash Return: {financial_metrics['cash_on_cash']}")
    if financial_metrics["yield"]:
        print(f"Yield: {financial_metrics['yield']}")
    if financial_metrics["profitability_index"]:
        print(f"Profitability Index: {financial_metrics['profitability_index']}")
    
    # Save results to file
    output_file = "financial_model_example.json"
    print(f"\nSaving results to {output_file}...")
    
    results = {
        "description": description,
        "time_horizon": time_horizon,
        "risk_factors": risk_factors,
        "research_data": research_data,
        "market_conditions": market_conditions,
        "yield_data": yield_data,
        "financial_model": financial_model,
        "financial_metrics": financial_metrics
    }
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 