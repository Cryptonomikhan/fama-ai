#!/usr/bin/env python3
"""
Example of using session management with Agno's storage system.

This example demonstrates how to create, resume, and manage sessions
using the SessionManager with SQLite storage.

Run this example with:
   python examples/session_manager_example.py
"""

import os
import time
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.storage.factory import initialize_storage, StorageError
from src.storage.session import create_session_manager

console = Console()

def display_session_info(manager, session_id):
    """Display detailed information about a session."""
    try:
        metadata = manager.get_session_metadata(session_id)
        
        # Create a table for session details
        table = Table(title=f"Session {session_id} Details")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Add basic properties
        for key, value in metadata.items():
            table.add_row(key, str(value))
        
        console.print(table)
    except StorageError as e:
        console.print(f"[bold red]Error retrieving session info: {str(e)}[/bold red]")

def create_new_session(manager, user_id, metadata=None):
    """Create a new session with optional metadata."""
    try:
        # Create the session
        session_id = manager.create_session(user_id, metadata)
        
        console.print(Panel(
            f"Session [bold]{session_id}[/bold] created for user [bold]{user_id}[/bold]",
            title="New Session Created",
            border_style="green"
        ))
        
        return session_id
    except StorageError as e:
        console.print(f"[bold red]Error creating session: {str(e)}[/bold red]")
        return None

def list_all_sessions(manager, user_id=None):
    """List all available sessions, optionally filtered by user ID."""
    try:
        # Get sessions
        sessions = manager.list_sessions(user_id)
        
        if not sessions:
            if user_id:
                console.print(f"[yellow]No sessions found for user {user_id}[/yellow]")
            else:
                console.print("[yellow]No sessions found[/yellow]")
            return
        
        # Create a table for sessions
        table = Table(title=f"Available Sessions{' for user ' + user_id if user_id else ''}")
        table.add_column("Session ID", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("User ID", style="yellow")
        table.add_column("Messages", style="blue")
        
        # Add each session to the table
        for session_id in sessions:
            try:
                metadata = manager.get_session_metadata(session_id)
                created_at = metadata.get("created_at", "Unknown")
                session_user_id = metadata.get("user_id", "Unknown")
                message_count = metadata.get("message_count", 0)
                
                table.add_row(session_id, created_at, session_user_id, str(message_count))
            except StorageError:
                # If we can't get metadata, just add the session ID
                table.add_row(session_id, "Error", "Error", "Error")
        
        console.print(table)
    except StorageError as e:
        console.print(f"[bold red]Error listing sessions: {str(e)}[/bold red]")

def interact_with_agent(storage, session_id=None, user_id=None):
    """Create an agent with the specified storage and session ID, then interact with it."""
    # Create the agent
    try:
        agent = Agent(
            llm=OpenAIChat(model="gpt-3.5-turbo"),
            storage=storage,
            session_id=session_id,
            user_id=user_id,
            description="A helpful assistant that demonstrates session management."
        )
        
        if session_id:
            console.print(f"[bold green]Resumed session: {agent.session_id}[/bold green]")
        else:
            console.print(f"[bold green]Created new session: {agent.session_id}[/bold green]")
            session_id = agent.session_id
        
        # Simple interaction loop
        console.print("[bold blue]Chat with the agent (type 'exit' to quit):[/bold blue]")
        
        while True:
            user_input = console.input("[bold cyan]You: [/bold cyan]")
            
            if user_input.lower() in ["exit", "quit", "q"]:
                break
            
            # Send message to agent
            response = agent.chat(user_input)
            
            # Display response
            console.print(Panel(
                Markdown(response),
                title="Agent",
                border_style="green"
            ))
        
        return session_id
    except Exception as e:
        console.print(f"[bold red]Error interacting with agent: {str(e)}[/bold red]")
        return None

def main():
    """Main function to demonstrate session management."""
    parser = argparse.ArgumentParser(description="Session management example")
    parser.add_argument('--create', action='store_true', help='Create a new session')
    parser.add_argument('--list', action='store_true', help='List sessions')
    parser.add_argument('--resume', type=str, help='Resume a specific session')
    parser.add_argument('--user', type=str, default="example_user", help='User ID')
    parser.add_argument('--db', type=str, default="sessions.db", help='SQLite DB path')
    
    args = parser.parse_args()
    
    console.print(Panel(
        "This example demonstrates how to use the SessionManager for persistent agent sessions",
        title="Session Management Example",
        border_style="blue"
    ))
    
    # Initialize storage
    try:
        storage = initialize_storage(
            storage_type="sqlite",
            storage_connection=args.db,
            table_name="agent_sessions"
        )
        console.print(f"[bold green]✓[/bold green] SQLite storage initialized with database: {args.db}")
        
        # Create session manager
        manager = create_session_manager(storage)
        console.print(f"[bold green]✓[/bold green] Session manager created")
        
        # Choose action based on arguments
        if args.list:
            # List sessions
            console.print("\n[bold blue]Available Sessions:[/bold blue]")
            list_all_sessions(manager, args.user if args.user != "example_user" else None)
            
        elif args.resume:
            # Resume existing session
            console.print(f"\n[bold blue]Resuming Session: {args.resume}[/bold blue]")
            display_session_info(manager, args.resume)
            
            # Interact with agent using resumed session
            interact_with_agent(storage, args.resume, args.user)
            
        elif args.create:
            # Create new session
            console.print(f"\n[bold blue]Creating New Session for User: {args.user}[/bold blue]")
            
            # Create with metadata
            metadata = {
                "app_version": "1.0",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "client_info": "Session Manager Example",
                "user_agent": "Python Session Manager Example"
            }
            
            # Create the session
            session_id = create_new_session(manager, args.user, metadata)
            
            if session_id:
                # Interact with agent using new session
                interact_with_agent(storage, session_id, args.user)
                
                # Show updated session info
                console.print("\n[bold blue]Updated Session Info:[/bold blue]")
                display_session_info(manager, session_id)
            
        else:
            # Default: create a new session and interact
            console.print(f"\n[bold blue]Starting with Default Session for User: {args.user}[/bold blue]")
            
            # Just interact with a new agent (will create a session automatically)
            session_id = interact_with_agent(storage, None, args.user)
            
            if session_id:
                # Show session info
                console.print("\n[bold blue]Session Info:[/bold blue]")
                display_session_info(manager, session_id)
                
                # Show all sessions
                console.print("\n[bold blue]All Sessions:[/bold blue]")
                list_all_sessions(manager)
        
    except StorageError as e:
        console.print(f"[bold red]Storage error: {str(e)}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")

if __name__ == "__main__":
    main() 