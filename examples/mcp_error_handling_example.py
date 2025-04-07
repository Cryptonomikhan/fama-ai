#!/usr/bin/env python3
"""
MCP Error Handling Example

This example demonstrates how the Financial Modeling API handles MCP server failures,
focusing on:
1. How the API gracefully handles MCP servers that fail to start
2. How the API continues operation when MCP servers fail during execution
3. What error logging and reporting occurs during MCP failures
4. How to implement proper error handling in client applications

The script tests various error scenarios to validate the robustness of the MCP implementation.
"""

import os
import sys
import json
import tempfile
import requests
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table

# Create a console for pretty output
console = Console()

# API endpoint
API_URL = "http://localhost:8000/task/submit"

def create_sample_financial_data():
    """Create a temporary directory with sample financial data files"""
    temp_dir = tempfile.mkdtemp(prefix="financial_data_")
    console.print(f"Created temporary directory: [bold cyan]{temp_dir}[/bold cyan]\n")
    
    # Create a simple JSON file with financial data
    financial_data = {
        "project": {
            "name": "Financial Analysis Project",
            "description": "Sample project for MCP error testing"
        },
        "data_points": [
            {"id": 1, "value": 100},
            {"id": 2, "value": 200},
            {"id": 3, "value": 300}
        ]
    }
    
    with open(os.path.join(temp_dir, "sample_data.json"), "w") as f:
        json.dump(financial_data, f, indent=2)
    
    console.print("Created sample financial data file:")
    console.print("  • [bold]sample_data.json[/bold]: Simple financial data for testing")
    console.print("\n")
    
    return temp_dir

