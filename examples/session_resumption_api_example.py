#!/usr/bin/env python3
"""
Example of using the session resumption API endpoint.

This example demonstrates how to create a session and then resume it using the REST API,
following the Agno patterns for persistent conversations.

Run this example after starting the API server:
   python examples/session_resumption_api_example.py
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.markdown import Markdown
from rich.table import Table

# Set up console for nicer output
console = Console()

# API server URL - adjust if needed
API_URL = "http://localhost:8000/api/v1"


def create_session(user_id: str, storage_type: str, storage_connection: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new session using the API endpoint.
    
    Args:
        user_id: The user identifier for the session
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        metadata: Optional metadata to associate with the session
        
    Returns:
        Dictionary containing the session information
        
    Raises:
        Exception: If the API call fails
    """
    # Prepare the request payload
    payload = {
        "user_id": user_id,
        "storage_type": storage_type,
        "storage_connection": storage_connection,
        "metadata": metadata or {}
    }
    
    try:
        # Make the API call to create a session
        console.print("[bold]Creating session...[/bold]")
        response = requests.post(
            f"{API_URL}/sessions/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the session information
        console.print("[bold green]✓[/bold green] Session created successfully")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error creating session: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        raise Exception(f"Failed to create session: {str(e)}")


def resume_session(session_id: str, storage_type: str, storage_connection: str, 
                   table_name: str = "agent_sessions") -> Dict[str, Any]:
    """
    Resume an existing session using the API endpoint.
    
    Args:
        session_id: The session ID to resume
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        table_name: Table or collection name for storing sessions
        
    Returns:
        Dictionary containing the session information and messages
        
    Raises:
        Exception: If the API call fails
    """
    # Prepare the request payload
    payload = {
        "session_id": session_id,
        "storage_type": storage_type,
        "storage_connection": storage_connection,
        "table_name": table_name,
        "validate_exists": True
    }
    
    try:
        # Make the API call to resume the session
        console.print(f"[bold]Resuming session {session_id}...[/bold]")
        response = requests.post(
            f"{API_URL}/sessions/resume",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the session information
        console.print("[bold green]✓[/bold green] Session resumed successfully")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error resuming session: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        raise Exception(f"Failed to resume session: {str(e)}")


def display_session_info(session_info: Dict[str, Any], show_messages: bool = False):
    """Display information about the created or resumed session."""
    # Create a table for session details
    table = Table(title=f"Session Information: {session_info.get('session_id')}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    # Add basic session properties
    table.add_row("Session ID", session_info.get("session_id", "N/A"))
    table.add_row("User ID", session_info.get("user_id", "N/A"))
    table.add_row("Created At", session_info.get("created_at", "N/A"))
    
    # Add any metadata properties
    metadata = session_info.get("metadata", {})
    if metadata:
        for key, value in metadata.items():
            if key not in ["session_id", "user_id", "created_at", "message_count"]:
                table.add_row(f"Metadata: {key}", str(value))
    
    # Display the session information table
    console.print(table)
    
    # If showing messages and they exist, display them
    if show_messages and "messages" in session_info:
        messages = session_info.get("messages", [])
        if messages:
            console.print(Panel(
                Pretty(messages),
                title=f"Session Messages ({len(messages)})",
                border_style="blue",
                expand=False
            ))
        else:
            console.print("[yellow]No messages in this session yet[/yellow]")


def main():
    """Main function to demonstrate session creation and resumption."""
    console.print(Panel(
        "This example demonstrates how to create and resume a session using the API endpoints",
        title="Session Resumption API Example",
        border_style="blue"
    ))
    
    # Define user ID and metadata for the session
    user_id = "example_user"
    metadata = {
        "app_version": "1.0",
        "client_info": "API Resume Example",
        "device": "Testing System",
        "preferences": {"language": "en-US"}
    }
    
    # For this example, we'll use SQLite storage
    storage_type = "sqlite"
    storage_path = "example_resume_sessions.db"
    
    console.print(f"[bold]User ID: [cyan]{user_id}[/cyan][/bold]")
    console.print(f"[bold]Storage: [cyan]{storage_type}[/cyan] at [cyan]{storage_path}[/cyan][/bold]")
    
    try:
        # Step 1: Create a new session
        session_info = create_session(
            user_id=user_id,
            storage_type=storage_type,
            storage_connection=storage_path,
            metadata=metadata
        )
        
        # Display the created session information
        console.print("\n[bold]Created Session Information:[/bold]")
        display_session_info(session_info)
        
        # Store the session ID for resuming
        session_id = session_info.get("session_id")
        console.print(f"\n[bold]Session ID for resumption: [cyan]{session_id}[/cyan][/bold]")
        
        # Simulate some time passing
        console.print("\n[bold yellow]Waiting 2 seconds to simulate time passing...[/bold yellow]")
        time.sleep(2)
        
        # Step 2: Resume the session
        resumed_session = resume_session(
            session_id=session_id,
            storage_type=storage_type,
            storage_connection=storage_path
        )
        
        # Display the resumed session information with messages
        console.print("\n[bold]Resumed Session Information:[/bold]")
        display_session_info(resumed_session, show_messages=True)
        
        # Step 3: Try to resume a non-existent session
        console.print("\n[bold]Attempting to resume a non-existent session...[/bold]")
        try:
            invalid_session = resume_session(
                session_id="non_existent_session_id",
                storage_type=storage_type,
                storage_connection=storage_path
            )
        except Exception as e:
            console.print(f"[bold yellow]Expected error: {str(e)}[/bold yellow]")
        
        console.print("\n[bold green]✓[/bold green] Session resumption example completed successfully")
        console.print(f"[bold]The session [cyan]{session_id}[/cyan] has been created and can be resumed in future API calls.[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Example failed: {str(e)}[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 