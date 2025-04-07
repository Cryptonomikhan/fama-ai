#!/usr/bin/env python3
"""
Example of using YAML file-based storage for persistent agent sessions with Agno.

This example demonstrates how to use YAML storage to maintain conversation
history across multiple interactions with an agent.

Run this example with:
   python examples/yaml_storage_example.py
"""

import os
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

from src.storage.factory import initialize_storage

console = Console()

# Define storage directory - use a dedicated folder in the user's home directory
STORAGE_DIR = os.path.expanduser("~/agno_yaml_storage")

def print_chat_history(agent):
    """Print the agent's chat history in a formatted manner."""
    console.print("\n[bold green]Chat History:[/bold green]")
    
    for i, message in enumerate(agent.chat_history):
        if message["role"] == "user":
            console.print(Panel(
                message["content"],
                title=f"User (Message {i+1})",
                border_style="blue"
            ))
        elif message["role"] == "assistant":
            console.print(Panel(
                message["content"],
                title=f"Assistant (Message {i+1})",
                border_style="green"
            ))

def main():
    # Ensure the storage directory exists
    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    
    # Initialize YAML storage
    try:
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=STORAGE_DIR,
            create_dir_if_not_exists=True
        )
        console.print(f"[bold green]✓[/bold green] YAML storage initialized in: {STORAGE_DIR}")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to initialize YAML storage: {str(e)}")
        return

    # Check for session ID in environment variable
    session_id = os.environ.get("SESSION_ID")
    if session_id:
        console.print(f"[bold blue]ℹ[/bold blue] Resuming session: {session_id}")
    else:
        session_id = None
        console.print("[bold blue]ℹ[/bold blue] Creating new session")

    # Create an agent with YAML storage
    agent = Agent(
        llm=OpenAIChat(model="gpt-3.5-turbo"),
        tools=[DuckDuckGoTools()],
        storage=storage,
        session_id=session_id,
        user_id="example_user",
        description="A helpful assistant that remembers previous conversations.",
        include_history_in_prompts=True
    )

    # Display the session ID for future reference
    console.print(f"[bold yellow]Session ID:[/bold yellow] {agent.session_id}")
    console.print("You can use this session ID to continue this conversation later by setting:")
    console.print(f"[bold]export SESSION_ID={agent.session_id}[/bold]")
    
    # Display the storage file location
    session_file = os.path.join(STORAGE_DIR, f"{agent.session_id}.yaml")
    console.print(f"\n[bold cyan]Storage File:[/bold cyan] {session_file}")

    # Ask the agent some questions
    questions = [
        "What's the capital of France?",
        "What's the population of that city?"
    ]

    for question in questions:
        console.print(Panel(
            f"Asking: {question}",
            title="New Question",
            border_style="yellow"
        ))
        
        response = agent.chat(question)
        
        console.print(Panel(
            Markdown(response),
            title="Agent Response",
            border_style="green"
        ))
    
    # Print the chat history
    print_chat_history(agent)
    
    # Show what the YAML file contains (if it exists)
    session_file = os.path.join(STORAGE_DIR, f"{agent.session_id}.yaml")
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = yaml.safe_load(f)
            
            console.print("\n[bold magenta]Storage File Contents:[/bold magenta]")
            yaml_content = yaml.dump(session_data, sort_keys=False, default_flow_style=False)
            console.print(Syntax(
                yaml_content,
                "yaml",
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            ))
        except Exception as e:
            console.print(f"[bold red]Could not read session file: {str(e)}[/bold red]")

if __name__ == "__main__":
    main() 