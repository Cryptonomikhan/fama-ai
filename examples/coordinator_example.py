#!/usr/bin/env python3
"""
Example script for using the Agent Coordinator.

This script demonstrates how to use the AgentCoordinator to process
an investment vehicle description with both step-by-step and team-based approaches.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the AgentCoordinator
from agents.agent_coordinator import AgentCoordinator

def main():
    """Run the Agent Coordinator example."""
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
    
    # Initialize the AgentCoordinator
    coordinator = AgentCoordinator(provider=provider)
    
    # Example investment vehicle description
    description = """
    Tokenized GPU Asset Model: A yield-generating investment vehicle that acquires and operates
    a fleet of high-performance GPU servers for AI/ML workloads in data centers. 
    
    The investment vehicle purchases latest-generation GPUs and deploys them in tier-1 data centers,
    generating revenue by leasing GPU compute capacity to AI research organizations, tech companies, 
    and cloud service providers. The asset is tokenized, allowing fractional ownership with each token 
    representing a specific share of the underlying GPU assets and entitling holders to a proportional 
    share of the net income generated.
    
    Revenue comes from hourly/monthly rates for GPU compute time, while expenses include electricity costs,
    data center colocation fees, maintenance, hardware refreshes, management, and administration. 
    
    Key risks include technological obsolescence as newer GPU models are released, fluctuations in demand
    for AI compute resources, energy price volatility, and potential changes in regulations regarding
    cryptocurrency mining which competes for similar resources.
    """
    
    print("\n" + "="*80)
    print("INVESTMENT VEHICLE ANALYSIS - OPTIMIZED WORKFLOW".center(80))
    print("="*80 + "\n")
    
    print("The Agent Coordinator now uses an improved workflow with optimal sequencing:")
    print("1. Research Agent: Deep research on market conditions and investment structure")
    print("2. Assumption Generator: Create key modeling assumptions based on research")
    print("3. Modeling Agent: Build financial models using research and assumptions")
    print("4. Scenario Planner: Generate baseline, bull, and bear scenarios")
    print("5. Validator: Validate all aspects of the analysis\n")
    
    # Demonstrate both approaches
    demonstrate_approaches = True
    
    if demonstrate_approaches:
        print("COMPARING ANALYSIS APPROACHES".center(80))
        print("-"*80 + "\n")
        print("This example will demonstrate two different approaches:")
        print("1. Step-by-Step: Traditional sequential processing with structured output")
        print("2. Team-Based: Using the Agno Team framework for agent coordination\n")
        
        # First, use the step-by-step approach
        print("1. STEP-BY-STEP APPROACH".center(80))
        print("-"*80 + "\n")
        
        print("Starting step-by-step analysis...\n")
        step_results = coordinator.process_investment_vehicle(
            description=description,
            time_horizon=5,
            risk_factors="moderate",
            output_format="json",
            research_context="Focus on GPU compute market trends, AI/ML workload demands, and technological evolution of GPU hardware.",
            use_team_approach=False
        )
        
        # Get the request ID from the results
        step_request_id = step_results.get("request_id", "unknown")
        
        print(f"Step-by-step analysis complete! Request ID: {step_request_id[:8]}...\n")
        
        # Print the key sections of the results
        print("ANALYSIS RESULTS (STEP-BY-STEP)".center(80))
        print("-"*80)
        
        # Research results
        print("\n📊 RESEARCH RESULTS")
        print(f"Research conducted on tokenized GPU assets and market conditions")
        
        # Assumptions
        print("\n🔍 KEY ASSUMPTIONS")
        if "assumptions" in step_results:
            assumption_categories = step_results["assumptions"].keys()
            for category in assumption_categories:
                print(f"- {category.replace('_', ' ').title()} assumptions included")
        
        # Financial model
        print("\n💰 FINANCIAL MODEL")
        print(f"Financial model created for a {step_results['time_horizon']} year time horizon")
        
        # Financial metrics
        print("\n📈 FINANCIAL METRICS")
        if "metrics" in step_results:
            for metric, value in step_results["metrics"].items():
                if isinstance(value, (int, float)):
                    print(f"- {metric}: {value:.2f}")
                else:
                    print(f"- {metric}: {value}")
        
        # Scenario planning
        print("\n🔮 SCENARIO PLANNING")
        if "scenarios" in step_results:
            for scenario, details in step_results["scenarios"].items():
                print(f"- {scenario.replace('_', ' ').title()} scenario developed")
        
        # Validation
        print("\n✅ VALIDATION")
        if "validation" in step_results:
            for validation_type in step_results["validation"]:
                print(f"- {validation_type.replace('_', ' ').title()} completed")
        
        # Save the step-by-step results to a JSON file
        step_filename = f"step_results_{step_request_id[:8]}.json"
        with open(step_filename, "w") as f:
            json.dump(step_results, f, indent=2)
        
        print(f"\nStep-by-step results saved to {step_filename}")
        
        # Now, use the team-based approach
        print("\n\n2. TEAM-BASED APPROACH".center(80))
        print("-"*80 + "\n")
        
        print("Starting team-based analysis...\n")
        team_results = coordinator.process_investment_vehicle(
            description=description,
            time_horizon=5,
            risk_factors="moderate",
            output_format="json",
            research_context="Focus on GPU compute market trends, AI/ML workload demands, and technological evolution of GPU hardware.",
            use_team_approach=True
        )
        
        # Get the request ID from the results
        team_request_id = team_results.get("request_id", "unknown")
        
        print(f"Team-based analysis complete! Request ID: {team_request_id[:8]}...\n")
        
        # Check if team_response is present in the results
        if "team_response" in team_results:
            print("TEAM ANALYSIS RESULTS".center(80))
            print("-"*80)
            print(team_results["team_response"])
            print()
        
        # Save the team-based results to a JSON file
        team_filename = f"team_results_{team_request_id[:8]}.json"
        with open(team_filename, "w") as f:
            json.dump(team_results, f, indent=2)
        
        print(f"Team-based results saved to {team_filename}")
        
        print("\nCOMPARISON OF APPROACHES".center(80))
        print("-"*80 + "\n")
        print("Step-by-Step Approach:")
        print("✅ Provides highly structured output")
        print("✅ Each step builds on the previous with explicit data passing")
        print("✅ Full control over each step in the process")
        print("❌ More complex implementation with manual data handling")
        print("❌ Requires more code to manage the workflow")
        print()
        print("Team-Based Approach:")
        print("✅ More concise code for agent coordination")
        print("✅ Automatic handling of inter-agent communication")
        print("✅ Better for free-form text responses")
        print("❌ Less structured output format")
        print("❌ Requires post-processing to extract structured data")
        
    else:
        # Use the default step-by-step approach for simplicity
        print("Starting investment vehicle analysis...\n")
        
        # Process the investment vehicle description
        results = coordinator.process_investment_vehicle(
            description=description,
            time_horizon=5,
            risk_factors="moderate",
            output_format="json",
            research_context="Focus on GPU compute market trends, AI/ML workload demands, and technological evolution of GPU hardware."
        )
        
        # Get the request ID from the results
        request_id = results.get("request_id", "unknown")
        
        print(f"Analysis complete! Request ID: {request_id[:8]}...\n")
        
        # Print the key sections of the results
        print("ANALYSIS RESULTS".center(80))
        print("-"*80)
        
        # Research results
        print("\n📊 RESEARCH RESULTS")
        print(f"Research conducted on tokenized GPU assets and market conditions")
        
        # Assumptions (now generated before modeling)
        print("\n🔍 KEY ASSUMPTIONS")
        if "assumptions" in results:
            assumption_categories = results["assumptions"].keys()
            for category in assumption_categories:
                print(f"- {category.replace('_', ' ').title()} assumptions included")
        
        # Financial model
        print("\n💰 FINANCIAL MODEL")
        print(f"Financial model created for a {results['time_horizon']} year time horizon")
        
        # Financial metrics
        print("\n📈 FINANCIAL METRICS")
        if "metrics" in results:
            for metric, value in results["metrics"].items():
                if isinstance(value, (int, float)):
                    print(f"- {metric}: {value:.2f}")
                else:
                    print(f"- {metric}: {value}")
        
        # Scenario planning
        print("\n🔮 SCENARIO PLANNING")
        if "scenarios" in results:
            for scenario, details in results["scenarios"].items():
                print(f"- {scenario.replace('_', ' ').title()} scenario developed")
        
        # Validation
        print("\n✅ VALIDATION")
        if "validation" in results:
            for validation_type in results["validation"]:
                print(f"- {validation_type.replace('_', ' ').title()} completed")
        
        # Save the results to a JSON file
        filename = f"example_results_{request_id[:8]}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")

if __name__ == "__main__":
    main() 