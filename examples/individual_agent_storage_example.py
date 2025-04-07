#!/usr/bin/env python3
"""
Example script demonstrating how to create individual agents with persistent storage.

This script shows how to initialize individual agent types with storage
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

from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.storage.factory import initialize_storage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize console for pretty output
console = Console()

def print_section(title, content, style="blue"):
    """Print a section with a title and content."""
    console.print(Panel(content, title=title, style=style))

def run_agent_with_storage(agent_type="searcher"):
    """
    Run an agent with persistent storage.
    
    Args:
        agent_type: Type of agent to create ("searcher" or "assumption_generator")
    """
    # Get API key from environment or use a default for the example
    api_key = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
    
    # Create a unique session ID (or you can use a fixed one for resuming later)
    session_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    user_id = "example_user"
    
    print_section(f"{agent_type.capitalize()} Agent Configuration", f"""
    Session ID: {session_id}
    User ID: {user_id}
    
    This example will initialize a {agent_type} agent with SQLite storage.
    All agent states and conversations will be persisted to the database.
    """)
    
    # Storage configuration 
    # You can choose from: sqlite, postgres, mongodb, dynamodb, json, yaml
    storage_type = "sqlite"
    storage_connection = "examples/data/individual_agent_sessions.db"
    table_name = "agent_sessions"
    
    # Step 1: Initialize the storage
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
        return
    
    # Step 2: Initialize the requested agent type with storage
    try:
        console.print(f"\n[bold]Initializing {agent_type} agent with storage...[/bold]")
        
        # Create the appropriate agent type
        if agent_type == "searcher":
            agent_instance = SearchingAgent(
                provider="openai",
                model_id="gpt-4o",
                temperature=0.1,
                api_key=api_key,
                session_id=session_id,
                storage=storage  # Pass the storage object directly
            )
            query = "What are the current trends in AI server farm investments?"
        elif agent_type == "assumption_generator":
            # For assumption generator, we need some data to work with
            sample_data = """
            AI server farms require significant capital investment and have been growing rapidly
            to meet increasing demand for AI compute. Power consumption ranges from 20-30 MW for
            medium-sized facilities, with costs between $10-15 million per MW of capacity. 
            Construction timeframes typically range from 12-18 months. Average utilization rates
            range from 70-90% depending on location and customer types.
            """
            agent_instance = AssumptionGeneratorAgent(
                provider="openai",
                model_id="gpt-4o",
                temperature=0.1,
                api_key=api_key,
                data=sample_data,
                session_id=session_id,
                storage=storage  # Pass the storage object directly
            )
            query = "Build assumptions for an AI server farm investment financial model based on the provided data."
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        print_section(f"{agent_type.capitalize()} Agent Initialized", f"""
        Provider: openai
        Model: gpt-4o
        Session ID: {session_id}
        
        Agent is configured to use {storage_type} storage.
        All conversations and state will be saved to the database.
        """, style="green")
        
        # Step 3: Run the agent with a query
        console.print(f"\n[bold]Running query:[/bold] {query}")
        response = agent_instance.agent.run(query)
        
        # Display the response
        print_section("Agent Response", Markdown(response.content), style="blue")
        
        # The agent's state is now saved to storage and can be resumed later
        print_section("Session Saved", f"""
        The agent's state has been saved to the {storage_type} storage.
        To resume this session later, use the same session ID:
        
        Session ID: {session_id}
        """, style="green")
        
        # Step 4: Demonstrate session continuity with a follow-up question
        if agent_type == "searcher":
            follow_up = "What are the main cost considerations for these investments?"
        else:
            follow_up = "What assumptions would vary most in bull vs bear scenarios?"
            
        console.print(f"\n[bold]Running follow-up query:[/bold] {follow_up}")
        follow_up_response = agent_instance.agent.run(follow_up)
        
        # Display the follow-up response
        print_section("Follow-up Response", Markdown(follow_up_response.content), style="blue")
        
        print_section("Session Continuity", """
        Notice how the agent maintains context from the previous interaction.
        This is made possible by the persistent storage.
        
        In a real application, you could close the application, restart it later,
        and resume the exact same session by providing the session ID.
        """, style="cyan")
        
    except Exception as e:
        print_section(f"{agent_type.capitalize()} Agent Failed", f"Error: {str(e)}", style="red")
        import traceback
        traceback.print_exc()

def main():
    """Run the example with both agent types."""
    console.print("[bold]===== Running Searcher Agent Example =====\n[/bold]")
    run_agent_with_storage("searcher")
    
    console.print("\n\n[bold]===== Running Assumption Generator Agent Example =====\n[/bold]")
    run_agent_with_storage("assumption_generator")

if __name__ == "__main__":
    main() 