def test_nonexistent_directory():
    """Test error handling when the filesystem MCP directory doesn't exist"""
    console.print(Panel(
        "Testing error handling for non-existent filesystem directory",
        title="Test Case 1",
        style="yellow"
    ))
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        console.print("Please set your OpenAI API key with: export OPENAI_API_KEY=your-api-key")
        return None
    
    # Create request payload with non-existent directory
    nonexistent_path = "/path/that/definitely/does/not/exist/12345"
    
    payload = {
        "task": "Analyze the financial data in the provided directory and summarize the key metrics.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        "use_filesystem_mcp": True,
        "filesystem_root_path": nonexistent_path,
        "verbose_logging": True
    }
    
    console.print(f"Testing with non-existent directory: [bold red]{nonexistent_path}[/bold red]")
    
    try:
        response = requests.post(API_URL, json=payload)
        
        console.print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            console.print("[bold green]✓[/bold green] API successfully continued operation despite invalid directory")
            result = {
                "status_code": response.status_code,
                "message": "API continued operation despite invalid directory",
                "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
        else:
            console.print(f"[bold red]Error response:[/bold red] {response.text}")
            result = {
                "status_code": response.status_code,
                "message": "API returned an error",
                "response": response.text
            }
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
        return {
            "status_code": None,
            "message": f"Request error: {str(e)}",
            "response": None
        }

def test_invalid_mcp_command():
    """Test error handling when an invalid MCP command is provided"""
    console.print(Panel(
        "Testing error handling for invalid MCP server command",
        title="Test Case 2",
        style="yellow"
    ))
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        return None
    
    # Create request payload with invalid MCP server command
    payload = {
        "task": "Analyze the financial trends and create a summary report.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        "mcp_servers": [
            {
                "command": "command_that_does_not_exist_12345",
                "args": ["--nonexistent-flag"],
                "env": {"TEST": "value"}
            }
        ],
        "verbose_logging": True
    }
    
    console.print("Testing with invalid MCP server command: [bold red]command_that_does_not_exist_12345[/bold red]")
    
    try:
        response = requests.post(API_URL, json=payload)
        
        console.print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            console.print("[bold green]✓[/bold green] API successfully continued operation despite invalid MCP command")
            result = {
                "status_code": response.status_code,
                "message": "API continued operation despite invalid MCP command",
                "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
        else:
            console.print(f"[bold red]Error response:[/bold red] {response.text}")
            result = {
                "status_code": response.status_code,
                "message": "API returned an error",
                "response": response.text
            }
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
        return {
            "status_code": None,
            "message": f"Request error: {str(e)}",
            "response": None
        }

def test_multiple_failing_servers(data_directory):
    """Test error handling when multiple MCP servers fail"""
    console.print(Panel(
        "Testing error handling for multiple failing MCP servers",
        title="Test Case 3",
        style="yellow"
    ))
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        return None
    
    # Create request payload with:
    # 1. A filesystem MCP with valid path
    # 2. Two invalid MCP server commands
    payload = {
        "task": "Analyze the financial data and provide a summary of the key metrics.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        "use_filesystem_mcp": True,
        "filesystem_root_path": data_directory,
        "mcp_servers": [
            {
                "command": "invalid_command_1",
                "args": ["--arg1", "--arg2"],
                "env": {"KEY1": "value1"}
            },
            {
                "command": "invalid_command_2",
                "args": ["--flag1"],
                "env": {"KEY2": "value2"}
            }
        ],
        "verbose_logging": True
    }
    
    console.print("Testing with:")
    console.print(f"  • Valid filesystem path: [bold green]{data_directory}[/bold green]")
    console.print("  • Invalid MCP command 1: [bold red]invalid_command_1[/bold red]")
    console.print("  • Invalid MCP command 2: [bold red]invalid_command_2[/bold red]")
    
    try:
        response = requests.post(API_URL, json=payload)
        
        console.print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            console.print("[bold green]✓[/bold green] API successfully continued with valid filesystem MCP despite invalid commands")
            result = {
                "status_code": response.status_code,
                "message": "API continued with valid filesystem MCP despite invalid commands",
                "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
        else:
            console.print(f"[bold red]Error response:[/bold red] {response.text}")
            result = {
                "status_code": response.status_code,
                "message": "API returned an error",
                "response": response.text
            }
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
        return {
            "status_code": None,
            "message": f"Request error: {str(e)}",
            "response": None
        }

def test_invalid_environment_variables():
    """Test error handling when invalid environment variables are provided to MCP server"""
    console.print(Panel(
        "Testing error handling for invalid environment variables to MCP server",
        title="Test Case 4",
        style="yellow"
    ))
    
    # You need to provide your own API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        return None
    
    # Create request payload with problematic environment variables
    payload = {
        "task": "Analyze the financial trends and create a summary report.",
        "model_id": "gpt-4o",
        "model_provider": "openai",
        "provider_api_key": openai_api_key,
        "stream": False,
        "mcp_servers": [
            {
                "command": "npx",
                "args": ["-y", "@financialtools/mcp-server"],
                "env": {
                    # Add invalid environment variable (non-string value)
                    "NUMERIC_VALUE": 12345,
                    # Add extremely long environment variable that might cause issues
                    "EXTREMELY_LONG_KEY": "a" * 10000
                }
            }
        ],
        "verbose_logging": True
    }
    
    console.print("Testing with problematic environment variables:")
    console.print("  • Non-string numeric value: [bold red]NUMERIC_VALUE: 12345[/bold red]")
    console.print("  • Extremely long value: [bold red]EXTREMELY_LONG_KEY: 'a' * 10000[/bold red]")
    
    try:
        response = requests.post(API_URL, json=payload)
        
        console.print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            console.print("[bold green]✓[/bold green] API successfully continued operation despite environment variable issues")
            result = {
                "status_code": response.status_code,
                "message": "API continued operation despite environment variable issues",
                "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
            }
        else:
            console.print(f"[bold red]Error response:[/bold red] {response.text}")
            result = {
                "status_code": response.status_code,
                "message": "API returned an error",
                "response": response.text
            }
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error making request:[/bold red] {str(e)}")
        return {
            "status_code": None,
            "message": f"Request error: {str(e)}",
            "response": None
        }

def summarize_results(results):
    """Summarize the test results in a table"""
    table = Table(title="MCP Error Handling Test Results")
    
    table.add_column("Test Case", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Message", style="white")
    
    for test_name, result in results.items():
        status = "✓ SUCCESS" if result["status_code"] == 200 else "✗ FAILED"
        status_style = "green" if result["status_code"] == 200 else "red"
        
        table.add_row(
            test_name,
            f"[{status_style}]{status}[/{status_style}]",
            result["message"]
        )
    
    console.print(table)
    
    # Provide overall assessment
    success_count = sum(1 for result in results.values() if result["status_code"] == 200)
    total_count = len(results)
    
    overall_panel = Panel(
        f"[bold]Tests Passed: {success_count}/{total_count}[/bold]\n\n"
        f"{'[bold green]All tests passed successfully!' if success_count == total_count else '[bold yellow]Some tests failed!'}\n\n"
        "The Financial Modeling API's MCP error handling was tested against various failure scenarios.\n"
        "When MCP servers fail to initialize, the API should continue operating without them rather than failing completely.",
        title="Test Summary",
        subtitle=f"Success Rate: {success_count}/{total_count}"
    )
    
    console.print(overall_panel)

def main():
    """Run the MCP error handling tests"""
    console.print(Panel(
        "[bold]This example tests error handling for MCP server failures[/bold]\n"
        "The script will run a series of tests to verify that the Financial Modeling API handles\n"
        "MCP server failures gracefully and continues to operate even when MCP servers fail.",
        title="MCP Error Handling Tests",
        style="green"
    ))
    
    # Check for required environment variable
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set")
        console.print("Please set your OpenAI API key with: export OPENAI_API_KEY=your-api-key")
        return
    
    # Create temporary directory with sample data for tests
    data_directory = create_sample_financial_data()
    
    try:
        # Run the error handling tests
        results = {}
        
        # Test 1: Non-existent directory
        console.print("\n[bold]Running Test 1: Non-existent directory[/bold]")
        results["Non-existent directory"] = test_nonexistent_directory()
        
        # Test 2: Invalid MCP command
        console.print("\n[bold]Running Test 2: Invalid MCP command[/bold]")
        results["Invalid MCP command"] = test_invalid_mcp_command()
        
        # Test 3: Multiple failing servers
        console.print("\n[bold]Running Test 3: Multiple failing servers[/bold]")
        results["Multiple failing servers"] = test_multiple_failing_servers(data_directory)
        
        # Test 4: Invalid environment variables
        console.print("\n[bold]Running Test 4: Invalid environment variables[/bold]")
        results["Invalid environment variables"] = test_invalid_environment_variables()
        
        # Summarize results
        console.print("\n[bold]Test Results Summary:[/bold]")
        summarize_results(results)
        
    finally:
        # Clean up
        console.print(f"\nCleaning up temporary directory: {data_directory}")
        import shutil
        shutil.rmtree(data_directory)
        console.print("Cleanup complete")

if __name__ == "__main__":
    main() 