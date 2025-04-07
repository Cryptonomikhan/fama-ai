#!/usr/bin/env python3
"""
Advanced Memory Integration Example with Agno

This example demonstrates how to use all of Agno's memory capabilities:
1. Chat history memory
2. User-specific memories
3. Conversation summarization
4. Memory pruning for long conversations
5. Memory serialization and persistence

Run this example with:
   python examples/advanced_memory_example.py
"""
import os
import json
import uuid
from pprint import pprint
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.json import JSON
from rich.table import Table

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.memory.agent import AgentMemory
from agno.memory.db.sqlite import SqliteMemoryDb

# Import our storage factory
from src.storage.factory import initialize_storage

# Create a console for rich output
console = Console()

def print_section(title, content=None):
    """Print a section header with optional content."""
    console.print(f"\n[bold cyan]{'='*20} {title} {'='*20}[/bold cyan]")
    if content:
        console.print(content)

def print_memory_contents(agent):
    """Print memory contents in a formatted manner."""
    print_section("Memory Contents")
    
    # Create a table for the chat history
    table = Table(title="Chat History")
    table.add_column("Role", style="bold")
    table.add_column("Content")
    
    for message in agent.memory.messages:
        table.add_row(message.role, message.content[:100] + "..." if len(message.content) > 100 else message.content)
    
    console.print(table)
    
    # Display user memories if available
    if hasattr(agent.memory, 'memories') and agent.memory.memories:
        print_section("User Memories")
        for memory in agent.memory.memories:
            console.print(Panel(
                memory,
                title="User Memory",
                border_style="green"
            ))
    
    # Display summary if available
    if hasattr(agent.memory, 'summary') and agent.memory.summary:
        print_section("Conversation Summary")
        console.print(Panel(
            agent.memory.summary,
            title="Summary",
            border_style="yellow"
        ))

def main():
    """Run the advanced memory example."""
    # Create directories if they don't exist
    os.makedirs("tmp", exist_ok=True)
    
    # Generate unique identifiers
    session_id = str(uuid.uuid4())
    user_id = "user-12345"
    
    print_section("Initializing Agent with Advanced Memory", 
                 f"Session ID: {session_id}\nUser ID: {user_id}")
    
    # Initialize memory database for persistent memories
    memory_db = SqliteMemoryDb(
        table_name="agent_memories",
        db_file="tmp/memory_storage.db"
    )
    
    # Initialize storage
    storage = initialize_storage(
        storage_type="sqlite",
        storage_connection="tmp/agent_storage.db",
        table_name="agent_sessions"
    )
    
    # Create the agent with advanced memory capabilities
    agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        
        # Memory configuration
        memory=AgentMemory(
            db=memory_db,
            
            # Enable user memory creation
            create_user_memories=True,
            update_user_memories_after_run=True,
            
            # Enable session summary
            create_session_summary=True,
            update_session_summary_after_run=True,
            
            # Configure max messages to demonstrate pruning
            max_messages=10
        ),
        
        # Storage for persistence
        storage=storage,
        
        # Add message history to prompts
        add_history_to_messages=True,
        num_history_responses=5,
        
        # Enable agent to read chat history (Agno tool)
        read_chat_history=True,
        
        # Agent configuration
        session_id=session_id,
        user_id=user_id,
        description="You are a knowledgeable financial advisor that helps users with investment decisions and remembers important details about them."
    )
    
    print_section("Agent Initialized", 
                 "The agent is configured with advanced memory capabilities including chat history, user memories, and summarization.")
    
    # First interaction
    print_section("First Interaction")
    response = agent.get_response("Hi, I'm Alex and I'm interested in investing for retirement. I'm 35 years old.")
    console.print(Panel(response, title="Agent Response", border_style="green"))
    print_memory_contents(agent)
    
    # Second interaction with personal details
    print_section("Second Interaction")
    response = agent.get_response("I currently live in Boston and work as a software engineer. I have about $50,000 saved up that I want to invest.")
    console.print(Panel(response, title="Agent Response", border_style="green"))
    print_memory_contents(agent)
    
    # Third interaction with a question
    print_section("Third Interaction")
    response = agent.get_response("What investment options would you recommend for someone in my situation?")
    console.print(Panel(response, title="Agent Response", border_style="green"))
    print_memory_contents(agent)
    
    # Fourth interaction testing memory recall
    print_section("Fourth Interaction - Testing Memory Recall")
    response = agent.get_response("Can you remind me how old I am and what I do for a living?")
    console.print(Panel(response, title="Agent Response", border_style="green"))
    print_memory_contents(agent)
    
    # Demonstrate exporting memory state
    print_section("Memory Serialization")
    memory_dict = agent.memory.to_dict()
    console.print(Syntax(
        json.dumps(memory_dict, indent=2, default=str)[:1000] + "...",
        "json",
        theme="monokai"
    ))
    
    # Session resumption demonstration
    print_section("Session Resumption Simulation")
    console.print("[bold]Imagine the API has restarted, but we can resume using the same session_id:[/bold]")
    
    # Create a new agent with the same session ID
    resumed_agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        memory=AgentMemory(
            db=memory_db,
            create_user_memories=True,
            create_session_summary=True
        ),
        storage=storage,
        add_history_to_messages=True,
        session_id=session_id,  # Use the same session ID to resume
        user_id=user_id,
        description="You are a knowledgeable financial advisor that helps users with investment decisions and remembers important details about them."
    )
    
    # Test memory after resumption
    response = resumed_agent.get_response("Hello again. Do you remember my name and how much I have saved up?")
    console.print(Panel(response, title="Agent Response After Resumption", border_style="green"))
    print_memory_contents(resumed_agent)
    
    # Conclusion
    print_section("Conclusion")
    console.print("[bold green]This example demonstrated Agno's advanced memory capabilities:[/bold green]")
    console.print("1. Chat history persistence using SQLite storage")
    console.print("2. User-specific memories extracted from conversations")
    console.print("3. Conversation summarization for context management")
    console.print("4. Memory pruning (max_messages configuration)")
    console.print("5. Session continuity across interactions")
    console.print("\n[italic]These capabilities are built into Agno and can be configured through agent parameters, no custom implementation required.[/italic]")

if __name__ == "__main__":
    main() 