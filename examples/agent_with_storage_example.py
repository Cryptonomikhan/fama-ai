#!/usr/bin/env python3
"""
Example script demonstrating how to create agents with persistent storage.

This script shows how to initialize the financial modeling team with storage
capabilities, allowing for persistent sessions across API calls.
"""

import logging
import os
import json
import uuid
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agents.init_agents import initialize_financial_modeling_team
from src.storage.factory import initialize_storage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize console for pretty output
console = Console()

def print_section(title, content, style="blue"):
    """Print a section with a title and content."""
    console.print(Panel(content, title=title, style=style))

def main():
    """
    Demonstrate creating agents with storage capabilities.
    """
    # Get API key from environment or use a default for the example
    api_key = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
    
    # Create a unique session ID (or you can use a fixed one for resuming later)
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    user_id = "example_user"
    
    print_section("Storage Configuration", f"""
    Session ID: {session_id}
    User ID: {user_id}
    
    This example will initialize agents with SQLite storage.
    All agent states and conversations will be persisted to the database.
    """)
    
    # Storage configuration 
    # You can choose from: sqlite, postgres, mongodb, dynamodb, json, yaml
    storage_type = "sqlite"
    storage_connection = "examples/data/agent_sessions.db"
    table_name = "agent_sessions"
    
    # Step 1: First, let's initialize the storage directly to see if it works
    try:
        storage = initialize_storage(
            storage_type=storage_type,
            storage_connection=storage_connection,
            session_id=session_id,
            user_id=user_id,
            table_name=table_name
        )
        print_section("Storage Initialized", f"""
        Storage type: {storage_type}
        Connection: {storage_connection}
        Table name: {table_name}
        Storage class: {type(storage).__name__}
        """, style="green")
    except Exception as e:
        print_section("Storage Initialization Failed", f"Error: {str(e)}", style="red")
        storage = None
    
    # Step 2: Initialize financial modeling team with storage
    try:
        console.print("\n[bold]Initializing financial modeling team with storage...[/bold]")
        team = initialize_financial_modeling_team(
            api_key=api_key,
            provider="openai",
            model_id="gpt-4o",
            temperature=0.1,
            storage_type=storage_type,
            storage_connection=storage_connection,
            session_id=session_id,
            user_id=user_id,
            table_name=table_name,
            team_name="Financial Modeling Team with Storage",
            team_mode="coordinate"
        )
        
        # The team is now an Agno Team object with storage capabilities
        print_section("Team Initialized", f"""
        Team name: {team.name}
        Number of agents: {len(team.members)}
        Session ID: {session_id}
        Storage: {"Enabled" if storage else "Disabled"}
        
        Each agent and the team are configured to use {storage_type} storage.
        All conversations and state will be saved to the database.
        """, style="green")
    except Exception as e:
        print_section("Team Initialization Failed", f"Error: {str(e)}", style="red")
        return
    
    # Step 3: Use the team with a simple query
    try:
        query = "What are the current trends in AI server farm investments?"
        
        console.print(f"\n[bold]Running team query:[/bold] {query}")
        
        # Use the team as a whole instead of individual agents
        response = team.run(query)
        
        # Display the response
        print_section("Team Response", Markdown(response.content), style="blue")
        
        # The team's state is now saved to storage and can be resumed later
        # with the same session_id
        print_section("Session Saved", f"""
        The team's state has been saved to the {storage_type} storage.
        To resume this session later, use the same session ID:
        
        Session ID: {session_id}
        """, style="green")
        
        # Demonstrate accessing individual agents through team.agent_dict for backward compatibility
        console.print("\n[bold]Individual agents are still accessible through team.agent_dict:[/bold]")
        for agent_name, agent in team.agent_dict.items():
            console.print(f"- {agent_name}")
            
    except Exception as e:
        print_section("Query Failed", f"Error: {str(e)}", style="red")
        import traceback
        traceback.print_exc()
    
    # Step 4: Run a follow-up query to demonstrate session continuity
    try:
        follow_up_query = "Based on these trends, what would be the key metrics to track for an AI server farm investment?"
        
        console.print(f"\n[bold]Running follow-up query to demonstrate session continuity:[/bold] {follow_up_query}")
        
        # The team maintains context from the previous interaction
        follow_up_response = team.run(follow_up_query)
        
        # Display the response
        print_section("Follow-up Response", Markdown(follow_up_response.content), style="blue")
        
        print_section("Session Continuity", """
        Notice how the team maintains context from the previous interaction.
        This is made possible by the persistent storage.
        
        The team has a shared memory across all its member agents, allowing for
        coherent multi-turn conversations.
        """, style="cyan")
    except Exception as e:
        print_section("Follow-up Query Failed", f"Error: {str(e)}", style="red")
    
    # Step 5: Show how to resume a session in a later run
    print_section("Resuming a Session", f"""
    To resume a session in a later run, initialize the team with the same session_id:
    
    ```python
    team = initialize_financial_modeling_team(
        api_key=api_key,
        provider="openai",
        model_id="gpt-4o",
        storage_type="{storage_type}",
        storage_connection="{storage_connection}",
        session_id="{session_id}",  # Use the saved session ID
        user_id="{user_id}",
        table_name="{table_name}",
        team_name="Financial Modeling Team with Storage",
        team_mode="coordinate"
    )
    
    # Continue the conversation with the team
    response = team.run("Tell me more about AI server farm power requirements")
    ```
    
    The team will load its previous state and continue the conversation with
    full context of all previous interactions.
    """, style="cyan")

if __name__ == "__main__":
    main() 