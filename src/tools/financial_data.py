"""
Financial Data Tools using Plaid API integration.

This module provides tools for retrieving and analyzing financial data
from various sources, including the Plaid API.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PlaidDataTools:
    """
    Tools for retrieving and analyzing financial data using Plaid API.
    
    Provides methods to fetch transactions, balances, and analyze
    financial data from connected bank accounts and financial institutions.
    """
    
    def __init__(self):
        self.name = "PlaidDataTools"
        self.description = "Tools for retrieving and analyzing financial data from Plaid"
        self.base_url = "https://sandbox.plaid.com"  # Use sandbox environment by default
        self.client_id = os.environ.get("PLAID_CLIENT_ID")
        self.secret = os.environ.get("PLAID_SECRET")
    
    async def fetch_transactions(self, query: str) -> str:
        """
        Fetch transaction data from Plaid API.
        
        Args:
            query: Query containing access token and optional date range
            
        Returns:
            Transaction data in a structured format
        """
        logger.info("Fetching transactions from Plaid")
        
        # For demonstration, we'll use simulated data
        # In a real implementation, this would call the Plaid API
        
        # Extract access token and date range from query
        # In a real implementation, this would be more sophisticated
        access_token = None
        business_context = {}
        
        # Check if the query contains a context dictionary with plaid_access_token
        if isinstance(query, dict):
            if 'plaid_access_token' in query:
                access_token = query['plaid_access_token']
            
            # Extract business context for generating relevant transactions
            business_keys = ["investment_type", "industry", "stage", "revenue_model", "name", "description"]
            business_context = {k: query.get(k) for k in business_keys if k in query}
        else:
            # Try to extract token from the query string
            import re
            token_match = re.search(r"token[:\s]+([\w\-]+)", query, re.IGNORECASE)
            if token_match:
                access_token = token_match.group(1)
        
        if not access_token:
            return "No Plaid access token found. Please provide a valid access token."
        
        # Try to get transaction data via LLM if available
        try:
            from agno.models import OpenAIChat
            
            # Use LLM to generate contextually relevant transactions
            model = OpenAIChat(model_name="gpt-4o")
            
            # Create prompt based on available business context
            prompt = "Generate a list of 6-8 realistic financial transactions for "
            
            if business_context:
                if "name" in business_context and "description" in business_context:
                    prompt += f"a business named '{business_context['name']}' which is {business_context['description']}. "
                
                if "investment_type" in business_context:
                    prompt += f"This is a {business_context['investment_type']} investment. "
                
                if "industry" in business_context:
                    prompt += f"Industry: {business_context['industry']}. "
                
                if "stage" in business_context:
                    prompt += f"Stage: {business_context['stage']}. "
                
                if "revenue_model" in business_context:
                    prompt += f"Revenue model: {business_context['revenue_model']}. "
            else:
                prompt += "a typical small business. "
            
            prompt += """
            For each transaction, provide:
            1. Transaction date (within the last 7 days)
            2. Merchant/entity name
            3. Amount (positive for income, negative for expenses)
            4. Category (following common expense/income categories)
            
            Format as JSON with the following structure:
            [
                {
                    "date": "YYYY-MM-DD",
                    "name": "Merchant Name",
                    "amount": 0.00,
                    "category": ["Primary Category", "Subcategory"]
                }
            ]
            
            Include a mix of income and expenses that would be realistic for this business.
            """
            
            # Generate transactions using LLM
            transactions_json = model.generate(prompt)
            try:
                # Try to extract and parse JSON from the response
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', transactions_json, re.DOTALL)
                if json_match:
                    transactions_json = json_match.group(0)
                
                transactions = json.loads(transactions_json)
                logger.info(f"Generated {len(transactions)} contextual transactions using LLM")
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Error parsing transactions from LLM: {e}")
                # Fall back to default transactions
                raise ValueError("Could not parse LLM transactions")
        except Exception as e:
            logger.warning(f"Could not use LLM for transaction generation: {e}")
            logger.info("Using default simulated transactions")
            
            # Simulate transaction data with defaults
            transactions = [
                {
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "name": "Amazon",
                    "amount": -84.95,
                    "category": ["Shopping", "Electronics"]
                },
                {
                    "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "name": "Starbucks",
                    "amount": -5.50,
                    "category": ["Food and Drink", "Coffee Shop"]
                },
                {
                    "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "name": "Monthly Salary",
                    "amount": 4500.00,
                    "category": ["Income", "Salary"]
                },
                {
                    "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                    "name": "Rent Payment",
                    "amount": -1800.00,
                    "category": ["Housing", "Rent"]
                },
                {
                    "date": (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d"),
                    "name": "Utility Bill",
                    "amount": -135.27,
                    "category": ["Housing", "Utilities"]
                }
            ]
        
        # Format the transaction data for response
        response = "# Recent Transactions\n\n"
        response += "| Date | Description | Amount | Category |\n"
        response += "|------|-------------|--------|----------|\n"
        
        for txn in transactions:
            amount_str = f"${abs(txn['amount']):.2f}"
            if txn['amount'] < 0:
                amount_str = f"-{amount_str}"
            else:
                amount_str = f"+{amount_str}"
            
            response += f"| {txn['date']} | {txn['name']} | {amount_str} | {', '.join(txn['category'])} |\n"
        
        response += "\n**Note:** This is simulated transaction data. In a production environment, real transaction data would be retrieved from the Plaid API."
        
        return response
    
    async def fetch_account_balances(self, query: str) -> str:
        """
        Fetch account balance data from Plaid API.
        
        Args:
            query: Query containing access token
            
        Returns:
            Account balance data in a structured format
        """
        logger.info("Fetching account balances from Plaid")
        
        # For demonstration, we'll use simulated data
        # In a real implementation, this would call the Plaid API
        
        # Extract access token from query
        # In a real implementation, this would be more sophisticated
        access_token = None
        
        # Check if the query contains a context dictionary with plaid_access_token
        if isinstance(query, dict) and 'plaid_access_token' in query:
            access_token = query['plaid_access_token']
        else:
            # Try to extract token from the query string
            import re
            token_match = re.search(r"token[:\s]+([\w\-]+)", query, re.IGNORECASE)
            if token_match:
                access_token = token_match.group(1)
        
        if not access_token:
            return "No Plaid access token found. Please provide a valid access token."
        
        # Simulate account data (this would come from Plaid API in production)
        simulated_accounts = [
            {
                "account_id": "checking-123",
                "name": "Checking Account",
                "type": "depository",
                "subtype": "checking",
                "balances": {
                    "current": 5240.23,
                    "available": 5240.23,
                    "iso_currency_code": "USD"
                }
            },
            {
                "account_id": "savings-456",
                "name": "Savings Account",
                "type": "depository",
                "subtype": "savings",
                "balances": {
                    "current": 12750.00,
                    "available": 12750.00,
                    "iso_currency_code": "USD"
                }
            },
            {
                "account_id": "creditcard-789",
                "name": "Credit Card",
                "type": "credit",
                "subtype": "credit card",
                "balances": {
                    "current": -2340.56,
                    "available": 15159.44,
                    "limit": 17500.00,
                    "iso_currency_code": "USD"
                }
            }
        ]
        
        # Format the account data for response
        response = "# Account Balances\n\n"
        response += "| Account | Type | Current Balance | Available Balance |\n"
        response += "|---------|------|----------------|-------------------|\n"
        
        total_assets = 0
        total_liabilities = 0
        
        for acct in simulated_accounts:
            current_balance = acct["balances"]["current"]
            available_balance = acct["balances"].get("available", current_balance)
            
            # Format the balances
            if acct["type"] == "credit":
                current_balance_str = f"-${abs(current_balance):.2f}"
                available_balance_str = f"${available_balance:.2f}"
                total_liabilities += abs(current_balance)
            else:
                current_balance_str = f"${current_balance:.2f}"
                available_balance_str = f"${available_balance:.2f}"
                total_assets += current_balance
            
            response += f"| {acct['name']} | {acct['subtype'].replace('_', ' ').title()} | {current_balance_str} | {available_balance_str} |\n"
        
        # Add summary
        net_worth = total_assets - total_liabilities
        net_worth_str = f"${net_worth:.2f}" if net_worth >= 0 else f"-${abs(net_worth):.2f}"
        
        response += f"\n## Summary\n"
        response += f"- **Total Assets:** ${total_assets:.2f}\n"
        response += f"- **Total Liabilities:** ${total_liabilities:.2f}\n"
        response += f"- **Net Worth:** {net_worth_str}\n\n"
        
        response += "**Note:** This is simulated account data. In a production environment, real account data would be retrieved from the Plaid API."
        
        return response
    
    async def analyze_spending(self, query: str) -> str:
        """
        Analyze spending patterns from transaction data.
        
        Args:
            query: Query containing access token and optional time period
            
        Returns:
            Spending analysis with category breakdowns and insights
        """
        logger.info("Analyzing spending patterns")
        
        # For demonstration, we'll use simulated data
        # In a real implementation, this would analyze real transaction data from Plaid
        
        # Extract business context for more relevant analysis
        business_context = {}
        if isinstance(query, dict):
            # Extract business context for generating relevant analysis
            business_keys = ["investment_type", "industry", "stage", "revenue_model", "name", "description"]
            business_context = {k: query.get(k) for k in business_keys if k in query}
        
        # Try to generate spending analysis via LLM if available
        try:
            from agno.models import OpenAIChat
            
            # Use LLM to generate contextually relevant spending analysis
            model = OpenAIChat(model_name="gpt-4o")
            
            # Create prompt based on available business context
            prompt = "Generate a realistic spending analysis with categories, amounts, and insights for "
            
            if business_context:
                if "name" in business_context and "description" in business_context:
                    prompt += f"a business named '{business_context['name']}' which is {business_context['description']}. "
                
                if "investment_type" in business_context:
                    prompt += f"This is a {business_context['investment_type']} investment. "
                
                if "industry" in business_context:
                    prompt += f"Industry: {business_context['industry']}. "
                
                if "stage" in business_context:
                    prompt += f"Stage: {business_context['stage']}. "
                
                if "revenue_model" in business_context:
                    prompt += f"Revenue model: {business_context['revenue_model']}. "
            else:
                prompt += "a typical small business. "
            
            prompt += """
            Provide the following:
            
            1. Total monthly spending (a realistic amount)
            2. 7-9 spending categories with:
               - Category name
               - Monthly amount spent
               - Percentage of total spending
            3. 3-4 insights about the spending patterns
            
            Format the spending categories as a JSON list with this structure:
            [
                {
                    "category": "Category Name",
                    "amount": 1234.56,
                    "percentage": 12.3
                }
            ]
            
            Then provide insights as a simple list, each one on a new line starting with a dash (-).
            
            Make sure the percentages add up to approximately 100%.
            """
            
            # Generate spending analysis using LLM
            spending_analysis = model.generate(prompt)
            
            # Extract JSON array for spending categories
            import re
            categories_match = re.search(r'\[\s*\{.*\}\s*\]', spending_analysis, re.DOTALL)
            if categories_match:
                categories_json = categories_match.group(0)
                spending_categories = json.loads(categories_json)
                logger.info(f"Generated spending analysis with {len(spending_categories)} categories using LLM")
                
                # Extract insights
                insights = []
                insights_section = spending_analysis.split(categories_json)[-1].strip()
                for line in insights_section.split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        insights.append(line[1:].strip())
            else:
                raise ValueError("Could not extract spending categories from LLM response")
                
        except Exception as e:
            logger.warning(f"Could not use LLM for spending analysis: {e}")
            logger.info("Using default simulated spending analysis")
            
            # Simulate spending analysis with default data
            spending_categories = [
                {"category": "Housing", "amount": 2100.00, "percentage": 35},
                {"category": "Food & Dining", "amount": 800.00, "percentage": 13.3},
                {"category": "Transportation", "amount": 450.00, "percentage": 7.5},
                {"category": "Shopping", "amount": 750.00, "percentage": 12.5},
                {"category": "Entertainment", "amount": 350.00, "percentage": 5.8},
                {"category": "Personal Care", "amount": 200.00, "percentage": 3.3},
                {"category": "Health & Fitness", "amount": 300.00, "percentage": 5},
                {"category": "Utilities", "amount": 450.00, "percentage": 7.5},
                {"category": "Other", "amount": 600.00, "percentage": 10}
            ]
            
            # Default insights
            insights = [
                "Housing is your largest expense category at 35% of total spending.",
                "Your Food & Dining expenses are slightly above the recommended 10-15% of monthly spending.",
                "Your spending in Entertainment and Personal Care categories is well-balanced."
            ]
        
        total_spending = sum(category["amount"] for category in spending_categories)
        
        # Format the spending analysis for response
        response = "# Spending Analysis\n\n"
        response += f"**Total Monthly Spending:** ${total_spending:.2f}\n\n"
        
        response += "## Spending by Category\n\n"
        response += "| Category | Amount | % of Total |\n"
        response += "|----------|--------|------------|\n"
        
        for category in sorted(spending_categories, key=lambda x: x["amount"], reverse=True):
            response += f"| {category['category']} | ${category['amount']:.2f} | {category['percentage']}% |\n"
        
        # Add insights
        response += "\n## Insights\n\n"
        for insight in insights:
            response += f"- {insight}\n"
        
        response += "\n**Note:** This is a simulated spending analysis. In a production environment, real transaction data would be analyzed from the Plaid API."
        
        return response
    
    async def calculate_financial_metrics(self, query: str) -> str:
        """
        Calculate key financial metrics based on account data.
        
        Args:
            query: Query containing access token and optional parameters
            
        Returns:
            Key financial metrics and ratios
        """
        logger.info("Calculating financial metrics")
        
        # Parse query to extract context for metrics calculation
        business_context = {}
        if isinstance(query, dict):
            # Extract business context for generating relevant metrics
            context_keys = ["investment_type", "industry", "stage", "revenue_model", "monthly_income", 
                           "monthly_expenses", "assets", "liabilities", "cash_balance"]
            business_context = {k: query.get(k) for k in context_keys if k in query}
        
        # Try to generate financial metrics using LLM
        try:
            from agno.models import OpenAIChat
            
            # Use LLM to generate contextually relevant financial metrics
            model = OpenAIChat(model_name="gpt-4o")
            
            # Create base financial data to work with (from query or defaults)
            financial_data = {
                "monthly_income": business_context.get("monthly_income", 4500.00),
                "monthly_expenses": business_context.get("monthly_expenses", 4000.00),
                "cash_balance": business_context.get("cash_balance", 15000.00),
                "assets": business_context.get("assets", 35000.00),
                "liabilities": business_context.get("liabilities", 20000.00)
            }
            
            # Create prompt for financial metrics
            prompt = f"""
            Calculate key financial metrics and provide analysis based on the following financial data:
            
            Financial Data:
            - Monthly Income: ${financial_data['monthly_income']:.2f}
            - Monthly Expenses: ${financial_data['monthly_expenses']:.2f}
            - Cash Balance: ${financial_data['cash_balance']:.2f}
            - Assets: ${financial_data['assets']:.2f}
            - Liabilities: ${financial_data['liabilities']:.2f}
            
            """
            
            # Add investment type context if available
            if "investment_type" in business_context:
                prompt += f"Investment Type: {business_context['investment_type']}\n"
            if "industry" in business_context:
                prompt += f"Industry: {business_context['industry']}\n"
            if "stage" in business_context:
                prompt += f"Stage: {business_context['stage']}\n"
            
            prompt += """
            Please calculate the following key financial metrics:
            1. Debt-to-Income Ratio
            2. Savings Rate (as a percentage of income)
            3. Emergency Fund Ratio (in months)
            4. Net Worth
            5. Monthly Free Cash Flow
            
            Additionally, provide a short analysis of each metric with recommendations:
            - Whether the Debt-to-Income Ratio is healthy (ideally < 0.36)
            - Whether the Savings Rate is adequate (ideally > 15%)
            - Whether the Emergency Fund is sufficient (ideally 3-6 months)
            - Whether the Monthly Free Cash Flow is positive or concerning
            
            Format your response as a Markdown report with:
            1. A numeric value for each metric
            2. Clear sections for each metric category
            3. Recommendations for each metric
            
            Be specific about whether each metric is within recommended ranges.
            """
            
            # Generate financial metrics using LLM
            financial_metrics_report = model.generate(prompt)
            
            if financial_metrics_report and len(financial_metrics_report) > 200:
                logger.info(f"Generated financial metrics using LLM")
                return financial_metrics_report
                
        except Exception as e:
            logger.warning(f"Could not generate financial metrics with LLM: {e}")
            logger.info("Using template financial metrics")
        
        # If LLM is not available or fails, calculate basic metrics from available data
        monthly_income = business_context.get("monthly_income", 4500.00)
        monthly_expenses = business_context.get("monthly_expenses", 4000.00)
        cash_balance = business_context.get("cash_balance", 15000.00)
        assets = business_context.get("assets", 35000.00)
        liabilities = business_context.get("liabilities", 20000.00)
        
        # Calculate basic metrics
        debt_to_income_ratio = liabilities / (monthly_income * 12) if monthly_income > 0 else 0.32
        savings_rate = (monthly_income - monthly_expenses) / monthly_income if monthly_income > 0 else 0.11
        emergency_fund_ratio = cash_balance / monthly_expenses if monthly_expenses > 0 else 3.2
        net_worth = assets - liabilities
        monthly_free_cash_flow = monthly_income - monthly_expenses
        
        # Format the financial metrics for response
        response = "# Key Financial Metrics\n\n"
        
        response += "## Income & Expenses\n\n"
        response += f"- **Monthly Income:** ${monthly_income:.2f}\n"
        response += f"- **Monthly Expenses:** ${monthly_expenses:.2f}\n"
        response += f"- **Monthly Free Cash Flow:** ${monthly_free_cash_flow:.2f}\n\n"
        
        response += "## Financial Ratios\n\n"
        response += f"- **Debt-to-Income Ratio:** {debt_to_income_ratio:.2f} (Recommended: < 0.36)\n"
        response += f"- **Savings Rate:** {savings_rate:.2f} or {savings_rate*100:.1f}% (Recommended: > 0.15 or 15%)\n"
        response += f"- **Emergency Fund Ratio:** {emergency_fund_ratio:.1f} months (Recommended: 3-6 months)\n\n"
        
        response += "## Net Worth\n\n"
        response += f"- **Current Net Worth:** ${net_worth:.2f}\n\n"
        
        # Add insights based on metrics
        response += "## Analysis\n\n"
        
        if debt_to_income_ratio > 0.36:
            response += "- **Warning:** Your debt-to-income ratio is high. Consider reducing debt or increasing income.\n"
        else:
            response += "- **Good:** Your debt-to-income ratio is within healthy limits.\n"
        
        if savings_rate < 0.10:
            response += "- **Warning:** Your savings rate is low. Aim to save at least 10-15% of income.\n"
        else:
            response += "- **Good:** Your savings rate is healthy.\n"
        
        if emergency_fund_ratio < 3:
            response += "- **Warning:** Your emergency fund could be improved. Aim for 3-6 months of expenses.\n"
        else:
            response += "- **Good:** Your emergency fund is adequate.\n"
        
        if monthly_free_cash_flow < 0:
            response += "- **Warning:** You're spending more than you earn. Review your budget to reduce expenses.\n"
        else:
            response += "- **Good:** You have positive cash flow each month.\n"
        
        response += "\n**Note:** This is a simplified financial metrics report. In a production environment, metrics would be calculated from actual financial data retrieved from the Plaid API."
        
        return response 