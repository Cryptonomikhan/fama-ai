#!/usr/bin/env python3
"""
Example demonstrating PostgreSQL storage usage with Agno agents.

This example shows how to initialize and use PostgreSQL storage for persistent 
agent sessions based on the Agno framework.
"""
import os
import json
import typer
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Import our storage factory
from src.storage.factory import initialize_storage

# Database URL for PostgreSQL
# The syntax follows the format: postgresql+psycopg://username:password@host:port/database
# As mentioned in the Agno docs, you can run PostgreSQL using Docker:
# docker run -d \
#   -e POSTGRES_DB=ai \
#   -e POSTGRES_USER=ai \
#   -e POSTGRES_PASSWORD=ai \
#   -e PGDATA=/var/lib/postgresql/data/pgdata \
#   -v pgvolume:/var/lib/postgresql/data \
#   -p 5532:5432 \
#   --name pgvector \
#   agno/pgvector:16
DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Rich console for pretty output
console = Console()

def print_chat_history(agent):
    """Print the agent's chat history"""
    console.print(
        Panel(
            JSON(json.dumps([m.model_dump(include={"role", "content"}) for m in agent.memory.messages]), indent=4),
            title=f"Chat History for session_id: {agent.session_id}",
            expand=True,
        )
    )

def postgres_agent(new: bool = False, user: str = "user"):
    """
    Run an agent with PostgreSQL storage.
    
    Args:
        new: Whether to start a new session or continue an existing one
        user: User ID for the session
    """
    session_id: Optional[str] = None
    
    # Initialize storage using our factory
    storage = initialize_storage(
        storage_type="postgres",
        storage_connection=DB_URL,
        table_name="agent_sessions"
    )
    
    # Get existing session ID if not starting a new session
    if not new:
        try:
            # The get_all_session_ids method is available in PostgresAgentStorage
            existing_sessions: List[str] = storage.get_all_session_ids(user)
            if len(existing_sessions) > 0:
                session_id = existing_sessions[0]
        except Exception as e:
            console.print(f"[yellow]Warning: Could not retrieve existing sessions: {str(e)}[/yellow]")
    
    # Create an agent with the storage
    agent = Agent(
        session_id=session_id,
        user_id=user,
        storage=storage,
        model=OpenAIChat(id="gpt-4o"),
        tools=[DuckDuckGoTools()],
        # Show tool calls in the response
        show_tool_calls=True,
        # Enable the agent to read the chat history
        read_chat_history=True,
        # We can also automatically add the chat history to the messages
        add_history_to_messages=True,
        # Number of history responses to include
        num_history_responses=3,
    )
    
    if session_id is None:
        session_id = agent.session_id
        console.print(f"[green]Started Session: {session_id}[/green]\n")
    else:
        console.print(f"[blue]Continuing Session: {session_id}[/blue]\n")
    
    # Runs the agent as a CLI app
    agent.cli_app(markdown=True)

def main():
    """Entry point for the example"""
    typer.run(postgres_agent)

if __name__ == "__main__":
    main() 