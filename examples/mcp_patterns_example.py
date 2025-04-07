#!/usr/bin/env python3
"""
MCP Usage Patterns Example

This script demonstrates recommended patterns and best practices for using
Model Context Protocol (MCP) with the Financial Modeling API.

It covers:
1. Common MCP usage patterns and configurations
2. Best practices for different use cases
3. Performance considerations
4. Security recommendations

Each pattern is shown with a complete working example.
"""

import os
import sys
import json
import tempfile
import requests
import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

# Create a console for pretty output
console = Console()

# API endpoint
API_URL = "http://localhost:8000/task/submit"

def create_test_directory():
    """Create a temporary directory with test files for demonstrating MCP patterns"""
    temp_dir = tempfile.mkdtemp(prefix="mcp_patterns_")
    console.print(f"Created temporary directory: [bold cyan]{temp_dir}[/bold cyan]\n")
    
    # Create subdirectories for different data types
    os.makedirs(os.path.join(temp_dir, "financial_data"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "market_research"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "reports"), exist_ok=True)
    
    # Create financial data files
    financial_sample = {
        "balance_sheet": {
            "assets": {
                "current_assets": {
                    "cash": 1250000,
                    "accounts_receivable": 750000,
                    "inventory": 500000,
                    "prepaid_expenses": 125000
                },
                "non_current_assets": {
                    "property_plant_equipment": 3500000,
                    "intangible_assets": 1200000,
                    "investments": 800000
                }
            },
            "liabilities": {
                "current_liabilities": {
                    "accounts_payable": 450000,
                    "short_term_debt": 300000,
                    "accrued_expenses": 175000
                },
                "non_current_liabilities": {
                    "long_term_debt": 2500000,
                    "deferred_tax": 350000
                }
            },
            "equity": {
                "common_stock": 1000000,
                "retained_earnings": 3800000
            }
        },
        "income_statement": {
            "revenue": 5200000,
            "cost_of_goods_sold": 2800000,
            "gross_profit": 2400000,
            "operating_expenses": {
                "salaries": 1100000,
                "marketing": 300000,
                "rent": 200000,
                "utilities": 100000,
                "other": 150000
            },
            "operating_income": 550000,
            "interest_expense": 125000,
            "income_before_tax": 425000,
            "income_tax": 85000,
            "net_income": 340000
        },
        "cash_flow": {
            "operating_activities": {
                "net_income": 340000,
                "depreciation": 175000,
                "changes_in_working_capital": -120000,
                "cash_from_operations": 395000
            },
            "investing_activities": {
                "capital_expenditures": -250000,
                "acquisitions": -100000,
                "cash_from_investing": -350000
            },
            "financing_activities": {
                "debt_repayment": -150000,
                "dividends": -100000,
                "cash_from_financing": -250000
            },
            "net_change_in_cash": -205000
        }
    }
    
    with open(os.path.join(temp_dir, "financial_data", "financial_statements.json"), "w") as f:
        json.dump(financial_sample, f, indent=2)
    
    # Create market research files
    market_research = """# Market Analysis Report

## Industry Overview

The SaaS market is expected to grow at a CAGR of 11.7% from 2022 to 2028, reaching a market value of $702.19 billion by 2028.

## Key Competitors

1. **Competitor A**
   - Market Share: 24.5%
   - Annual Revenue: $1.2B
   - Key Products: Product X, Product Y

2. **Competitor B**
   - Market Share: 18.2%
   - Annual Revenue: $950M
   - Key Products: Product Z

3. **Competitor C**
   - Market Share: 12.8%
   - Annual Revenue: $720M
   - Key Products: Product W

## Target Market

The primary target market consists of mid-sized enterprises with:
- 100-1000 employees
- $10M-$100M annual revenue
- Technology-forward mindset
- Global operations

## Growth Opportunities

1. Expansion into healthcare vertical
2. Integration with emerging AI technologies
3. Development of mobile-first solutions
"""
    
    with open(os.path.join(temp_dir, "market_research", "market_analysis.md"), "w") as f:
        f.write(market_research)
    
    # Create configuration file
    config = {
        "project": {
            "name": "Financial Analysis Demo",
            "version": "1.0.0",
            "settings": {
                "currency": "USD",
                "fiscal_year_end": "12-31",
                "reporting_period": "quarterly"
            }
        },
        "analysis_parameters": {
            "discount_rate": 0.08,
            "growth_rate": 0.05,
            "inflation_rate": 0.025,
            "tax_rate": 0.21
        },
        "scenarios": {
            "base_case": {
                "growth_rate": 0.05,
                "margin_improvement": 0.01
            },
            "upside_case": {
                "growth_rate": 0.08,
                "margin_improvement": 0.02
            },
            "downside_case": {
                "growth_rate": 0.02,
                "margin_improvement": 0.00
            }
        }
    }
    
    with open(os.path.join(temp_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    
    console.print("Created sample directory structure with files:")
    console.print("  • [bold]financial_data/financial_statements.json[/bold]: Company financial data")
    console.print("  • [bold]market_research/market_analysis.md[/bold]: Market research document")
    console.print("  • [bold]config.json[/bold]: Project configuration file")
    console.print("  • [bold]reports/[/bold]: Empty directory for generated reports")
    console.print("\n")
    
    return temp_dir

def pattern_filesystem_read_only(data_directory, api_key):
    """Pattern 1: Read-only Filesystem MCP (most common and safest pattern)"""
    console.print(Panel(
        "Pattern 1: Read-only Filesystem MCP Access\n"
        "This pattern provides the AI with read-only access to a specific data directory.\n"
        "It's the most common and safest pattern for MCP usage.",
        title="MCP Pattern 1",
        subtitle="Best for data analysis tasks",
        style="green"
    ))
    
    # Create request payload focusing on read-only filesystem access
    payload = {
        "task": "Analyze the financial statements in the financial_data directory. Create a summary of the company's financial health, profitability, and key financial ratios. Also reference the market research document to provide context for the company's performance relative to the industry.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": api_key,
        "stream": False,
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory
    }
    
    console.print("\n[bold]Key best practices demonstrated:[/bold]")
    console.print("1. Limit access to a specific directory only")
    console.print("2. Use filesystem MCP in read-only mode")
    console.print("3. Provide clear instructions about which files to analyze")
    console.print("4. Keep MCP configuration minimal for security")
    
    # Display request information
    console.print("\n[bold]API Request:[/bold]")
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    
    # Ask user if they want to run this example
    if Prompt.ask("\nRun this example?", choices=["y", "n"], default="y") == "y":
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Sending request to API...", total=None)
                response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                console.print(Panel(
                    Markdown(response.text),
                    title="Analysis Results",
                    subtitle="Using Read-only Filesystem MCP",
                    width=100
                ))
            else:
                console.print(f"[bold red]Error {response.status_code}:[/bold red] {response.text}")
        except Exception as e:
            console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
    
    console.print("\n")
    return

def pattern_multiple_mcp_servers(data_directory, api_key):
    """Pattern 2: Combining filesystem MCP with specialized tool servers"""
    console.print(Panel(
        "Pattern 2: Multiple MCP Servers\n"
        "This pattern combines filesystem access with specialized tool servers to extend AI capabilities.\n"
        "It demonstrates how to use multiple MCP servers with different purposes simultaneously.",
        title="MCP Pattern 2",
        subtitle="Best for advanced analysis with specialized tools",
        style="green"
    ))
    
    # Create request payload with multiple MCP servers
    payload = {
        "task": "Analyze the financial data in financial_statements.json. Use the financial tools MCP server to calculate advanced financial metrics like WACC, EVA, and ROI. Then use the market data server to compare these metrics with industry benchmarks mentioned in the market research document.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": api_key,
        "stream": False,
        # Enable filesystem MCP
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory,
        # Configure custom MCP servers
        "mcp_servers": [
            {
                "command": "npx",
                "args": ["-y", "@financialtools/mcp-server"],
                "env": {
                    "API_KEY": "test-financial-tools-key",
                    "MODE": "analytical"
                }
            },
            {
                "command": "npx -y @marketdata/mcp-server",
                "env": {
                    "API_KEY": "test-market-data-key",
                    "DATA_SOURCE": "premium"
                }
            }
        ]
    }
    
    console.print("\n[bold]Key best practices demonstrated:[/bold]")
    console.print("1. Combining filesystem access with specialized tool servers")
    console.print("2. Providing clear server-specific environment variables")
    console.print("3. Using consistent command format across servers")
    console.print("4. Ensuring each server has a specific, focused purpose")
    
    # Display request information
    console.print("\n[bold]API Request:[/bold]")
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    
    console.print("\n[bold yellow]Note:[/bold yellow] This example uses placeholder MCP servers that may not be installed on your system.")
    console.print("In a real implementation, you would need to install these packages or provide valid commands.")
    
    # For this example, we'll skip the actual execution since the servers are placeholders
    console.print("\n[bold]Implementation notes:[/bold]")
    console.print("1. Each MCP server runs in its own process")
    console.print("2. The API handles server startup, connection, and termination")
    console.print("3. Error handling ensures API continues even if an MCP server fails")
    console.print("4. Resources are automatically cleaned up when the API request completes")
    
    return

def pattern_secure_mcp_configuration(data_directory, api_key):
    """Pattern 3: Secure MCP configuration for production environments"""
    console.print(Panel(
        "Pattern 3: Secure MCP Configuration\n"
        "This pattern demonstrates security best practices for MCP in production environments.\n"
        "It shows how to limit access, validate commands, and handle environment variables.",
        title="MCP Pattern 3",
        subtitle="Best for production deployments",
        style="green"
    ))
    
    # Create a secure configuration example
    payload = {
        "task": "Analyze the financial statements and prepare a financial health report. Focus on liquidity, solvency, and profitability ratios.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": api_key,
        "stream": False,
        # Secure filesystem MCP configuration
        "use_filesystem_mcp": True,
        "filesystem_root_path": os.path.join(data_directory, "financial_data"),  # Only allow access to financial_data subdirectory
        # Secure MCP server configuration
        "mcp_servers": [
            {
                # Using fully qualified path for security
                "command": "/usr/local/bin/node",
                "args": [
                    "/path/to/verified/mcp-server.js",
                    "--readonly",
                    "--no-network",
                    "--timeout=30000"
                ],
                "env": {
                    "API_KEY": "secure-api-key",
                    "LOG_LEVEL": "warn",
                    "ALLOWED_OPERATIONS": "read,list,metadata",
                    "NODE_ENV": "production"
                }
            }
        ],
        # Additional security parameters
        "verbose_logging": True
    }
    
    console.print("\n[bold]Security best practices demonstrated:[/bold]")
    console.print("1. Limiting filesystem access to specific subdirectories only")
    console.print("2. Using absolute paths for commands to prevent path manipulation")
    console.print("3. Setting strict server arguments (readonly, no-network, timeout)")
    console.print("4. Explicitly specifying allowed operations")
    console.print("5. Setting production environment variables")
    console.print("6. Enabling verbose logging for security auditing")
    
    # Display request information
    console.print("\n[bold]API Request:[/bold]")
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    
    console.print("\n[bold]Production deployment recommendations:[/bold]")
    console.print("1. Use container isolation for MCP servers when possible")
    console.print("2. Implement strict resource limits (CPU, memory, disk I/O)")
    console.print("3. Apply network security policies to prevent unauthorized access")
    console.print("4. Rotate API keys and credentials regularly")
    console.print("5. Audit MCP server logs for suspicious activity")
    console.print("6. Use dedicated service accounts with minimal permissions")
    
    return

def pattern_streaming_with_mcp(data_directory, api_key):
    """Pattern 4: Streaming results with MCP for long-running analyses"""
    console.print(Panel(
        "Pattern 4: Streaming with MCP\n"
        "This pattern shows how to use streaming responses with MCP for long-running financial analyses.\n"
        "It demonstrates incremental result delivery while maintaining MCP connections.",
        title="MCP Pattern 4",
        subtitle="Best for long-running analyses",
        style="green"
    ))
    
    # Create request payload with streaming enabled
    payload = {
        "task": "Perform a comprehensive analysis of the financial statements. Include detailed profitability analysis, trend analysis over time, and key financial ratios. Provide a deep dive into balance sheet components, income statement drivers, and cash flow patterns. Make specific recommendations based on the findings.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": api_key,
        "stream": True,  # Enable streaming
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory
    }
    
    console.print("\n[bold]Key best practices demonstrated:[/bold]")
    console.print("1. Using streaming for long-running financial analyses")
    console.print("2. Maintaining MCP connections throughout the streaming process")
    console.print("3. Processing incremental results as they arrive")
    console.print("4. Handling MCP resource cleanup reliably with streaming")
    
    # Display request information
    console.print("\n[bold]API Request:[/bold]")
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    
    # Ask user if they want to run this example
    if Prompt.ask("\nRun this streaming example?", choices=["y", "n"], default="y") == "y":
        try:
            # Make streaming request
            console.print("\n[bold]Streaming response:[/bold]")
            # Using requests with stream=True for streaming
            with requests.post(API_URL, json=payload, stream=True) as response:
                if response.status_code == 200:
                    # Process the streaming response
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            console.print(chunk, end="")
                else:
                    console.print(f"\n[bold red]Error {response.status_code}:[/bold red] {response.text}")
            console.print("\n")
        except Exception as e:
            console.print(f"\n[bold red]Error making streaming request:[/bold red] {str(e)}")
    
    console.print("\n[bold]Streaming with MCP considerations:[/bold]")
    console.print("1. MCP servers remain active for the entire duration of the streaming response")
    console.print("2. Resources are only released after the full response is complete")
    console.print("3. Longer timeouts may be needed for streaming with complex analyses")
    console.print("4. Client should handle potential connection drops gracefully")
    
    return

def pattern_mcp_and_knowledge_base(data_directory, api_key):
    """Pattern 5: Combining MCP with knowledge base for enhanced context"""
    console.print(Panel(
        "Pattern 5: MCP with Knowledge Base\n"
        "This pattern demonstrates how to combine MCP with a knowledge base for enhanced context.\n"
        "It shows how to leverage both file access and vector search simultaneously.",
        title="MCP Pattern 5",
        subtitle="Best for comprehensive financial analysis",
        style="green"
    ))
    
    # Create or point to a knowledge source file
    knowledge_text = """
# Financial Analysis Best Practices

## Key Financial Ratios

### Liquidity Ratios
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets - Inventory) / Current Liabilities
- Cash Ratio = Cash and Cash Equivalents / Current Liabilities

### Profitability Ratios
- Gross Profit Margin = Gross Profit / Revenue
- Operating Profit Margin = Operating Income / Revenue
- Net Profit Margin = Net Income / Revenue
- Return on Assets (ROA) = Net Income / Total Assets
- Return on Equity (ROE) = Net Income / Shareholder's Equity

### Solvency Ratios
- Debt to Equity Ratio = Total Debt / Total Equity
- Debt Ratio = Total Debt / Total Assets
- Interest Coverage Ratio = EBIT / Interest Expense

### Efficiency Ratios
- Asset Turnover Ratio = Revenue / Average Total Assets
- Inventory Turnover Ratio = Cost of Goods Sold / Average Inventory
- Receivables Turnover Ratio = Revenue / Average Accounts Receivable

## Industry Benchmarks
For SaaS companies:
- Gross Margin: 70-85%
- Operating Margin: 15-25%
- Net Margin: 10-20%
- Current Ratio: 1.5-2.5
- Quick Ratio: 1.0-2.0
- Debt to Equity: 0.5-1.5
"""
    
    # Create request payload combining MCP with knowledge base
    payload = {
        "task": "Analyze the financial statements in the financial_data directory. Calculate key financial ratios and compare them to industry benchmarks. Use the knowledge base information about financial analysis best practices to provide context and recommendations.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": api_key,
        "stream": False,
        # MCP configuration
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory,
        # Knowledge base configuration
        "knowledge_text": knowledge_text,
        "vector_db_type": "lancedb",
        "embedder_provider": "openai",
        "embedder_model": "text-embedding-3-small",
        # Optional: Add URLs if needed
        # "knowledge_urls": ["https://example.com/financial_best_practices.pdf"]
    }
    
    console.print("\n[bold]Key best practices demonstrated:[/bold]")
    console.print("1. Combining MCP with knowledge base for richer context")
    console.print("2. Using filesystem access for raw data analysis")
    console.print("3. Leveraging vector search for best practices and benchmarks")
    console.print("4. Ensuring both data sources complement each other")
    
    # Display request information
    console.print("\n[bold]API Request:[/bold]")
    request_json = json.dumps(payload, indent=2)
    syntax = Syntax(
        request_json, 
        "json", 
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(syntax)
    
    # For this example, we'll skip the actual execution to avoid setting up a knowledge base
    console.print("\n[bold yellow]Note:[/bold yellow] This example requires a knowledge base which isn't set up in this demo.")
    
    console.print("\n[bold]Implementation best practices:[/bold]")
    console.print("1. MCP provides access to specific files and raw data")
    console.print("2. Knowledge base provides general principles and industry benchmarks")
    console.print("3. Vector search helps find relevant financial analysis guidelines")
    console.print("4. Together they create a powerful analysis capability")
    console.print("5. The AI can reference both private data files and general knowledge")
    
    return

def summarize_patterns():
    """Summarize the MCP usage patterns demonstrated"""
    table = Table(title="MCP Usage Patterns Summary")
    
    table.add_column("Pattern", style="cyan")
    table.add_column("Use Case", style="green")
    table.add_column("Key Benefits", style="white")
    table.add_column("Security Considerations", style="yellow")
    
    table.add_row(
        "Read-only Filesystem",
        "Data analysis, financial reporting",
        "- Simple configuration\n- Minimal attack surface\n- Best for most use cases",
        "- Limit directory access\n- Use absolute paths"
    )
    
    table.add_row(
        "Multiple MCP Servers", 
        "Advanced financial modeling",
        "- Combines multiple specialized tools\n- Enhanced capabilities\n- Flexible architecture",
        "- Validate all commands\n- Use minimal permissions\n- Audit server access"
    )
    
    table.add_row(
        "Secure Configuration",
        "Production deployments",
        "- Hardened production setup\n- Enhanced logging\n- Strict access controls",
        "- Use container isolation\n- Set resource limits\n- Regular credential rotation"
    )
    
    table.add_row(
        "Streaming with MCP",
        "Long-running financial analyses",
        "- Incremental result delivery\n- Better user experience\n- Handles complex analyses",
        "- Longer resource allocation\n- Need connection reliability\n- Resource cleanup monitoring"
    )
    
    table.add_row(
        "MCP with Knowledge Base",
        "Comprehensive financial research",
        "- Combines file access with vector search\n- Richer context\n- Enhanced recommendations",
        "- Multiple security domains\n- Complex configuration\n- Increased attack surface"
    )
    
    console.print(table)
    
    console.print(Panel(
        "[bold]General Best Practices for MCP Usage[/bold]\n\n"
        "1. Always use the most restrictive access pattern necessary for the task\n"
        "2. Prefer read-only filesystem access when possible\n"
        "3. Use absolute paths and validate commands in production environments\n"
        "4. Implement proper error handling for MCP server failures\n"
        "5. Ensure secure credential management for MCP servers\n"
        "6. Monitor and audit MCP server usage regularly\n"
        "7. Implement timeouts to prevent hung processes\n"
        "8. Test MCP configurations thoroughly before production deployment",
        title="MCP Usage Guidelines",
        style="green"
    ))

def main():
    """Run the MCP usage patterns example"""
    console.print(Panel(
        "[bold]This example demonstrates recommended patterns for MCP usage[/bold]\n"
        "Each pattern shows a different approach to using Model Context Protocol (MCP)\n"
        "with the Financial Modeling API, along with best practices and security considerations.",
        title="MCP Usage Patterns Example",
        style="green"
    ))
    
    # Check for required environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        console.print("Please set your OpenAI API key with: export OPENAI_API_KEY=your-api-key")
        return
    
    # Create temporary directory with test data
    data_directory = create_test_directory()
    
    try:
        # Pattern 1: Read-only Filesystem MCP
        pattern_filesystem_read_only(data_directory, api_key)
        
        # Pattern 2: Multiple MCP Servers
        pattern_multiple_mcp_servers(data_directory, api_key)
        
        # Pattern 3: Secure MCP Configuration
        pattern_secure_mcp_configuration(data_directory, api_key)
        
        # Pattern 4: Streaming with MCP
        pattern_streaming_with_mcp(data_directory, api_key)
        
        # Pattern 5: MCP with Knowledge Base
        pattern_mcp_and_knowledge_base(data_directory, api_key)
        
        # Summarize the patterns
        summarize_patterns()
        
    finally:
        # Clean up
        console.print(f"\nCleaning up temporary directory: {data_directory}")
        import shutil
        shutil.rmtree(data_directory)
        console.print("Cleanup complete")

if __name__ == "__main__":
    main() 