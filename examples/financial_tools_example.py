from src.tools.financial_calculations import FinancialCalculationTools
from src.tools.model_formatting import ModelFormattingTools
from agno.agent import Agent
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def main():
    # Initialize the toolkits
    financial_tools = FinancialCalculationTools()
    formatting_tools = ModelFormattingTools()
    
    print("Financial Modeling Tools Example")
    print("================================\n")
    
    # Example 1: DCF Analysis
    print("Example 1: DCF Analysis")
    cash_flows = [-100000, 25000, 35000, 45000, 50000, 60000]
    discount_rate = 0.08
    
    dcf_result = financial_tools.calculate_dcf(cash_flows, discount_rate)
    print(f"NPV: ${dcf_result['npv']}")
    print(f"Discounted Cash Flows: {dcf_result['discounted_cash_flows']}")
    print(f"Cumulative DCF: {dcf_result['cumulative_dcf']}\n")
    
    # Example 2: IRR Calculation
    print("Example 2: IRR Calculation")
    irr_result = financial_tools.calculate_irr(cash_flows)
    print(f"IRR: {irr_result['irr']}%\n")
    
    # Example 3: Income Statement
    print("Example 3: Income Statement")
    periods = ["Year 1", "Year 2", "Year 3"]
    revenue = [500000, 600000, 750000]
    cogs = [200000, 230000, 280000]
    operating_expenses = [150000, 165000, 180000]
    taxes = [45000, 61500, 87000]
    
    income_statement = financial_tools.build_income_statement(
        revenue, cogs, operating_expenses, taxes, periods
    )
    
    # Format as markdown
    income_statement_md = financial_tools.format_financial_data(income_statement, "markdown")
    print(income_statement_md)
    
    # Example 4: Cash Flow Statement
    print("Example 4: Cash Flow Statement")
    net_income = [105000, 143500, 203000]
    depreciation = [30000, 30000, 30000]
    changes_in_working_capital = [-15000, -20000, -25000]
    capital_expenditures = [-50000, -60000, -70000]
    financing_cash_flows = [-20000, -30000, -40000]
    
    cash_flow_statement = financial_tools.build_cash_flow_statement(
        net_income, depreciation, changes_in_working_capital, 
        capital_expenditures, financing_cash_flows, periods
    )
    
    # Format as markdown
    cash_flow_md = financial_tools.format_financial_data(cash_flow_statement, "markdown")
    print(cash_flow_md)
    
    # Example 5: Scenario Analysis
    print("Example 5: Scenario Analysis")
    scenario_names = ["Bear Case", "Base Case", "Bull Case"]
    revenue_projections = [
        [400000, 450000, 500000],  # Bear
        [500000, 600000, 750000],  # Base
        [600000, 800000, 1000000]  # Bull
    ]
    cost_projections = [
        [350000, 380000, 410000],  # Bear
        [350000, 395000, 460000],  # Base
        [350000, 420000, 520000]   # Bull
    ]
    discount_rates = [0.10, 0.08, 0.06]  # Different rates for different scenarios
    
    scenario_results = financial_tools.scenario_analysis(
        scenario_names, revenue_projections, cost_projections, 
        discount_rates, periods
    )
    
    # Format as markdown
    scenario_md = financial_tools.format_financial_data(scenario_results, "markdown")
    print(scenario_md)
    
    # Example 6: Generate Visualization
    print("Example 6: Generate Visualization")
    # Visualization of income statement
    income_visualization = formatting_tools.generate_visualization(
        income_statement,
        chart_type="bar",
        title="Income Statement",
        x_label="Year",
        y_label="Amount ($)",
        series_to_plot=["revenue", "net_income", "operating_income"]
    )
    print(income_visualization)
    
    # Visualization of scenario analysis
    scenario_visualization = formatting_tools.generate_visualization(
        scenario_results,
        chart_type="line",
        title="Profit Projections by Scenario",
        x_label="Year",
        y_label="Profit ($)"
    )
    print(scenario_visualization)
    
    # Example 7: Create a comprehensive model summary
    print("Example 7: Comprehensive Model Summary")
    key_metrics = {
        "npv": dcf_result["npv"],
        "irr": irr_result["irr"],
        "payback_period": 2.5,
        "total_investment": 100000,
        "average_annual_return": 23.5
    }
    
    model_summary = formatting_tools.format_model_summary(
        model_name="AI Server Farm Investment Model",
        income_statement=income_statement,
        cash_flow_statement=cash_flow_statement,
        scenario_analysis=scenario_results,
        key_metrics=key_metrics,
        format_type="markdown"
    )
    
    print(model_summary)
    
    # Example 8: Using the tools with an Agent
    print("\nExample 8: Using the tools with an Agent")
    agent = Agent(
        tools=[financial_tools, formatting_tools],
        show_tool_calls=True,
        markdown=True
    )
    
    query = """
    Given the following financial data:
    - Initial investment: $100,000
    - Cash flows for 5 years: $25,000, $35,000, $45,000, $50,000, $60,000
    - Discount rate: 8%
    
    Calculate the NPV, IRR, and payback period. Then create a simple visualization 
    of the discounted cash flows.
    """
    
    print("Query:", query)
    response = agent.run(query)
    print("\nAgent response:")
    print(response.content)


if __name__ == "__main__":
    main() 