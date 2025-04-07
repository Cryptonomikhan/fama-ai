#!/usr/bin/env python3
"""
Example script demonstrating how to resume a team session with persistent storage.

This script shows how to use a previously saved session ID to continue a conversation
with the financial modeling team using storage for session persistence.
"""

import logging
import os
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from src.agents.init_agents import initialize_financial_modeling_team

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize console for pretty output
console = Console()

def print_section(title, content, style="blue"):
    """Print a section with a title and content."""
    console.print(Panel(content, title=title, style=style))

def get_saved_session_id():
    """
    Get a previously saved session ID either from a file or user input.
    
    Returns:
        str: A session ID to resume
    """
    # Path to store session IDs
    session_file = Path("examples/data/saved_sessions.json")
    
    # Create directory if it doesn't exist
    session_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if we have saved sessions
    if session_file.exists():
        try:
            with open(session_file, 'r') as f:
                sessions = json.load(f)
                
            if sessions and len(sessions) > 0:
                console.print("[bold]Found saved sessions:[/bold]")
                for i, (session_id, session_info) in enumerate(sessions.items(), 1):
                    console.print(f"{i}. {session_info.get('name', 'Unnamed session')} - {session_id}")
                
                choice = Prompt.ask(
                    "Enter the number of the session to resume or 'n' for a new ID", 
                    choices=[str(i) for i in range(1, len(sessions) + 1)] + ['n'],
                    default="1"
                )
                
                if choice != 'n':
                    session_id = list(sessions.keys())[int(choice) - 1]
                    return session_id
        except Exception as e:
            logger.error(f"Error reading saved sessions: {str(e)}")
    
    # If we don't have saved sessions or user wants a new one
    session_id = Prompt.ask("Enter a session ID to resume")
    return session_id

def save_session_id(session_id, name=None):
    """
    Save a session ID to a file for future use.
    
    Args:
        session_id: The session ID to save
        name: Optional name for the session
    """
    session_file = Path("examples/data/saved_sessions.json")
    
    # Create directory if it doesn't exist
    session_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing sessions if file exists
    sessions = {}
    if session_file.exists():
        try:
            with open(session_file, 'r') as f:
                sessions = json.load(f)
        except:
            pass
    
    # Add or update this session
    if not name:
        name = Prompt.ask("Enter a name for this session", default="Team Session")
    
    sessions[session_id] = {
        "name": name,
        "last_used": str(Path(__file__).stem),
        "storage_type": "sqlite",  # In a real app, store these with the session too
        "storage_connection": "examples/data/agent_sessions.db",
        "table_name": "agent_sessions"
    }
    
    # Save back to file
    with open(session_file, 'w') as f:
        json.dump(sessions, f, indent=2)
    
    console.print(f"[green]Session ID saved: {session_id}[/green]")

def main():
    """
    Resume a team conversation using a previously saved session ID.
    """
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print_section("API Key Missing", "Please set the OPENAI_API_KEY environment variable", style="red")
        return
    
    # Get a session ID to resume
    session_id = get_saved_session_id()
    user_id = "example_user"  # In a real app, this would be a persistent user ID
    
    print_section("Resuming Team Session", f"""
    Session ID: {session_id}
    User ID: {user_id}
    
    This example will resume a team session using SQLite storage.
    """)
    
    # Storage configuration (should match what was used to create the session)
    storage_type = "sqlite"
    storage_connection = "examples/data/agent_sessions.db"
    table_name = "agent_sessions"
    
    # Initialize the team with the same session ID and storage config
    try:
        console.print("\n[bold]Initializing financial modeling team with stored session...[/bold]")
        team = initialize_financial_modeling_team(
            api_key=api_key,
            provider="openai",
            model_id="gpt-4o",
            temperature=0.1,
            storage_type=storage_type,
            storage_connection=storage_connection,
            session_id=session_id,  # The key to resuming the session
            user_id=user_id,
            table_name=table_name,
            team_name="Resumed Financial Modeling Team",
            team_mode="coordinate"
        )
        
        print_section("Team Resumed", f"""
        Team name: {team.name}
        Number of agents: {len(team.members)}
        Session ID: {session_id}
        
        The team has loaded its previous state from storage.
        You can now continue the conversation where you left off.
        """, style="green")
        
        # Save this session ID for future use
        save_session_id(session_id)
        
    except Exception as e:
        print_section("Team Resumption Failed", f"Error: {str(e)}", style="red")
        return
    
    # Run interactive conversation with the team
    console.print("\n[bold]Resumed conversation with the team:[/bold]")
    console.print("[italic]Type 'exit' to end the conversation[/italic]\n")
    
    while True:
        try:
            query = Prompt.ask("\n[bold]Your question to the team[/bold]")
            
            if query.lower() in ['exit', 'quit', 'bye']:
                break
                
            # Run the query through the team
            response = team.run(query)
            
            # Display the response
            print_section("Team Response", Markdown(response.content), style="blue")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print_section("Error", f"An error occurred: {str(e)}", style="red")
    
    print_section("Session Saved", f"""
    The team's state has been saved to storage.
    
    To resume this conversation later, run this script again and select this session ID:
    {session_id}
    """, style="green")

if __name__ == "__main__":
    main() 