#!/usr/bin/env python3
"""
Example usage of the Scenario Planner Agent.

This script demonstrates how to use the Scenario Planner Agent to create
scenario models for investment vehicles based on financial models.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scenario_planner import ScenarioPlannerAgent
from agents.modeling import ModelingAgent
from agents.research import ResearchAgent

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to demonstrate Scenario Planner Agent usage.
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
    
    # Initialize the Scenario Planner Agent
    scenario_planner = ScenarioPlannerAgent(provider=provider)
    
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
    
    print("\nGenerating scenarios...")
    # Generate scenarios using the Scenario Planner Agent
    scenarios = scenario_planner.generate_scenarios(
        description=description,
        financial_model=financial_model,
        research_data=research_data,
        market_conditions=market_conditions,
        risk_factors=risk_factors,
        time_horizon=time_horizon
    )
    
    print("\nAnalyzing scenario impact...")
    # Analyze the impact of different scenarios
    scenario_impact = scenario_planner.analyze_scenario_impact(
        scenarios=scenarios,
        financial_metrics=financial_metrics
    )
    
    # Print the scenarios and impact analysis
    print("\n" + "=" * 80)
    print("SCENARIO PLANNING RESULTS:")
    print("=" * 80)
    
    # Print baseline scenario
    if "baseline" in scenarios and "description" in scenarios["baseline"]:
        print("\nBASELINE SCENARIO:")
        print("-" * 40)
        print(scenarios["baseline"]["description"][:500] + "..." if len(scenarios["baseline"]["description"]) > 500 else scenarios["baseline"]["description"])
    
    # Print bull scenario
    if "bull" in scenarios and "description" in scenarios["bull"]:
        print("\nBULL SCENARIO:")
        print("-" * 40)
        print(scenarios["bull"]["description"][:500] + "..." if len(scenarios["bull"]["description"]) > 500 else scenarios["bull"]["description"])
    
    # Print bear scenario
    if "bear" in scenarios and "description" in scenarios["bear"]:
        print("\nBEAR SCENARIO:")
        print("-" * 40)
        print(scenarios["bear"]["description"][:500] + "..." if len(scenarios["bear"]["description"]) > 500 else scenarios["bear"]["description"])
    
    # Print scenario impact analysis
    print("\n" + "=" * 80)
    print("SCENARIO IMPACT ANALYSIS:")
    print("=" * 80)
    if "comparative_analysis" in scenario_impact and "raw" in scenario_impact["comparative_analysis"]:
        print("\nCOMPARATIVE ANALYSIS:")
        print("-" * 40)
        print(scenario_impact["comparative_analysis"]["raw"][:500] + "..." if len(scenario_impact["comparative_analysis"]["raw"]) > 500 else scenario_impact["comparative_analysis"]["raw"])
    
    if "risk_assessment" in scenario_impact and "raw" in scenario_impact["risk_assessment"]:
        print("\nRISK ASSESSMENT:")
        print("-" * 40)
        print(scenario_impact["risk_assessment"]["raw"][:500] + "..." if len(scenario_impact["risk_assessment"]["raw"]) > 500 else scenario_impact["risk_assessment"]["raw"])
    
    if "decision_framework" in scenario_impact and "raw" in scenario_impact["decision_framework"]:
        print("\nDECISION FRAMEWORK:")
        print("-" * 40)
        print(scenario_impact["decision_framework"]["raw"][:500] + "..." if len(scenario_impact["decision_framework"]["raw"]) > 500 else scenario_impact["decision_framework"]["raw"])
    
    # Save results to file
    output_file = "scenario_planning_example.json"
    print(f"\nSaving results to {output_file}...")
    
    results = {
        "description": description,
        "time_horizon": time_horizon,
        "risk_factors": risk_factors,
        "research_data": research_data,
        "market_conditions": market_conditions,
        "yield_data": yield_data,
        "financial_model": financial_model,
        "financial_metrics": financial_metrics,
        "scenarios": scenarios,
        "scenario_impact": scenario_impact
    }
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main() 