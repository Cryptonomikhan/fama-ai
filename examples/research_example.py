#!/usr/bin/env python3
"""
Example usage of the Research Agent.

This script demonstrates how to use the Research Agent to gather information
about an investment vehicle.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.research import ResearchAgent

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to demonstrate Research Agent usage.
    """
    print("Initializing Research Agent...")
    
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
    
    # Initialize the Research Agent
    agent = ResearchAgent(provider=provider)
    
    # Example investment vehicle description
    description = """
    A tokenized GPU asset model where investors purchase fractional ownership of GPU compute 
    resources that are leased to AI companies for training and inference, with revenue derived 
    from hourly usage fees.
    """
    
    # Perform research
    print("\nResearching investment vehicle...")
    results = agent.research_investment_vehicle(
        description=description,
        time_horizon=5,
        additional_context={
            "focus_areas": "AI industry growth, GPU demand trends, leasing market dynamics",
            "specific_interests": "Pricing models, maintenance costs, depreciation factors"
        }
    )
    
    # Print the results
    print("\n" + "=" * 50)
    print("RESEARCH RESULTS:")
    print("=" * 50)
    print(results["raw_research"])
    print("=" * 50)
    
    # Get current market conditions
    print("\nGetting current market conditions...")
    market_conditions = agent.get_market_conditions()
    
    print("\n" + "=" * 50)
    print("MARKET CONDITIONS:")
    print("=" * 50)
    print(market_conditions["market_conditions"])
    print("=" * 50)
    
    # Get yield data for a similar investment vehicle type
    print("\nGetting yield data for similar investments...")
    yield_data = agent.get_yield_data(
        vehicle_type="GPU compute resources and data center REITs",
        time_period="last 5 years"
    )
    
    print("\n" + "=" * 50)
    print("YIELD DATA:")
    print("=" * 50)
    print(yield_data["yield_data"])
    print("=" * 50)

if __name__ == "__main__":
    main() 