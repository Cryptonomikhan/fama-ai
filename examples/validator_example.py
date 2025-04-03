#!/usr/bin/env python3
"""
Example script for using the Validator Agent.

This script demonstrates how to use the ValidatorAgent to validate
financial models and identify issues and improvements.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary components
from agents.research import ResearchAgent
from agents.modeling import ModelingAgent
from agents.validator import ValidatorAgent
from models.model_factory import create_model

def main():
    """Run the Validator Agent example."""
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
    
    modeling_agent = ModelingAgent(
        provider=provider,
        temperature=0.1
    )
    
    validator_agent = ValidatorAgent(
        provider=provider,
        temperature=0.1
    )
    
    # Example investment vehicle description
    description = """
    SaaS Subscription Revenue Securitization: A yield-generating investment vehicle 
    that purchases the rights to future subscription revenue from established SaaS 
    companies. The securitized subscription contracts are bundled into tranches based 
    on customer retention probability and credit quality.
    
    The investment provides upfront capital to SaaS companies while offering investors 
    steady monthly cash flows from the subscription payments. The model includes a 
    reserve fund to cover potential defaults and a waterfall payment structure.
    
    Revenue comes from the recurring subscription payments, while expenses include 
    servicing fees, administration costs, and technology platform fees for tracking 
    and managing the subscription payments.
    
    The investment involves credit risk from subscriber defaults, retention risk from 
    subscription cancellations, and concentration risk if the portfolio is not 
    sufficiently diversified across different SaaS providers.
    """
    
    print("\nGathering research data...")
    # Gather research data
    research_results = research_agent.research_investment_vehicle(
        description=description,
        time_horizon=5,
        additional_context="Focus on SaaS subscription models, churn rates, and securitization structures."
    )
    
    # Get additional market conditions
    market_conditions = research_agent.get_market_conditions()
    
    # Get yield data for similar investments
    yield_data = research_agent.get_yield_data(
        vehicle_type="subscription revenue securitization",
        time_period="last 5 years"
    )
    
    print("\nCreating financial model...")
    # Create a financial model
    financial_model = modeling_agent.create_financial_model(
        description=description,
        research_data=research_results,
        market_conditions=market_conditions,
        yield_data=yield_data,
        time_horizon=5,
        risk_factors="moderate"
    )
    
    # Generate financial metrics
    metrics = modeling_agent.generate_metrics(
        financial_model=financial_model,
        time_horizon=5,
        discount_rate=0.1
    )
    
    # Create mock scenarios and assumptions for demonstration
    scenarios = {
        "baseline": {
            "description": "Stable SaaS market with consistent growth",
            "churn_rate": "Annual churn rate of 10-12%",
            "revenue_growth": "Annual growth of 6-8% in subscription values",
            "default_rate": "2-3% of subscribers"
        },
        "bull": {
            "description": "Strong SaaS sector growth with high retention",
            "churn_rate": "Annual churn rate of 7-8%",
            "revenue_growth": "Annual growth of 10-12% in subscription values",
            "default_rate": "1-2% of subscribers"
        },
        "bear": {
            "description": "Economic downturn impacting subscription renewals",
            "churn_rate": "Annual churn rate of 18-20%",
            "revenue_growth": "Annual decline of 2-4% in subscription values",
            "default_rate": "5-6% of subscribers"
        }
    }
    
    assumptions = {
        "revenue_assumptions": [
            "Average subscription value increases 3% annually",
            "Churn rate of 12% per year for baseline scenario",
            "New subscriptions acquired at 15% annual growth rate",
            "90% of subscriptions are annual, 10% are monthly"
        ],
        "opex_assumptions": [
            "Servicing costs at 2% of AUM annually",
            "Administration costs fixed at $150,000 per year + inflation",
            "Technology platform fees at 0.5% of AUM annually",
            "Legal and compliance costs at $75,000 per year"
        ],
        "capex_assumptions": [
            "Initial technology infrastructure setup of $250,000",
            "Technology upgrades of $50,000 every 2 years",
            "No physical assets required"
        ],
        "market_assumptions": [
            "SaaS industry growth at 15% CAGR over next 5 years",
            "Average SaaS company valuation multiples remain stable",
            "Increasing competition for subscription securitization deals",
            "Gradual interest rate increases of 25bps per year"
        ],
        "financial_assumptions": [
            "Discount rate of 10% for NPV calculations",
            "Tax rate of 21% on net income",
            "Reserve fund maintained at 5% of total AUM",
            "Leverage ratio capped at 3:1 debt-to-equity"
        ]
    }
    
    print("\nValidating financial model...")
    # Validate the financial model
    validation_results = validator_agent.validate_model(
        description=description,
        financial_model=financial_model,
        assumptions=assumptions,
        metrics=metrics,
        scenarios=scenarios,
        research_data=research_results,
        market_conditions=market_conditions
    )
    
    print("\nValidating financial metrics...")
    # Validate the financial metrics
    metric_validation = validator_agent.validate_metrics(
        metrics=metrics,
        financial_model=financial_model
    )
    
    print("\nValidating scenario analyses...")
    # Validate the scenario analyses
    scenario_validation = validator_agent.validate_scenarios(
        scenarios=scenarios,
        financial_model=financial_model,
        assumptions=assumptions,
        market_conditions=market_conditions
    )
    
    # Print the results in a readable format
    print("\n" + "="*80)
    print("VALIDATION RESULTS".center(80))
    print("="*80 + "\n")
    
    print("1. MODEL VALIDATION")
    print("-"*80)
    
    # Print overall score
    overall_score = validation_results.get("overall_score")
    if overall_score:
        print(f"Overall Validation Score: {overall_score}/100")
    print()
    
    # Print critical issues
    print("Critical Issues:")
    for item in validation_results.get("issues", {}).get("critical", []):
        print(f"  - {item}")
    print()
    
    # Print major issues
    print("Major Issues:")
    for item in validation_results.get("issues", {}).get("major", []):
        print(f"  - {item}")
    print()
    
    # Print minor issues
    print("Minor Issues:")
    for item in validation_results.get("issues", {}).get("minor", []):
        print(f"  - {item}")
    print()
    
    # Print recommendations
    print("Recommendations:")
    for item in validation_results.get("recommendations", []):
        print(f"  - {item}")
    print()
    
    # Print risk areas
    print("Risk Areas:")
    for item in validation_results.get("risk_areas", []):
        print(f"  - {item}")
    print()
    
    # Print compliance notes
    print("Compliance Notes:")
    for item in validation_results.get("compliance_notes", []):
        print(f"  - {item}")
    print()
    
    print("2. METRIC VALIDATION")
    print("-"*80)
    
    # Print IRR validation
    print("IRR Validation:")
    irr_status = metric_validation.get("irr", {}).get("status")
    if irr_status:
        print(f"  Status: {irr_status}")
    for item in metric_validation.get("irr", {}).get("issues", []):
        print(f"  - Issue: {item}")
    for item in metric_validation.get("irr", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    # Print NPV validation
    print("NPV Validation:")
    npv_status = metric_validation.get("npv", {}).get("status")
    if npv_status:
        print(f"  Status: {npv_status}")
    for item in metric_validation.get("npv", {}).get("issues", []):
        print(f"  - Issue: {item}")
    for item in metric_validation.get("npv", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    # Print ROI validation
    print("ROI Validation:")
    roi_status = metric_validation.get("roi", {}).get("status")
    if roi_status:
        print(f"  Status: {roi_status}")
    for item in metric_validation.get("roi", {}).get("issues", []):
        print(f"  - Issue: {item}")
    for item in metric_validation.get("roi", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    print("3. SCENARIO VALIDATION")
    print("-"*80)
    
    # Print scenario coverage validation
    print("Scenario Coverage:")
    coverage_status = scenario_validation.get("scenario_coverage", {}).get("status")
    if coverage_status:
        print(f"  Status: {coverage_status}")
    for item in scenario_validation.get("scenario_coverage", {}).get("gaps", []):
        print(f"  - Gap: {item}")
    for item in scenario_validation.get("scenario_coverage", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    # Print scenario assumptions validation
    print("Scenario Assumptions:")
    assumptions_status = scenario_validation.get("scenario_assumptions", {}).get("status")
    if assumptions_status:
        print(f"  Status: {assumptions_status}")
    for item in scenario_validation.get("scenario_assumptions", {}).get("issues", []):
        print(f"  - Issue: {item}")
    for item in scenario_validation.get("scenario_assumptions", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    # Print scenario impact validation
    print("Scenario Impact Analysis:")
    impact_status = scenario_validation.get("scenario_impact", {}).get("status")
    if impact_status:
        print(f"  Status: {impact_status}")
    for item in scenario_validation.get("scenario_impact", {}).get("issues", []):
        print(f"  - Issue: {item}")
    for item in scenario_validation.get("scenario_impact", {}).get("recommendations", []):
        print(f"  - Recommendation: {item}")
    print()
    
    # Save the results to a JSON file
    results = {
        "description": description,
        "validation_results": validation_results,
        "metric_validation": metric_validation,
        "scenario_validation": scenario_validation
    }
    
    filename = "validator_example.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    main() 