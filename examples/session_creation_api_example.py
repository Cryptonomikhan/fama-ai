#!/usr/bin/env python3
"""
Example of using the session creation API endpoint.

This example demonstrates how to create a session using the REST API
and shows how to use the created session for agent interactions.

Run this example after starting the API server:
   python examples/session_creation_api_example.py
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

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
        response = requests.post(
            f"{API_URL}/sessions/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the session information
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


def display_session_info(session_info: Dict[str, Any]):
    """Display information about the created session."""
    console.print(Panel(
        Pretty(session_info),
        title="Created Session Information",
        border_style="green"
    ))


def main():
    """Main function to demonstrate session creation."""
    console.print(Panel(
        "This example demonstrates how to create a session using the API endpoint",
        title="Session Creation API Example",
        border_style="blue"
    ))
    
    # Define user ID and metadata for the session
    user_id = "example_user"
    metadata = {
        "app_version": "1.0",
        "client_info": "API Example Script",
        "device": "MacBook Pro",
        "timezone": "UTC-5",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    # For this example, we'll use SQLite storage
    storage_type = "sqlite"
    storage_path = "example_sessions.db"
    
    console.print(f"[bold]Creating session for user: [cyan]{user_id}[/cyan][/bold]")
    console.print(f"[bold]Storage type: [cyan]{storage_type}[/cyan][/bold]")
    console.print(f"[bold]Storage path: [cyan]{storage_path}[/cyan][/bold]")
    
    try:
        # Create the session
        session_info = create_session(
            user_id=user_id,
            storage_type=storage_type,
            storage_connection=storage_path,
            metadata=metadata
        )
        
        # Display the session information
        display_session_info(session_info)
        
        # Store the session ID for future use
        session_id = session_info.get("session_id")
        console.print(f"[bold green]✓[/bold green] Session created successfully!")
        console.print(f"[bold]Session ID: [cyan]{session_id}[/cyan][/bold]")
        console.print("[bold]This session ID can be used in future API calls to continue the conversation.[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Session creation failed: {str(e)}[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 