#!/usr/bin/env python3
"""
Example of using session cleanup capabilities.

This example demonstrates how to delete individual sessions
and perform bulk cleanup operations following Agno's approach
to session management and lifecycle.

Run this example after starting the API server:
   python examples/session_cleanup_example.py
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
from rich.prompt import Prompt, Confirm

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


def list_sessions(storage_type: str, storage_connection: str, 
                  user_id: Optional[str] = None, table_name: str = "agent_sessions") -> List[Dict[str, Any]]:
    """
    List available sessions from the API.
    
    Args:
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        user_id: Optional user ID to filter sessions
        table_name: Table or collection name for storing sessions
        
    Returns:
        List of session information dictionaries
        
    Raises:
        Exception: If the API call fails
    """
    # This is a workaround since we don't have a dedicated list endpoint
    # In a real implementation, we'd have a dedicated endpoint for listing sessions
    
    # Create a session manager locally to list sessions
    try:
        from src.storage.factory import initialize_storage
        from src.storage.session import create_session_manager
        
        storage = initialize_storage(
            storage_type=storage_type,
            storage_connection=storage_connection,
            table_name=table_name
        )
        
        session_manager = create_session_manager(storage)
        
        # Get all sessions, filtered by user ID if provided
        session_ids = session_manager.list_sessions(user_id=user_id)
        
        # Get metadata for each session
        sessions = []
        for session_id in session_ids:
            try:
                metadata = session_manager.get_session_metadata(session_id)
                sessions.append({
                    "session_id": session_id,
                    "user_id": metadata.get("user_id", "unknown"),
                    "created_at": metadata.get("created_at", "unknown"),
                    "message_count": metadata.get("message_count", 0),
                    "metadata": metadata
                })
            except Exception as e:
                console.print(f"[bold yellow]Warning: Could not get metadata for session {session_id}: {str(e)}[/bold yellow]")
        
        return sessions
    
    except Exception as e:
        console.print(f"[bold red]Error listing sessions: {str(e)}[/bold red]")
        raise Exception(f"Failed to list sessions: {str(e)}")


def delete_session(session_id: str, storage_type: str, storage_connection: str, 
                   table_name: str = "agent_sessions") -> bool:
    """
    Delete a specific session.
    
    Args:
        session_id: The session ID to delete
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        table_name: Table or collection name for storing sessions
        
    Returns:
        True if the session was deleted successfully, False otherwise
        
    Raises:
        Exception: If the API call fails
    """
    try:
        # Make the API call to delete the session
        console.print(f"[bold]Deleting session {session_id}...[/bold]")
        response = requests.delete(
            f"{API_URL}/sessions/{session_id}",
            params={
                "storage_type": storage_type,
                "storage_connection": storage_connection,
                "table_name": table_name
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return success
        console.print(f"[bold green]✓[/bold green] Session {session_id} deleted successfully")
        return True
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error deleting session: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        return False


def cleanup_sessions(storage_type: str, storage_connection: str,
                     user_id: Optional[str] = None, max_age_days: int = 30,
                     keep_latest_per_user: int = 5, table_name: str = "agent_sessions") -> Dict[str, Any]:
    """
    Clean up sessions based on age and retention policy.
    
    Args:
        storage_type: Storage backend type (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        user_id: Optional user ID to filter sessions
        max_age_days: Maximum age of sessions to keep in days
        keep_latest_per_user: Number of latest sessions to keep per user
        table_name: Table or collection name for storing sessions
        
    Returns:
        Dictionary containing cleanup results
        
    Raises:
        Exception: If the API call fails
    """
    # Prepare the request payload
    payload = {
        "storage_type": storage_type,
        "storage_connection": storage_connection,
        "table_name": table_name,
        "user_id": user_id,
        "max_age_days": max_age_days,
        "keep_latest_per_user": keep_latest_per_user
    }
    
    try:
        # Make the API call to clean up sessions
        console.print("[bold]Cleaning up sessions...[/bold]")
        response = requests.post(
            f"{API_URL}/sessions/cleanup",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the cleanup results
        result = response.json()
        console.print(f"[bold green]✓[/bold green] Cleanup completed: {result['deleted_count']} sessions deleted, {result['remaining_count']} sessions remaining")
        return result
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error cleaning up sessions: {str(e)}[/bold red]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                console.print(f"[bold red]API error: {error_details.get('detail', 'Unknown error')}[/bold red]")
            except ValueError:
                console.print(f"[bold red]API response: {e.response.text}[/bold red]")
        raise Exception(f"Failed to clean up sessions: {str(e)}")


def display_sessions(sessions: List[Dict[str, Any]]):
    """Display a list of sessions in a table."""
    if not sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return
    
    # Create a table for sessions
    table = Table(title=f"Available Sessions ({len(sessions)})")
    table.add_column("Session ID", style="cyan")
    table.add_column("User ID", style="green")
    table.add_column("Created At", style="blue")
    table.add_column("Message Count", style="magenta")
    
    # Add each session to the table
    for session in sessions:
        table.add_row(
            session.get("session_id", "N/A"),
            session.get("user_id", "N/A"),
            session.get("created_at", "N/A"),
            str(session.get("message_count", 0))
        )
    
    # Display the table
    console.print(table)


def main():
    """Main function to demonstrate session cleanup."""
    console.print(Panel(
        "This example demonstrates how to clean up sessions",
        title="Session Cleanup Example",
        border_style="blue"
    ))
    
    # Storage settings
    storage_type = "sqlite"
    storage_path = "cleanup_example_sessions.db"
    
    console.print(f"[bold]Storage: [cyan]{storage_type}[/cyan] at [cyan]{storage_path}[/cyan][/bold]")
    
    try:
        # Step 1: Create multiple sessions for different users
        console.print("\n[bold]Step 1: Creating sample sessions for cleanup demo[/bold]")
        
        # Create sessions for user1
        user1_sessions = []
        for i in range(7):  # Create 7 sessions (more than we'll keep)
            metadata = {
                "app_version": "1.0",
                "client_info": f"Cleanup Example {i+1}",
                "device": "Testing Environment",
                "test_number": i+1
            }
            
            session_info = create_session(
                user_id="cleanup_user1",
                storage_type=storage_type,
                storage_connection=storage_path,
                metadata=metadata
            )
            
            user1_sessions.append(session_info)
            
            # Small delay between sessions to ensure different timestamps
            time.sleep(0.5)
        
        # Create sessions for user2
        user2_sessions = []
        for i in range(4):  # Create 4 sessions (less than we'll keep)
            metadata = {
                "app_version": "1.0",
                "client_info": f"Cleanup Example U2-{i+1}",
                "device": "Testing Environment",
                "test_number": i+1
            }
            
            session_info = create_session(
                user_id="cleanup_user2",
                storage_type=storage_type,
                storage_connection=storage_path,
                metadata=metadata
            )
            
            user2_sessions.append(session_info)
            
            # Small delay between sessions to ensure different timestamps
            time.sleep(0.5)
        
        # Step 2: List all sessions
        console.print("\n[bold]Step 2: Listing all sessions[/bold]")
        all_sessions = list_sessions(
            storage_type=storage_type,
            storage_connection=storage_path
        )
        
        display_sessions(all_sessions)
        
        # Step 3: Delete a specific session (manual cleanup)
        console.print("\n[bold]Step 3: Manual deletion of a specific session[/bold]")
        
        if user1_sessions:
            session_to_delete = user1_sessions[0]["session_id"]
            console.print(f"Deleting session: [cyan]{session_to_delete}[/cyan]")
            
            # Delete the session
            success = delete_session(
                session_id=session_to_delete,
                storage_type=storage_type,
                storage_connection=storage_path
            )
            
            if success:
                console.print(f"[bold green]✓[/bold green] Session {session_to_delete} deleted manually")
            else:
                console.print(f"[bold red]✗[/bold red] Failed to delete session {session_to_delete}")
        
        # List sessions again to confirm deletion
        console.print("\n[bold]Sessions after manual deletion:[/bold]")
        current_sessions = list_sessions(
            storage_type=storage_type,
            storage_connection=storage_path
        )
        
        display_sessions(current_sessions)
        
        # Step 4: Automatic session cleanup for a specific user
        console.print("\n[bold]Step 4: Automatic cleanup for user1 sessions[/bold]")
        console.print("[bold]This will keep only the 3 most recent sessions for user1[/bold]")
        
        # Clean up user1 sessions
        cleanup_result = cleanup_sessions(
            storage_type=storage_type,
            storage_connection=storage_path,
            user_id="cleanup_user1",
            max_age_days=30,  # Keep sessions from the last 30 days
            keep_latest_per_user=3  # But only keep the 3 most recent
        )
        
        # Display deleted sessions
        if cleanup_result.get("deleted_sessions"):
            console.print("[bold]Deleted sessions:[/bold]")
            for session_id in cleanup_result.get("deleted_sessions", []):
                console.print(f"  - [dim]{session_id}[/dim]")
        
        # List user1 sessions after cleanup
        console.print("\n[bold]User1 sessions after cleanup:[/bold]")
        user1_sessions_after = list_sessions(
            storage_type=storage_type,
            storage_connection=storage_path,
            user_id="cleanup_user1"
        )
        
        display_sessions(user1_sessions_after)
        
        # Step 5: Global cleanup with retention policy
        console.print("\n[bold]Step 5: Global cleanup with retention policy[/bold]")
        
        # Ask user for confirmation
        if Confirm.ask("[bold]Do you want to perform a global cleanup?[/bold]", default=True):
            # Clean up all sessions
            global_cleanup_result = cleanup_sessions(
                storage_type=storage_type,
                storage_connection=storage_path,
                user_id=None,  # All users
                max_age_days=30,
                keep_latest_per_user=2  # Only keep the 2 most recent per user
            )
            
            # List all sessions after global cleanup
            console.print("\n[bold]All sessions after global cleanup:[/bold]")
            final_sessions = list_sessions(
                storage_type=storage_type,
                storage_connection=storage_path
            )
            
            display_sessions(final_sessions)
        
        console.print("\n[bold green]✓[/bold green] Session cleanup example completed successfully")
        
    except Exception as e:
        console.print(f"[bold red]Example failed: {str(e)}[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 