#!/usr/bin/env python3
"""
Example script for using the Assumption Generator Agent.

This script demonstrates how to use the AssumptionGeneratorAgent to generate
and validate assumptions for financial models based on research data.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary components
from agents.research import ResearchAgent
from agents.assumption_generator import AssumptionGeneratorAgent
from models.model_factory import create_model

def main():
    """Run the Assumption Generator example."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for required API keys
    formation_api_key = os.getenv("FORMATION_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not formation_api_key and not openai_api_key:
        print("Error: No API keys found. Please set FORMATION_API_KEY or OPENAI_API_KEY in your .env file.")
        return
    
    # Select the model provider based on available API keys
    provider = "formation" if formation_api_key else "openai"
    print(f"Using {provider} as the model provider.")
    
    # Initialize the agents
    research_agent = ResearchAgent(
        provider=provider,
        temperature=0.2
    )
    
    assumption_generator = AssumptionGeneratorAgent(
        provider=provider,
        temperature=0.1
    )
    
    # Example investment vehicle description
    description = """
    Real Estate Debt Fund: A yield-generating investment vehicle that provides 
    senior and mezzanine debt financing for commercial real estate projects with 
    a focus on multifamily and industrial properties in growing metropolitan areas. 
    
    The fund targets an 8-10% annual return through interest payments and origination 
    fees on loans with 2-5 year terms. Leverage is limited to 50% LTV, providing a 
    cushion against property value declines.
    
    Key revenue streams include interest income, origination fees, and prepayment 
    penalties. Operating expenses include fund management fees, legal costs for loan 
    documentation, due diligence expenses, and loan servicing costs.
    
    The investment involves credit risk from borrower defaults, interest rate risk 
    from changing monetary policy, and market risk from the underlying real estate sectors.
    """
    
    print("\nGathering research data...")
    # Gather research data
    research_results = research_agent.research_investment_vehicle(
        description=description,
        time_horizon=5,
        additional_context="Focus on current real estate debt markets, multifamily and industrial property trends, and metropolitan growth patterns."
    )
    
    # Get additional market conditions
    market_conditions = research_agent.get_market_conditions()
    
    # Get yield data for similar investments
    yield_data = research_agent.get_yield_data(
        vehicle_type="real estate debt fund",
        time_period="last 5 years"
    )
    
    # Create a mock financial model for demonstration purposes
    financial_model = {
        "Year 1": {
            "capital_raised": "$50,000,000",
            "loans_originated": "$45,000,000",
            "interest_income": "$3,600,000",
            "fee_income": "$900,000",
            "total_revenue": "$4,500,000",
            "operating_expenses": "$1,500,000",
            "net_income": "$3,000,000",
            "return_on_investment": "6.0%"
        },
        "Year 2": {
            "capital_raised": "$0",
            "loans_originated": "$20,000,000",
            "interest_income": "$5,200,000",
            "fee_income": "$400,000",
            "total_revenue": "$5,600,000",
            "operating_expenses": "$1,700,000",
            "net_income": "$3,900,000",
            "return_on_investment": "7.8%"
        },
        "Year 3": {
            "capital_raised": "$0",
            "loans_originated": "$25,000,000",
            "interest_income": "$5,800,000",
            "fee_income": "$500,000",
            "total_revenue": "$6,300,000",
            "operating_expenses": "$1,900,000",
            "net_income": "$4,400,000",
            "return_on_investment": "8.8%"
        },
        "Year 4": {
            "capital_raised": "$0",
            "loans_originated": "$30,000,000",
            "interest_income": "$6,600,000",
            "fee_income": "$600,000",
            "total_revenue": "$7,200,000",
            "operating_expenses": "$2,100,000",
            "net_income": "$5,100,000",
            "return_on_investment": "10.2%"
        },
        "Year 5": {
            "capital_raised": "$0",
            "loans_originated": "$0",
            "interest_income": "$4,800,000",
            "fee_income": "$0",
            "total_revenue": "$4,800,000",
            "operating_expenses": "$1,600,000",
            "net_income": "$3,200,000",
            "return_on_investment": "6.4%"
        }
    }
    
    # Create mock scenarios
    scenarios = {
        "baseline": {
            "description": "Economic stability with moderate growth in urban centers",
            "interest_rates": "Gradual rise over 5 years, +100 bps",
            "property_values": "Annual appreciation of 3-4%",
            "default_rate": "1-2% of loans"
        },
        "bull": {
            "description": "Strong economic expansion with urban population growth",
            "interest_rates": "Stable rates for 2-3 years, then moderate rise",
            "property_values": "Annual appreciation of 5-7%",
            "default_rate": "< 1% of loans"
        },
        "bear": {
            "description": "Economic recession with pressure on real estate valuations",
            "interest_rates": "Sharp initial rise followed by central bank cuts",
            "property_values": "10-15% decline over first 2 years, then stabilization",
            "default_rate": "4-5% of loans"
        }
    }
    
    print("\nGenerating assumptions based on research data...")
    # Generate assumptions
    assumptions = assumption_generator.generate_assumptions(
        description=description,
        research_data=research_results,
        market_conditions=market_conditions,
        yield_data=yield_data,
        financial_model=financial_model,
        scenarios=scenarios,
        time_horizon=5,
        risk_factors="moderate"
    )
    
    print("\nValidating assumptions against research data...")
    # Validate assumptions
    validation = assumption_generator.validate_assumptions(
        assumptions=assumptions,
        research_data=research_results,
        market_conditions=market_conditions
    )
    
    # Print the results in a readable format
    print("\n" + "="*80)
    print("ASSUMPTION GENERATOR RESULTS".center(80))
    print("="*80 + "\n")
    
    print("1. KEY ASSUMPTIONS")
    print("-"*80)
    
    # Print revenue assumptions
    print("Revenue Assumptions:")
    for item in assumptions.get("revenue_assumptions", []):
        print(f"  - {item}")
    print()
    
    # Print operating expense assumptions
    print("Operating Expense Assumptions:")
    for item in assumptions.get("opex_assumptions", []):
        print(f"  - {item}")
    print()
    
    # Print capital expenditure assumptions
    print("CapEx Assumptions:")
    for item in assumptions.get("capex_assumptions", []):
        print(f"  - {item}")
    print()
    
    # Print market assumptions
    print("Market Assumptions:")
    for item in assumptions.get("market_assumptions", []):
        print(f"  - {item}")
    print()
    
    # Print financial assumptions
    print("Financial Assumptions:")
    for item in assumptions.get("financial_assumptions", []):
        print(f"  - {item}")
    print()
    
    print("2. ASSUMPTION VALIDATION")
    print("-"*80)
    
    # Print validation results
    print("Validation Results:")
    for key, value in validation.get("validation_results", {}).items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Print critical assumptions
    print("Critical Assumptions:")
    for item in validation.get("critical_assumptions", []):
        print(f"  - {item}")
    print()
    
    # Print areas of uncertainty
    print("Areas of Uncertainty:")
    for item in validation.get("areas_of_uncertainty", []):
        print(f"  - {item}")
    print()
    
    # Save the results to a JSON file
    results = {
        "description": description,
        "time_horizon": 5,
        "risk_factors": "moderate",
        "assumptions": assumptions,
        "validation": validation
    }
    
    filename = "assumption_generator_example.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    main() 