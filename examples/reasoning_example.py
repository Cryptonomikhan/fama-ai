#!/usr/bin/env python3
"""
Reasoning Example for Fama AI.

This example demonstrates how to use the thinking tools with Agno agents
to enable structured reasoning for complex tasks.
"""
import os
import sys
import logging
from textwrap import dedent
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.agent import Agent

from models.model_factory import create_model
from tools.thinking_tools import ThinkingTool, FinancialReasoningTool, CodeReasoningTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to run the reasoning example.
    """
    # Example 1: Basic Thinking Tool with Generic Reasoning
    run_basic_thinking_example()
    
    # Example 2: Financial Reasoning for Investment Analysis
    run_financial_reasoning_example()
    
    # Example 3: Code Reasoning for Dashboard Component Design
    run_code_reasoning_example()
    
    # Example 4: Advanced Reasoning with Multiple Tools
    run_advanced_reasoning_example()

def run_basic_thinking_example():
    """
    Run an example with the basic thinking tool.
    """
    logger.info("Running basic thinking tool example...")
    
    # Create a model for the agent - using a strong reasoning model
    model = create_model(
        provider="anthropic",  # Using Claude for this example
        model_id="claude-3-opus-20240229",
        temperature=0.2
    )
    
    # Initialize the agent with the thinking tool
    agent = Agent(
        model=model,
        name="Reasoning Agent",
        role="Analytical thinker for complex problems",
        description="An expert in structured reasoning and problem-solving",
        instructions=[
            "When faced with a complex problem, use the thinking tool to break it down",
            "Work through each step methodically, considering alternatives",
            "Validate your assumptions and check your work",
            "Present a clear, well-reasoned conclusion"
        ],
        tools=[ThinkingTool()],
        markdown=True,
        show_tool_calls=True
    )
    
    # Run the agent with a complex problem
    problem = """
    A tech startup is considering three different pricing models for their SaaS product:
    1. Freemium: Basic features free, premium features paid ($20/month)
    2. Tiered: Basic ($10/month), Professional ($25/month), Enterprise ($50/month)
    3. Usage-based: $0.10 per API call with a minimum of $5/month
    
    Based on market research, they estimate:
    - 10,000 users would use the free tier and 2,000 would convert to premium in the Freemium model
    - 5,000 Basic, 3,000 Professional, and 1,000 Enterprise users in the Tiered model
    - Average API calls would be 100 per user per month with 8,000 total users in the Usage-based model
    
    Which pricing model would generate the highest revenue? Explain your reasoning.
    """
    
    logger.info("Sending problem to reasoning agent...")
    response = agent.run(problem)
    logger.info("Basic reasoning example completed")
    
    # Print the response content
    print("\n\n=== BASIC REASONING EXAMPLE RESPONSE ===\n")
    print(response.content)
    print("\n======================================\n\n")

def run_financial_reasoning_example():
    """
    Run an example with the financial reasoning tool.
    """
    logger.info("Running financial reasoning tool example...")
    
    # Create a model for the agent
    model = create_model(
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        temperature=0.1
    )
    
    # Initialize the agent with the financial reasoning tool
    agent = Agent(
        model=model,
        name="Financial Reasoning Agent",
        role="Financial analyst for investment decisions",
        description="An expert in financial analysis and investment evaluation",
        instructions=[
            "Use the financial_reasoning tool to work through complex financial problems",
            "Break down calculations into clear steps",
            "Document all assumptions explicitly",
            "Validate calculations and check for errors",
            "Provide a clear investment recommendation with justification"
        ],
        tools=[FinancialReasoningTool()],
        markdown=True,
        show_tool_calls=True
    )
    
    # Run the agent with a financial analysis problem
    problem = """
    Evaluate a potential real estate investment with the following characteristics:
    
    - Purchase price: $500,000
    - Down payment: 25% ($125,000)
    - Loan terms: 30-year fixed at 4.5% interest
    - Expected monthly rent: $3,200
    - Property management fee: 8% of rental income
    - Property tax: $5,000 per year
    - Insurance: $1,800 per year
    - Maintenance: 5% of rental income
    - Vacancy rate: 5% average
    - Expected property value appreciation: 3% annually
    - Time horizon: 10 years
    
    Calculate:
    1. Monthly mortgage payment
    2. Annual cash flow
    3. Cash-on-cash return
    4. Cap rate
    5. Internal Rate of Return (IRR) for the 10-year period
    6. Return on Investment (ROI) for the 10-year period
    
    Based on these calculations, would you recommend this investment? Why or why not?
    """
    
    logger.info("Sending financial problem to reasoning agent...")
    response = agent.run(problem)
    logger.info("Financial reasoning example completed")
    
    # Print the response content
    print("\n\n=== FINANCIAL REASONING EXAMPLE RESPONSE ===\n")
    print(response.content)
    print("\n======================================\n\n")

def run_code_reasoning_example():
    """
    Run an example with the code reasoning tool.
    """
    logger.info("Running code reasoning tool example...")
    
    # Create a model for the agent
    model = create_model(
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        temperature=0.2
    )
    
    # Initialize the agent with the code reasoning tool
    agent = Agent(
        model=model,
        name="Code Reasoning Agent",
        role="Software architect for financial dashboards",
        description="An expert in designing and implementing financial dashboard components",
        instructions=[
            "Use the code_reasoning tool to work through complex coding problems",
            "Think carefully about component architecture and data flow",
            "Consider performance implications of design choices",
            "Design for maintainability and extensibility",
            "Follow React and Next.js best practices"
        ],
        tools=[CodeReasoningTool()],
        markdown=True,
        show_tool_calls=True
    )
    
    # Run the agent with a code design problem
    problem = """
    Design a React component for a Next.js financial dashboard that visualizes scenario analysis results.
    
    The component should:
    1. Display baseline, bull, and bear scenarios side-by-side
    2. Visualize key metrics (IRR, NPV, ROI) for each scenario using charts
    3. Allow users to toggle between different visualization types (bar charts, line charts)
    4. Include a comparison table showing percentage differences between scenarios
    5. Be responsive and work well on mobile devices
    6. Include proper error handling for missing or incomplete data
    
    Provide:
    - Component architecture
    - Key React hooks needed
    - Data structure design
    - Implementation of the main component
    """
    
    logger.info("Sending code problem to reasoning agent...")
    response = agent.run(problem)
    logger.info("Code reasoning example completed")
    
    # Print the response content
    print("\n\n=== CODE REASONING EXAMPLE RESPONSE ===\n")
    print(response.content)
    print("\n======================================\n\n")

def run_advanced_reasoning_example():
    """
    Run an example with multiple reasoning tools.
    """
    logger.info("Running advanced reasoning example with multiple tools...")
    
    # Create a model for the agent
    model = create_model(
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        temperature=0.2
    )
    
    # Initialize the agent with multiple reasoning tools
    agent = Agent(
        model=model,
        name="Advanced Reasoning Agent",
        role="Financial dashboard expert",
        description=dedent("""
            An expert in both financial analysis and software development,
            specialized in creating interactive financial dashboards for investment analysis.
        """),
        instructions=[
            "Use the think tool for general problem solving",
            "Use the financial_reasoning tool for financial calculations",
            "Use the code_reasoning tool for software design",
            "Break complex problems into clear steps",
            "Validate all assumptions and calculations",
            "Present solutions that combine financial insight with technical implementation"
        ],
        tools=[ThinkingTool(), FinancialReasoningTool(), CodeReasoningTool()],
        markdown=True,
        show_tool_calls=True
    )
    
    # Run the agent with a complex problem requiring multiple types of reasoning
    problem = """
    Your task is to design a Next.js dashboard component for a tokenized real estate investment that:
    
    1. Analyzes the following investment data:
       - Initial investment: $10M for a portfolio of 5 commercial properties
       - Expected annual rental yield: 7.5%
       - Property management costs: 15% of rental income
       - Expected appreciation: 3.5% annually
       - Token liquidity discount: 2% of total value
       - Investment timeframe: 8 years
    
    2. Creates an interactive dashboard with:
       - Financial metrics calculation (IRR, ROI, NPV)
       - Scenario comparison (baseline, bull, bear)
       - Sensitivity analysis for key parameters
       - Tokenization benefits visualization
    
    Provide both:
    - The financial analysis with calculations showing expected returns
    - The code architecture and implementation for the dashboard component
    """
    
    logger.info("Sending complex problem to advanced reasoning agent...")
    response = agent.run(problem)
    logger.info("Advanced reasoning example completed")
    
    # Print the response content
    print("\n\n=== ADVANCED REASONING EXAMPLE RESPONSE ===\n")
    print(response.content)
    print("\n======================================\n\n")

if __name__ == "__main__":
    main() 