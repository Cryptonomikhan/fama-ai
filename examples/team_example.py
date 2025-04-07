from src.agents.init_agents import initialize_financial_modeling_team
from dotenv import load_dotenv
import os
import logging
import argparse
from pathlib import Path
from agno.utils.pprint import pprint_run_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_sequential_agents(agent_team, investment_description):
    """Run each agent sequentially, passing data between them"""
    print("\n=== Running Agents Sequentially ===\n")
    
    # Step 1: Run the search agent
    print("\n--- Running Search Agent ---\n")
    searcher = agent_team["searcher"]
    search_prompt = f"Gather the information necessary to build a financial model for {investment_description}"
    
    search_response = searcher.run(search_prompt)
    search_results = search_response.content
    
    print("\n--- Search Results ---\n")
    pprint_run_response(search_response, markdown=True)
    
    # Step 2: Run the assumption generator
    print("\n--- Running Assumption Generator ---\n")
    assumption_generator = agent_team["assumption_generator"]
    assumption_prompt = f"Build assumptions based on the provided data relevant to building a financial model for {investment_description}"
    
    assumption_response = assumption_generator.run(
        assumption_prompt,
        data=search_results
    )
    assumptions = assumption_response.content
    
    print("\n--- Assumption Results ---\n")
    pprint_run_response(assumption_response, markdown=True)
    
    # Step 3: Run the metrics deriver
    print("\n--- Running Metrics Deriver ---\n")
    metrics_deriver = agent_team["metrics_deriver"]
    metrics_prompt = f"Derive a list of comprehensive metrics that should be included in a complete and sophisticated financial model for {investment_description}"
    
    metrics_response = metrics_deriver.run(
        metrics_prompt,
        searcher_data=search_results,
        assumption_data=assumptions
    )
    metrics = metrics_response.content
    
    print("\n--- Metrics Results ---\n")
    pprint_run_response(metrics_response, markdown=True)
    
    # Step 4: Run the financial modeler
    print("\n--- Running Financial Modeling Agent ---\n")
    financial_modeler = agent_team["financial_modeler"]
    model_prompt = f"""
    Based on the provided search data, assumptions, and metrics, build a comprehensive financial model for {investment_description}.
    
    Your financial model should include:
    1. Income statements
    2. Cash flow statements
    3. Scenario analysis (bull, bear, baseline)
    4. Key financial metrics (NPV, IRR, payback period)
    5. Gross and Net Yield calculations across scenarios
    """
    
    model_response = financial_modeler.run(
        model_prompt.strip(),
        searcher_data=search_results,
        assumption_data=assumptions,
        metrics_data=metrics
    )
    financial_model = model_response.content
    
    print("\n--- Financial Model Results ---\n")
    pprint_run_response(model_response, markdown=True)
    
    return {
        "search_results": search_results,
        "assumptions": assumptions,
        "metrics": metrics, 
        "financial_model": financial_model
    }

def run_team_approach(agent_team, investment_description):
    """Run the entire team as a coordinated unit"""
    print("\n=== Using the Coordinated Team Approach ===\n")
    
    # Get the team agent
    team = agent_team["team"]
    
    # Create a unified prompt for the team
    team_prompt = f"""
    Generate a comprehensive financial model for the following investment opportunity:
    
    {investment_description}
    
    Your task is to coordinate the specialized agents:
    - Searcher: Find relevant financial data and market information
    - Assumption Generator: Create realistic financial assumptions
    - Metrics Deriver: Identify key metrics for evaluation
    - Financial Modeler: Build the comprehensive financial model
    
    The financial model should include:
    - Income statements
    - Cash flow statements
    - Scenario analysis (bull, bear, baseline)
    - Key financial metrics (NPV, IRR, payback period)
    - Gross and Net Yield calculations
    
    IMPORTANT: Use MathTools for all calculations to ensure accuracy.
    """
    
    print("Running the agent team as a coordinated unit...")
    # Using the team to run the entire process
    team_response = team.run(team_prompt.strip())
    
    print("\n--- Team Results ---\n")
    pprint_run_response(team_response, markdown=True)
    
    return team_response.content

def main():
    parser = argparse.ArgumentParser(description="Financial Modeling Agent Team Example")
    parser.add_argument("--provider", default="formation", choices=["formation", "openai", "anthropic", "openrouter"],
                        help="Model provider to use")
    parser.add_argument("--model", default=None, help="Model ID (if not provided, will use provider default)")
    parser.add_argument("--temp", type=float, default=0.1, help="Temperature for generation")
    parser.add_argument("--knowledge", default=None, nargs="+", help="Knowledge files to include")
    parser.add_argument("--knowledge-urls", default=None, nargs="+", help="Knowledge URLs to include")
    parser.add_argument("--memory-id", default=None, help="Memory ID for persistent memory")
    parser.add_argument("--history-id", default=None, help="History ID for conversation tracking")
    parser.add_argument("--mode", default="both", choices=["sequential", "team", "both"],
                        help="Run mode: sequential, team, or both")
    parser.add_argument("--output-dir", default="examples/output", help="Directory to save outputs")
    args = parser.parse_args()
    
    # Set up paths for knowledge files
    knowledge_files = None
    if args.knowledge:
        knowledge_files = [str(Path(file).absolute()) for file in args.knowledge]
    
    # Get the API key based on provider
    provider_env_map = {
        "formation": "FORMATION_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    
    api_key = os.getenv(provider_env_map.get(args.provider))
    
    if not api_key:
        print(f"No API key found for provider {args.provider}. Please set the {provider_env_map.get(args.provider)} environment variable.")
        return
    
    print(f"\n=== Financial Modeling Agent Team Example ===")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model or 'default'}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Initialize the agent team
    print("\nInitializing financial modeling agent team...")
    agent_team = initialize_financial_modeling_team(
        api_key=api_key,
        provider=args.provider,
        model_id=args.model,
        temperature=args.temp,
        knowledge_files=knowledge_files,
        knowledge_urls=args.knowledge_urls,
        memory_id=args.memory_id,
        history_id=args.history_id
    )
    
    # Define an example investment to model
    investment_description = """
    A tokenized real estate fund that invests in multifamily properties
    in emerging tech hubs across the U.S. The fund targets properties that
    can be renovated to increase NOI by 15-20%. Initial capital raise is
    $10M with a target IRR of 18-22% over a 5-year hold period.
    """
    
    print(f"\nModeling investment: {investment_description.strip()}\n")
    
    # Run in sequential mode
    if args.mode in ["sequential", "both"]:
        sequential_results = run_sequential_agents(agent_team, investment_description)
        
        # Save sequential results
        if sequential_results:
            for key, content in sequential_results.items():
                output_file = output_dir / f"sequential_{key}.json"
                with open(output_file, "w") as f:
                    f.write(str(content))
    
    # Run in team mode
    if args.mode in ["team", "both"]:
        team_results = run_team_approach(agent_team, investment_description)
        
        # Save team results
        if team_results:
            team_output_file = output_dir / "team_results.json"
            with open(team_output_file, "w") as f:
                f.write(str(team_results))
    
    print(f"\nResults saved to {output_dir}/")

if __name__ == "__main__":
    main() 