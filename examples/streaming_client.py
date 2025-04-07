"""
Streaming Client Example

This script demonstrates how to connect to the streaming API endpoint
and handle the server-sent events for real-time updates.
"""

import requests
import json
import os
import sys
import time
from sseclient import SSEClient
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

# Load environment variables
load_dotenv()

# Initialize rich console for pretty output
console = Console()

def create_progress_display():
    """Create a rich progress display with custom columns"""
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )

def stream_financial_model(description, provider="formation", model_id=None, stream=True):
    """
    Stream a financial model from the API
    
    Args:
        description: Description of the investment opportunity
        provider: Model provider (formation, openai, anthropic, openrouter)
        model_id: Model ID to use (provider-specific)
        stream: Whether to stream the response
    """
    # API endpoint
    url = "http://localhost:8000/api/model"
    
    # Get API key from environment
    api_key = os.getenv("API_KEY", "test-api-key")
    
    # Get provider-specific API key
    provider_api_keys = {
        "formation": os.getenv("FORMATION_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY")
    }
    provider_api_key = provider_api_keys.get(provider)
    
    # Prepare the request payload
    payload = {
        "description": description,
        "provider": provider,
        "api_key": provider_api_key,
        "stream": stream,
        "temperature": 0.1
    }
    
    # Add model ID if provided
    if model_id:
        payload["model_id"] = model_id
    
    # Set headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    console.print(f"[bold green]Streaming financial model for:[/bold green]")
    console.print(f"[italic]{description}[/italic]")
    console.print(f"Using provider: [bold]{provider}[/bold]")
    
    if stream:
        # For streaming response
        with create_progress_display() as progress:
            # Initialize progress bars for each agent
            agent_tasks = {}
            overall_task = progress.add_task("[bold red]Overall Progress", total=100)
            
            # Make the request in streaming mode
            response = requests.post(url, json=payload, headers=headers, stream=True)
            
            if response.status_code != 200:
                console.print(f"[bold red]Error:[/bold red] {response.status_code} - {response.text}")
                return
            
            # Process the server-sent events
            client = SSEClient(response)
            final_result = None
            
            for event in client.events():
                try:
                    data = json.loads(event.data)
                    event_type = data.get("event")
                    message = data.get("message", "")
                    agent_name = data.get("agent")
                    progress_value = data.get("progress", 0)
                    error = data.get("error")
                    event_data = data.get("data")
                    
                    if event_type == "start":
                        console.print(f"[bold cyan]Started:[/bold cyan] {message}")
                    
                    elif event_type == "progress":
                        # Update overall progress
                        progress.update(overall_task, completed=progress_value)
                        
                        # Update or create agent-specific progress bar
                        if agent_name:
                            if agent_name not in agent_tasks:
                                agent_tasks[agent_name] = progress.add_task(
                                    f"[yellow]{agent_name.replace('_', ' ').title()}",
                                    total=100
                                )
                            progress.update(agent_tasks[agent_name], completed=progress_value * 2)
                        
                        console.print(f"[dim]{message}[/dim]")
                        
                        # If we have intermediate data, show a hint
                        if event_data:
                            for key, value in event_data.items():
                                if isinstance(value, str) and len(value) > 100:
                                    console.print(f"[dim]Received {key} ({len(value)} characters)[/dim]")
                                elif isinstance(value, dict):
                                    console.print(f"[dim]Received {key} ({len(value)} items)[/dim]")
                    
                    elif event_type == "complete":
                        # Complete all progress bars
                        progress.update(overall_task, completed=100)
                        for task_id in agent_tasks.values():
                            progress.update(task_id, completed=100)
                        
                        console.print(f"[bold green]Completed:[/bold green] {message}")
                        final_result = event_data
                    
                    elif event_type == "error":
                        console.print(f"[bold red]Error:[/bold red] {error}")
                        return
                    
                except json.JSONDecodeError:
                    console.print("[bold red]Error parsing event data[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]Error processing event:[/bold red] {str(e)}")
            
            # Process the final result
            if final_result:
                console.print("\n[bold green]Financial Model Summary:[/bold green]")
                
                # Show metrics
                if final_result.get("metrics"):
                    console.print("\n[bold cyan]Key Metrics:[/bold cyan]")
                    metrics_str = str(final_result["metrics"])
                    console.print(metrics_str[:500] + "..." if len(metrics_str) > 500 else metrics_str)
                
                # Show financial model highlights
                if final_result.get("financial_model"):
                    console.print("\n[bold cyan]Financial Model Highlights:[/bold cyan]")
                    model_str = str(final_result["financial_model"])
                    console.print(model_str[:500] + "..." if len(model_str) > 500 else model_str)
                
                console.print("\n[bold green]Complete results saved to 'model_results.json'[/bold green]")
                
                # Save complete results to file
                with open("model_results.json", "w") as f:
                    json.dump(final_result, f, indent=2)
    
    else:
        # For non-streaming response
        console.print("Making non-streaming request (this may take a while)...")
        start_time = time.time()
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            console.print(f"[bold red]Error:[/bold red] {response.status_code} - {response.text}")
            return
        
        elapsed_time = time.time() - start_time
        console.print(f"Request completed in {elapsed_time:.2f} seconds")
        
        result = response.json()
        
        console.print("\n[bold green]Financial Model Summary:[/bold green]")
        
        # Show metrics
        if result.get("metrics"):
            console.print("\n[bold cyan]Key Metrics:[/bold cyan]")
            metrics_str = str(result["metrics"])
            console.print(metrics_str[:500] + "..." if len(metrics_str) > 500 else metrics_str)
        
        # Show financial model highlights
        if result.get("financial_model"):
            console.print("\n[bold cyan]Financial Model Highlights:[/bold cyan]")
            model_str = str(result["financial_model"])
            console.print(model_str[:500] + "..." if len(model_str) > 500 else model_str)
        
        console.print("\n[bold green]Complete results saved to 'model_results.json'[/bold green]")
        
        # Save complete results to file
        with open("model_results.json", "w") as f:
            json.dump(result, f, indent=2)

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Stream a financial model from the API")
    parser.add_argument("description", nargs="?", help="Description of the investment opportunity")
    parser.add_argument("--provider", default="formation", choices=["formation", "openai", "anthropic", "openrouter"],
                        help="Model provider to use")
    parser.add_argument("--model", default=None, help="Model ID to use")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    args = parser.parse_args()
    
    # Default investment description if not provided
    description = args.description or """
    A tokenized real estate fund that invests in multifamily properties
    in emerging tech hubs across the U.S. The fund targets properties that
    can be renovated to increase NOI by 15-20%. Initial capital raise is
    $10M with a target IRR of 18-22% over a 5-year hold period.
    """
    
    # Stream the financial model
    stream_financial_model(
        description=description,
        provider=args.provider,
        model_id=args.model,
        stream=not args.no_stream
    )

if __name__ == "__main__":
    main() 