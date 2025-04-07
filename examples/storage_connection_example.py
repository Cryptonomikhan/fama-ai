#!/usr/bin/env python3
"""
Example of storage connection error handling with Agno.

This example demonstrates how to use the connection error handling and retry
mechanisms when initializing storage for agent persistence.

Run this example with:
   python examples/storage_connection_example.py
"""

import os
import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.markdown import Markdown

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.storage.factory import initialize_storage, StorageConnectionError, StorageError
from src.storage.connection import ensure_storage_healthy, monitor_connection_health

console = Console()

def simulate_connection_error(seconds=5):
    """Simulate a connection error by sleeping."""
    console.print("[bold yellow]Simulating a connection error...[/bold yellow]")
    with Progress() as progress:
        task = progress.add_task("[red]Connection failing...", total=seconds)
        for _ in range(seconds):
            time.sleep(1)
            progress.update(task, advance=1)
    console.print("[bold red]⚠️ Connection failed![/bold red]")

def display_connection_config(storage_type, connection_str, retries, retry_delay, monitoring):
    """Display connection configuration."""
    table = Table(title="Storage Connection Configuration")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Storage Type", storage_type)
    table.add_row("Connection String", connection_str)
    table.add_row("Max Retries", str(retries))
    table.add_row("Retry Delay", f"{retry_delay}s")
    table.add_row("Health Monitoring", "Enabled" if monitoring else "Disabled")
    
    console.print(table)

def create_agent_with_storage(storage_type, connection_str, **kwargs):
    """
    Create an agent with storage, demonstrating connection error handling.
    
    Args:
        storage_type: Type of storage to use
        connection_str: Connection string for the storage
        **kwargs: Additional parameters for storage initialization
    """
    retries = kwargs.pop('max_retries', 3)
    retry_delay = kwargs.pop('retry_delay', 2)
    monitoring = kwargs.pop('monitor_connection', False)
    
    # Display configuration
    display_connection_config(storage_type, connection_str, retries, retry_delay, monitoring)
    
    # First attempt - will fail if we simulate a connection error
    console.print("\n[bold blue]Step 1: First attempt to initialize storage[/bold blue]")
    try:
        storage = initialize_storage(
            storage_type=storage_type,
            storage_connection=connection_str,
            max_retries=1,  # Only try once for this demo
            retry_delay=0.5,
            validate_connection=True,
            monitor_connection=False,
            **kwargs
        )
        console.print("[bold green]✓ Storage initialized successfully on first attempt[/bold green]")
        
    except StorageConnectionError as e:
        console.print(Panel(
            f"[bold red]Connection Error:[/bold red] {str(e)}",
            title="Storage Connection Failed",
            border_style="red"
        ))
        console.print("\n[bold blue]Step 2: Retry with automatic retries[/bold blue]")
        
        # Second attempt - with automatic retries
        try:
            console.print(f"Attempting to connect with {retries} retries and {retry_delay}s delay between retries...")
            
            storage = initialize_storage(
                storage_type=storage_type,
                storage_connection=connection_str,
                max_retries=retries,
                retry_delay=retry_delay,
                validate_connection=True,
                monitor_connection=monitoring,
                **kwargs
            )
            
            console.print("[bold green]✓ Storage initialized successfully after retries[/bold green]")
            
        except StorageConnectionError as e:
            console.print(Panel(
                f"[bold red]Connection Error after retries:[/bold red] {str(e)}",
                title="All Connection Attempts Failed",
                border_style="red"
            ))
            console.print("\n[bold yellow]Exiting due to persistent connection errors[/bold yellow]")
            return None
    
    # Create agent with the initialized storage
    console.print("\n[bold blue]Step 3: Create agent with storage[/bold blue]")
    agent = Agent(
        llm=OpenAIChat(model="gpt-3.5-turbo"),
        storage=storage,
        user_id="example_user",
        description="A helpful assistant that demonstrates storage connection handling."
    )
    
    console.print(f"[bold green]✓ Agent created with session ID: {agent.session_id}[/bold green]")
    
    # Verify storage health
    console.print("\n[bold blue]Step 4: Verify storage health[/bold blue]")
    try:
        ensure_storage_healthy(storage, perform_write_test=True)
        console.print("[bold green]✓ Storage is healthy and working correctly[/bold green]")
    except StorageConnectionError as e:
        console.print(f"[bold red]✗ Storage health check failed: {str(e)}[/bold red]")
    
    # Enable monitoring if requested
    if monitoring and hasattr(storage, 'list_sessions'):
        console.print("\n[bold blue]Step 5: Enable connection health monitoring[/bold blue]")
        monitor_connection_health(
            storage=storage,
            interval=10,  # Check every 10 seconds
            max_failures=3
        )
        console.print("[bold green]✓ Connection health monitoring enabled[/bold green]")
    
    return agent

def main():
    """Main function to demonstrate storage connection error handling."""
    parser = argparse.ArgumentParser(description="Storage connection example")
    parser.add_argument('--storage-type', default='sqlite', 
                        help='Storage type (sqlite, json, etc.)')
    parser.add_argument('--connection', default=':memory:', 
                        help='Connection string or path')
    parser.add_argument('--simulate-error', action='store_true',
                        help='Simulate a connection error')
    parser.add_argument('--retries', type=int, default=3,
                        help='Number of retries')
    parser.add_argument('--retry-delay', type=float, default=2.0,
                        help='Delay between retries in seconds')
    parser.add_argument('--monitor', action='store_true',
                        help='Enable connection health monitoring')
    
    args = parser.parse_args()
    
    console.print(Panel(
        "This example demonstrates how to handle storage connection errors and retries",
        title="Storage Connection Error Handling",
        border_style="blue"
    ))
    
    # Simulate a connection error if requested
    if args.simulate_error:
        simulate_connection_error(3)
    
    # Create an agent with storage, demonstrating connection error handling
    agent = create_agent_with_storage(
        storage_type=args.storage_type,
        connection_str=args.connection,
        max_retries=args.retries,
        retry_delay=args.retry_delay,
        monitor_connection=args.monitor
    )
    
    if agent:
        console.print("\n[bold blue]Agent created successfully![/bold blue]")
        console.print("You can now interact with the agent and it will persist its state in storage.")
        console.print(f"Session ID: {agent.session_id}")
    else:
        console.print("\n[bold red]Failed to create agent due to storage connection issues.[/bold red]")

if __name__ == "__main__":
    main() 