#!/usr/bin/env python3
"""
Dashboard Builder Example for Fama AI.

This example demonstrates how to use the Dashboard Builder Agent to create
a Next.js dashboard for visualizing financial modeling results.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.research import ResearchAgent
from agents.modeling import ModelingAgent
from agents.scenario_planner import ScenarioPlannerAgent
from agents.dashboard_builder import DashboardBuilderAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """Main function to run the dashboard builder example."""
    
    # Example investment vehicle description
    investment_vehicle = """
    SaaS Revenue Securitization
    
    This investment vehicle involves the securitization of subscription revenue from a portfolio 
    of enterprise SaaS companies. The portfolio consists of 15 B2B SaaS companies with average 
    annual recurring revenue (ARR) of $12M each, 18% average annual growth rate, and 85% average 
    gross retention. The securitization involves issuing tokens that represent rights to a portion 
    of the future subscription revenue from this portfolio over a 5-year period. The initial token 
    sale will raise $50M, with tokens being fully liquid after a 12-month lockup period. Management 
    fees are 2% annually, with a 20% performance fee on returns exceeding an 8% hurdle rate.
    """
    
    # Initialize agents
    research_agent = ResearchAgent(provider="anthropic")
    modeling_agent = ModelingAgent(provider="anthropic")
    scenario_agent = ScenarioPlannerAgent(provider="anthropic")
    dashboard_agent = DashboardBuilderAgent(
        provider="anthropic", 
        output_dir="examples/dashboard-output"
    )
    
    # Step 1: Gather research data
    logger.info("Gathering research data...")
    research_data = research_agent.research_investment_vehicle(investment_vehicle)
    
    # Step 2: Gather market conditions
    logger.info("Analyzing market conditions...")
    market_conditions = research_agent.analyze_market_conditions(
        investment_vehicle, research_data
    )
    
    # Step 3: Gather yield data
    logger.info("Gathering yield data...")
    yield_data = research_agent.gather_yield_data(
        investment_vehicle, research_data, market_conditions
    )
    
    # Step 4: Create financial model
    logger.info("Creating financial model...")
    financial_model = modeling_agent.create_financial_model(
        investment_vehicle, 
        research_data, 
        market_conditions, 
        yield_data
    )
    
    # Step 5: Generate financial metrics
    logger.info("Calculating financial metrics...")
    financial_metrics = modeling_agent.calculate_financial_metrics(
        investment_vehicle, 
        financial_model
    )
    
    # Step 6: Generate scenarios
    logger.info("Generating scenarios...")
    scenarios = scenario_agent.generate_scenarios(
        investment_vehicle, 
        research_data, 
        market_conditions, 
        yield_data, 
        financial_model
    )
    
    # Step 7: Analyze scenario impact
    logger.info("Analyzing scenario impact...")
    scenario_impact = scenario_agent.analyze_scenario_impact(
        investment_vehicle, 
        scenarios, 
        financial_model, 
        financial_metrics
    )
    
    # Combine all results
    results = {
        "investment_vehicle": investment_vehicle,
        "research_results": research_data,
        "market_conditions": market_conditions,
        "yield_data": yield_data,
        "financial_model": financial_model,
        "financial_metrics": financial_metrics,
        "scenarios": scenarios,
        "scenario_impact": scenario_impact
    }
    
    # Step 8: Create dashboard
    logger.info("Creating dashboard...")
    dashboard_result = dashboard_agent.create_dashboard(
        results,
        project_name="saas-securitization-dashboard",
        theme="light",
        chart_library="recharts"
    )
    
    # Print dashboard generation results
    logger.info("Dashboard generation completed!")
    print("\nDashboard Generation Results:")
    print(f"Success: {dashboard_result['success']}")
    
    if dashboard_result['success']:
        print(f"Project Directory: {dashboard_result['project_directory']}")
        print(f"Components Created: {len(dashboard_result['components_created'])}")
        
        print("\nNext Steps:")
        for i, step in enumerate(dashboard_result['next_steps'], 1):
            print(f"{i}. {step}")
    else:
        print(f"Error: {dashboard_result.get('error', 'Unknown error')}")
    
    # Save results to a file
    results_file = "examples/dashboard_example_results.json"
    with open(results_file, "w") as f:
        json.dump(dashboard_result, f, indent=2)
    
    logger.info(f"Results saved to {results_file}")

if __name__ == "__main__":
    main() 