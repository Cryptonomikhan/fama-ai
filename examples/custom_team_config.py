"""
Custom Agent Team Configuration Example

This example shows how to create a custom agent team with specialized
instructions and tools for different financial modeling applications.
"""

from typing import Dict, Any, Optional
import logging
import os
from dotenv import load_dotenv

from agno import Agent, Team
from agno.tools import SearchTools, ThinkingTools, FileTools

from src.tools.math_utils import MathTools
from src.tools.financial_calculations import FinancialCalculationTools
from src.tools.website_scraper import WebsiteScraperTools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_real_estate_modeling_team(
    api_key: str,
    model_id: str = "gpt-4o",
    temperature: float = 0.1,
    mcp_server_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a specialized team for real estate financial modeling
    
    Args:
        api_key: OpenAI API key
        model_id: Model ID to use
        temperature: Temperature for generation
        mcp_server_url: URL for MCP server
    
    Returns:
        Dictionary containing the specialized agent team
    """
    # Initialize common tools
    math_tools = MathTools()
    financial_tools = FinancialCalculationTools()
    thinking_tools = ThinkingTools()
    search_tools = SearchTools(api_key=api_key)
    file_tools = FileTools()  # For reading/writing files
    website_scraper = WebsiteScraperTools(timeout=20)
    
    # 1. Create specialized real estate data searcher
    re_searcher = Agent(
        name="Real Estate Market Researcher",
        llm={
            "model": model_id,
            "api_key": api_key,
            "temperature": temperature
        },
        tools=[search_tools, thinking_tools, website_scraper],
        mcp_server_url=mcp_server_url,
        instructions="""
        You are a specialized real estate market researcher. Your focus is on finding:
        
        1. Cap rates for multifamily properties in specific regions
        2. Rental growth projections in target markets
        3. Renovation costs and ROI data for property improvements
        4. Occupancy rates and trends by property class and location
        5. Recent comparable property sales and their metrics
        6. Local economic indicators (job growth, population trends, income)
        
        Prioritize data from reliable real estate sources like:
        - CBRE, JLL, Cushman & Wakefield research reports
        - CoStar and Real Capital Analytics data
        - Zillow Research, Redfin Data Center
        - Federal Reserve economic data
        - Local real estate association reports
        
        When collecting cap rates, get data specific to property class (A, B, C)
        and specific neighborhoods when possible. Always note the date of the data.
        """
    )
    
    # 2. Create specialized real estate assumption generator
    re_assumption_generator = Agent(
        name="Real Estate Assumption Modeler",
        llm={
            "model": model_id,
            "api_key": api_key,
            "temperature": temperature
        },
        tools=[thinking_tools, math_tools],
        mcp_server_url=mcp_server_url,
        instructions="""
        You are a real estate assumption modeler specializing in:
        
        1. Creating acquisition assumptions:
            - Purchase price based on target cap rates
            - Closing costs (1-2% of purchase price)
            - Property inspection and due diligence costs
        
        2. Renovation and CapEx assumptions:
            - Interior renovation costs ($5K-15K per unit depending on scope)
            - Exterior/common area improvements
            - Timing of renovations and resulting rental premiums
        
        3. Operating assumptions:
            - Rental growth rates (by scenario: conservative, base, aggressive)
            - Vacancy rates (during stabilization and post-stabilization)
            - Bad debt/collection losses (0.5-2% of potential gross income)
            - Management fees (3-5% of effective gross income)
            - Repairs and maintenance ($500-1000 per unit annually)
            - Property tax increases post-acquisition
            - Insurance costs ($350-500 per unit annually)
            - Utilities and other operating expenses
        
        4. Financing assumptions:
            - Loan-to-Value ratio (typically 65-75% for multifamily)
            - Interest rates (current market rates + spread by scenario)
            - Loan term and amortization (typically 5-10 year term, 30 year amort)
            - Debt service coverage ratio requirements (minimum 1.25x)
            - Refinancing assumptions (if applicable in hold period)
        
        5. Exit assumptions:
            - Exit cap rate (typically 0.25-0.75% higher than entry cap)
            - Sale costs (1-2% of sale price)
            - Timing of sale (5-10 year hold period)
        
        For each assumption category, provide three scenarios:
        - Conservative/Bear: Lower rent growth, higher vacancy, higher cap rates
        - Base/Most Likely: Market average performance 
        - Aggressive/Bull: Above-market performance, lower cap rates
        
        Present all assumptions in a structured JSON format with clear categorization.
        """
    )
    
    # 3. Create specialized real estate metrics deriver
    re_metrics_deriver = Agent(
        name="Real Estate Metrics Specialist",
        llm={
            "model": model_id,
            "api_key": api_key,
            "temperature": temperature
        },
        tools=[thinking_tools, math_tools],
        mcp_server_url=mcp_server_url,
        instructions="""
        You are a real estate metrics specialist. Define and calculate the following:
        
        1. Return Metrics:
            - Cash-on-Cash Return (annual)
            - Equity Multiple
            - Internal Rate of Return (IRR)
            - Net Present Value (NPV)
            - Modified Internal Rate of Return (MIRR)
            - Average Annual Return
            - Gross Rent Multiplier
        
        2. Operating Metrics:
            - Capitalization Rate (Entry and Exit)
            - Net Operating Income (NOI)
            - Gross Operating Income
            - Operating Expense Ratio
            - Debt Service Coverage Ratio
            - Break-even Ratio
        
        3. Renovation Metrics:
            - Return on Investment for Renovations
            - Rent Premium from Renovations ($ and %)
            - Renovation Cost Per Unit
            - Value-Add Metrics (NOI increase from renovations)
        
        4. Risk Metrics:
            - Sensitivity Analysis (impact of cap rate, rent growth changes)
            - Scenario Analysis (impact in bull, bear, and base cases)
            - Break-even Occupancy
            - Interest Rate Sensitivity
        
        5. Investor Metrics:
            - Cash Flow Per Unit
            - Cash Flow Per Square Foot
            - Distribution Yield
            - Preferred Return Coverage
            - Investor IRR (before and after promote/carry)
        
        For each metric, define:
            - Name
            - Formula/calculation methodology
            - Typical benchmark ranges for multifamily
            - Units/format
            - Interpretation guide
        
        Format output as structured JSON with all metrics organized by category.
        """
    )
    
    # 4. Create specialized real estate financial modeler
    re_financial_modeler = Agent(
        name="Real Estate Financial Modeler",
        llm={
            "model": model_id,
            "api_key": api_key,
            "temperature": temperature
        },
        tools=[thinking_tools, math_tools, financial_tools, file_tools],
        mcp_server_url=mcp_server_url,
        instructions="""
        You are a specialized real estate financial modeler with expertise in:
        
        1. Detailed Acquisition Pro Forma:
            - Sources and Uses of Funds
            - Initial capital stack (equity, debt, preferred equity if applicable)
            - Closing cost breakdown
        
        2. Monthly Cash Flow Projections for Year 1:
            - Unit-by-unit renovation schedule
            - Lease-up/stabilization timeline
            - Detailed revenue and expense projections
        
        3. Annual Cash Flow Projections for Hold Period:
            - Rental income with growth assumptions
            - Other income (parking, storage, amenities, etc.)
            - Detailed operating expenses by category
            - Capital expenditures schedule
            - Debt service and refinancing (if applicable)
            - Equity distributions waterfall
        
        4. Renovation Budget and Schedule:
            - Detailed renovation costs by category
            - Timeline for improvements
            - Impact on rental income and occupancy
        
        5. Sensitivity Analysis:
            - Impact of cap rate changes
            - Impact of rental growth variations
            - Impact of renovation cost overruns
            - Impact of extended lease-up periods
        
        6. Investor Returns Calculation:
            - Detailed waterfall distribution model
            - Promote/carried interest calculations
            - Preferred return tracking
            - IRR and equity multiple by investor class
        
        7. Debt Analysis:
            - Detailed loan sizing
            - Debt service coverage calculations
            - Loan covenants compliance tracking
            - Refinancing analysis (if applicable)
        
        8. Exit Analysis:
            - Detailed sale proceeds calculation
            - Capital gains analysis
            - Return of capital and profit distribution
        
        Create a comprehensive model with all these components for bull, base, and bear scenarios.
        Use MathTools for all calculations to ensure accuracy.
        Format the model as a structured JSON with clearly organized sections.
        """
    )
    
    # Create the specialized team
    re_team = Team(
        name="Real Estate Financial Modeling Team",
        agents={
            "market_researcher": re_searcher,
            "assumption_modeler": re_assumption_generator,
            "metrics_specialist": re_metrics_deriver,
            "financial_modeler": re_financial_modeler
        },
        llm={
            "model": model_id,
            "api_key": api_key,
            "temperature": temperature
        },
        tools=[thinking_tools],
        mcp_server_url=mcp_server_url,
        instructions="""
        You are the coordinator for a specialized real estate financial modeling team.
        
        Your process should follow these steps:
        
        1. Start with the Market Researcher to gather specific market data:
           - Cap rates and trends for the target market/property type
           - Rental rates and growth projections
           - Comparable property data and performance metrics
           - Renovation costs and ROI benchmarks
        
        2. Have the Assumption Modeler create detailed assumptions:
           - Acquisition assumptions based on market data
           - Renovation assumptions and timeline
           - Operating assumptions (income, expenses, growth rates)
           - Financing terms based on current market conditions
           - Exit assumptions based on market projections
        
        3. Direct the Metrics Specialist to define key performance indicators:
           - Return metrics (IRR, Equity Multiple, Cash-on-Cash)
           - Operating metrics (Cap Rate, NOI, DSCR)
           - Renovation performance metrics
           - Risk and sensitivity metrics
        
        4. Guide the Financial Modeler to build a comprehensive model:
           - Detailed acquisition and capital structure
           - Monthly cash flow for year 1 with renovation timeline
           - Annual projections for full hold period
           - Multiple scenarios (bull, base, bear)
           - Investor waterfall distributions
           - Detailed sensitivity analysis
        
        Ensure all assumptions are consistent across the models and all calculations
        are performed using MathTools for accuracy. The final output should be a
        comprehensive financial model with clearly organized sections for each
        component of the analysis.
        
        Present the results with:
        1. Executive Summary of key findings and metrics
        2. Detailed financial projections
        3. Key risk factors and mitigation strategies
        4. Investment highlights and considerations
        """
    )
    
    return {
        "market_researcher": re_searcher,
        "assumption_modeler": re_assumption_generator,
        "metrics_specialist": re_metrics_deriver,
        "financial_modeler": re_financial_modeler,
        "team": re_team
    }

def main():
    """Example usage of the specialized real estate modeling team"""
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Create the specialized team
    print("Creating specialized real estate modeling team...")
    re_team = create_real_estate_modeling_team(api_key=api_key)
    
    # Example investment opportunity
    investment_description = """
    Value-add multifamily opportunity in Austin, TX. 150-unit garden-style 
    apartment complex built in 2000, currently 92% occupied with below-market rents.
    Purchase price: $28M ($186,667/unit). Planning $3M in renovations ($20K/unit)
    to upgrade unit interiors and common areas. Current rents average $1,350/month
    with projected post-renovation rents of $1,650/month. Market cap rates are
    around 4.75% for stabilized assets. Target 5-year hold period with 70% LTV
    financing at 5.25% interest rate (30-year amortization, 5-year term).
    """
    
    print(f"\nAnalyzing investment: {investment_description.strip()}\n")
    
    # Option 1: Run the entire team
    print("\n--- Running the Entire Team ---\n")
    team_prompt = f"""
    Generate a comprehensive real estate financial model for:
    
    {investment_description}
    
    Analyze the investment opportunity with detailed projections for:
    - Acquisition and renovation strategy
    - Monthly cash flows during the renovation period
    - Annual cash flows for the 5-year hold period
    - Exit valuation and sale proceeds
    - Investor returns across multiple scenarios
    
    Include detailed assumptions for all projections and calculate all
    relevant real estate investment metrics.
    """
    
    print("Team analysis in progress... (this may take several minutes)")
    team_result = re_team["team"].run(team_prompt.strip())
    
    print("\n--- Team Analysis Complete ---\n")
    print(f"Team produced a {len(str(team_result.content))} character analysis")
    
    # Option 2: Run agents individually for more control
    print("\n--- Running Individual Agents for More Control ---\n")
    
    # Step 1: Market research
    print("Gathering market data...")
    market_prompt = f"Research current multifamily market metrics in Austin, TX relevant to this investment: {investment_description}"
    market_data = re_team["market_researcher"].agent.run(market_prompt).content
    
    # Step 2: Create assumptions
    print("Generating investment assumptions...")
    assumption_prompt = f"Create detailed acquisition, renovation, operating, and exit assumptions for this investment based on the market research: {investment_description}"
    assumptions = re_team["assumption_modeler"].agent.run(
        assumption_prompt,
        market_data=market_data
    ).content
    
    # Step 3: Define metrics
    print("Defining performance metrics...")
    metrics_prompt = f"Define the key performance metrics to evaluate this multifamily renovation project: {investment_description}"
    metrics = re_team["metrics_specialist"].agent.run(
        metrics_prompt,
        market_data=market_data,
        assumptions=assumptions
    ).content
    
    # Step 4: Build financial model
    print("Building comprehensive financial model...")
    model_prompt = f"""
    Build a detailed financial model for this value-add multifamily investment:
    
    {investment_description}
    
    Include monthly projections during the renovation period and annual 
    projections for the full 5-year hold period. Calculate investor returns
    using a detailed waterfall distribution model.
    """
    financial_model = re_team["financial_modeler"].agent.run(
        model_prompt,
        market_data=market_data,
        assumptions=assumptions,
        metrics=metrics
    ).content
    
    print("\n--- Individual Agent Analysis Complete ---\n")
    print(f"Generated {len(str(financial_model))} character financial model")
    
    # Save results to files
    print("\nSaving results to files...")
    with open("examples/output/re_market_data.json", "w") as f:
        f.write(str(market_data))
    
    with open("examples/output/re_assumptions.json", "w") as f:
        f.write(str(assumptions))
    
    with open("examples/output/re_metrics.json", "w") as f:
        f.write(str(metrics))
    
    with open("examples/output/re_financial_model.json", "w") as f:
        f.write(str(financial_model))
    
    with open("examples/output/re_team_analysis.json", "w") as f:
        f.write(str(team_result.content))
    
    print("Analysis complete! Results saved to examples/output/ directory")

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs("examples/output", exist_ok=True)
    main() 