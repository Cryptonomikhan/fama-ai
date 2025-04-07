#!/usr/bin/env python3
"""
Example of using DynamoDB storage for persistent agent sessions with Agno.

Before running this example:
1. Set up a local DynamoDB instance:
   docker run -p 8000:8000 amazon/dynamodb-local

2. Run this example with:
   python examples/dynamodb_storage_example.py
"""

import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

from src.storage.factory import initialize_storage

console = Console()

# DynamoDB configuration
dynamodb_config = {
    "region_name": "us-west-2",
    "endpoint_url": "http://localhost:8000",  # For local development
    "create_table_if_not_exists": True
}

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
    # Initialize DynamoDB storage
    try:
        storage = initialize_storage(
            storage_type="dynamodb",
            storage_connection=dynamodb_config,
            table_name="agent_sessions"
        )
        console.print("[bold green]✓[/bold green] DynamoDB storage initialized successfully")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to initialize DynamoDB storage: {str(e)}")
        return

    # Check for session ID in environment variable
    session_id = os.environ.get("SESSION_ID")
    if session_id:
        console.print(f"[bold blue]ℹ[/bold blue] Resuming session: {session_id}")
    else:
        session_id = None
        console.print("[bold blue]ℹ[/bold blue] Creating new session")

    # Create an agent with DynamoDB storage
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

if __name__ == "__main__":
    main() 