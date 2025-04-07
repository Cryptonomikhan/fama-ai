#!/usr/bin/env python3
"""
Example of using session metadata tracking capabilities.

This example demonstrates how to retrieve and update session metadata
using the REST API, following Agno's approach to session management.

Run this example after starting the API server:
   python examples/session_metadata_example.py
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
from rich.prompt import Prompt

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


def get_session_metadata(session_id: str, storage_type: str, storage_connection: str, 
                        table_name: str = "agent_sessions") -> Dict[str, Any]:
    """
    Retrieve metadata for an existing session.
    
    Args:
        session_id: The session ID to get metadata for
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        table_name: Table or collection name for storing sessions
        
    Returns:
        Dictionary containing the session metadata
        
    Raises:
        Exception: If the API call fails
    """
    try:
        # Make the API call to get session metadata
        console.print(f"[bold]Getting metadata for session {session_id}...[/bold]")
        response = requests.get(
            f"{API_URL}/sessions/metadata/{session_id}",
            params={
                "storage_type": storage_type,
                "storage_connection": storage_connection,
                "table_name": table_name
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the session information
        console.print("[bold green]✓[/bold green] Session metadata retrieved successfully")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error getting session metadata: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        raise Exception(f"Failed to get session metadata: {str(e)}")


def update_session_metadata(session_id: str, storage_type: str, storage_connection: str, 
                          metadata: Dict[str, Any], table_name: str = "agent_sessions") -> Dict[str, Any]:
    """
    Update metadata for an existing session.
    
    Args:
        session_id: The session ID to update metadata for
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        metadata: New metadata to associate with the session
        table_name: Table or collection name for storing sessions
        
    Returns:
        Dictionary containing the updated session metadata
        
    Raises:
        Exception: If the API call fails
    """
    # Prepare the request payload
    payload = {
        "session_id": session_id,
        "storage_type": storage_type,
        "storage_connection": storage_connection,
        "table_name": table_name,
        "metadata": metadata
    }
    
    try:
        # Make the API call to update session metadata
        console.print(f"[bold]Updating metadata for session {session_id}...[/bold]")
        response = requests.put(
            f"{API_URL}/sessions/metadata",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the session information
        console.print("[bold green]✓[/bold green] Session metadata updated successfully")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error updating session metadata: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        raise Exception(f"Failed to update session metadata: {str(e)}")


def display_metadata(metadata_info: Dict[str, Any]):
    """Display detailed information about session metadata."""
    # Create a table for session details
    table = Table(title=f"Session Metadata: {metadata_info.get('session_id')}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    # Add basic session properties
    table.add_row("Session ID", metadata_info.get("session_id", "N/A"))
    table.add_row("User ID", metadata_info.get("user_id", "N/A"))
    table.add_row("Created At", metadata_info.get("created_at", "N/A"))
    table.add_row("Last Updated", metadata_info.get("last_updated", "N/A"))
    table.add_row("Message Count", str(metadata_info.get("message_count", "N/A")))
    
    # Add all metadata properties
    metadata = metadata_info.get("metadata", {})
    if metadata:
        for key, value in metadata.items():
            # Skip properties that are already displayed
            if key not in ["session_id", "user_id", "created_at", "last_updated", "message_count"]:
                table.add_row(f"Metadata: {key}", str(value) if not isinstance(value, dict) else json.dumps(value))
    
    # Display the table
    console.print(table)


def main():
    """Main function to demonstrate session metadata tracking."""
    console.print(Panel(
        "This example demonstrates how to work with session metadata",
        title="Session Metadata Example",
        border_style="blue"
    ))
    
    # Define user ID and initial metadata for the session
    user_id = "metadata_example_user"
    initial_metadata = {
        "app_version": "1.0",
        "client_info": "Metadata Example",
        "device": "Testing Environment",
        "preferences": {
            "theme": "dark",
            "language": "en-US",
            "notifications": True
        }
    }
    
    # For this example, we'll use SQLite storage
    storage_type = "sqlite"
    storage_path = "metadata_example_sessions.db"
    
    console.print(f"[bold]User ID: [cyan]{user_id}[/cyan][/bold]")
    console.print(f"[bold]Storage: [cyan]{storage_type}[/cyan] at [cyan]{storage_path}[/cyan][/bold]")
    
    try:
        # Step 1: Create a new session with initial metadata
        console.print("\n[bold]Step 1: Creating a new session with initial metadata[/bold]")
        session_info = create_session(
            user_id=user_id,
            storage_type=storage_type,
            storage_connection=storage_path,
            metadata=initial_metadata
        )
        
        # Store the session ID for later use
        session_id = session_info.get("session_id")
        console.print(f"[bold]Created session with ID: [cyan]{session_id}[/cyan][/bold]")
        
        # Display the initial metadata
        console.print("\n[bold]Initial Session Metadata:[/bold]")
        display_metadata(session_info)
        
        # Step 2: Retrieve the session metadata
        console.print("\n[bold]Step 2: Retrieving the session metadata[/bold]")
        metadata_info = get_session_metadata(
            session_id=session_id,
            storage_type=storage_type,
            storage_connection=storage_path
        )
        
        console.print("\n[bold]Retrieved Session Metadata:[/bold]")
        display_metadata(metadata_info)
        
        # Step 3: Update the session metadata
        console.print("\n[bold]Step 3: Updating the session metadata[/bold]")
        
        # Create new metadata with additional fields
        updated_metadata = {
            # Keep existing preferences
            "preferences": initial_metadata.get("preferences", {}),
            # Update app_version
            "app_version": "1.1",
            # Add new fields
            "last_interaction": time.strftime("%Y-%m-%d %H:%M:%S"),
            "interaction_count": 1,
            "user_topics": ["finance", "investing"],
            "completion_status": {
                "onboarding": True,
                "profile": False,
                "first_query": True
            }
        }
        
        # Update the session metadata
        updated_info = update_session_metadata(
            session_id=session_id,
            storage_type=storage_type,
            storage_connection=storage_path,
            metadata=updated_metadata
        )
        
        console.print("\n[bold]Updated Session Metadata:[/bold]")
        display_metadata(updated_info)
        
        # Step 4: Add more fields to the session metadata
        console.print("\n[bold]Step 4: Adding more fields to the session metadata[/bold]")
        
        # Simulate a user interaction - get input from user
        user_topic = Prompt.ask("[bold]Enter a topic you're interested in[/bold]", default="AI")
        
        # Get the existing metadata
        current_metadata = updated_info.get("metadata", {})
        
        # Create metadata with new fields
        new_metadata = {
            # Keep existing fields
            **current_metadata.get("preferences", {}),
            # Update interaction count
            "interaction_count": current_metadata.get("interaction_count", 1) + 1,
            "last_interaction": time.strftime("%Y-%m-%d %H:%M:%S"),
            # Add user's topic to the list
            "user_topics": current_metadata.get("user_topics", []) + [user_topic],
            # Add sentiment analysis
            "sentiment": {
                "positive": 0.8,
                "neutral": 0.15,
                "negative": 0.05
            }
        }
        
        # Update the session metadata again
        final_info = update_session_metadata(
            session_id=session_id,
            storage_type=storage_type,
            storage_connection=storage_path,
            metadata=new_metadata
        )
        
        console.print("\n[bold]Final Session Metadata:[/bold]")
        display_metadata(final_info)
        
        console.print("\n[bold green]✓[/bold green] Session metadata example completed successfully")
        console.print(f"[bold]The session [cyan]{session_id}[/cyan] metadata has been created, retrieved, and updated.[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Example failed: {str(e)}[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 