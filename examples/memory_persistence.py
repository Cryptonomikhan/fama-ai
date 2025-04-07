#!/usr/bin/env python3
"""
Memory Persistence Example

This example demonstrates how Agno's memory systems persist across multiple sessions.
It shows:
1. How to initialize a memory system with persistence
2. How memory is stored in a database and retrieved in later sessions
3. How user-specific memories are maintained across different conversations
"""

import os
import sys
import uuid
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.memory.agent import AgentMemory
from agno.memory.db.sqlite import SqliteMemoryDb
from agno.memory.memory import Message, MessageRole


# Create a console for pretty output
console = Console()


def create_memory_system(db_path, session_id, user_id):
    """
    Create a memory system with persistence capabilities.
    
    Args:
        db_path: Path to the SQLite database
        session_id: Session identifier
        user_id: User identifier
        
    Returns:
        An initialized AgentMemory instance
    """
    # Initialize the memory database
    memory_db = SqliteMemoryDb(
        table_name="agent_memories",
        db_file=db_path
    )
    
    # Create the agent memory with persistence enabled
    memory = AgentMemory(
        session_id=session_id,
        user_id=user_id,
        memory_db=memory_db,
        max_messages=10,
        create_user_memories=True,
        update_user_memories_after_run=True
    )
    
    return memory


def first_session(db_path, user_id):
    """
    Simulate a first conversation session with memory.
    
    Args:
        db_path: Path to the SQLite database
        user_id: User identifier
        
    Returns:
        Session ID used for this conversation
    """
    session_id = str(uuid.uuid4())
    console.print(f"[bold]First Session[/bold] (ID: {session_id})\n")
    
    # Create memory for this session
    memory = create_memory_system(db_path, session_id, user_id)
    
    # System message
    memory.add_message(Message(
        role=MessageRole.SYSTEM,
        content="You are a financial advisor helping with investment strategies."
    ))
    
    # First interaction
    console.print(Panel("[bold cyan]User:[/bold cyan] I'd like advice on tech stock investments", 
                        title="User Message"))
    memory.add_message(Message(
        role=MessageRole.USER,
        content="I'd like advice on tech stock investments"
    ))
    
    # Add response
    assistant_response = """
Tech stocks can be a valuable part of a diversified portfolio. Here are some considerations:

1. Look for companies with strong fundamentals and competitive advantages
2. Consider both established players (FAANG) and emerging innovators
3. Be mindful of valuation - tech stocks often trade at premium multiples
4. Monitor regulatory risks which can impact the sector
5. For reduced risk, consider tech-focused ETFs

Would you like specific recommendations for your risk profile?
"""
    console.print(Panel(Markdown(assistant_response), title="Assistant Response"))
    memory.add_message(Message(
        role=MessageRole.ASSISTANT,
        content=assistant_response
    ))
    
    # Update user memories manually (in a real app, the LLM would do this)
    memory.user_memories["interests"] = "Technology stocks, investments"
    memory.user_memories["risk_profile"] = "Unknown, needs clarification"
    memory.save_user_memories()
    
    console.print("\n[bold green]Session completed and memories saved[/bold green]")
    return session_id


def second_session(db_path, user_id, previous_session_id):
    """
    Simulate a second conversation session with the same user but a new session ID.
    
    Args:
        db_path: Path to the SQLite database
        user_id: User identifier from first session
        previous_session_id: Session ID from the first conversation
    """
    session_id = str(uuid.uuid4())
    console.print(f"\n[bold]Second Session[/bold] (ID: {session_id})\n")
    
    # Create a new memory instance for this session
    memory = create_memory_system(db_path, session_id, user_id)
    
    # Display existing user memories
    if memory.user_memories:
        console.print("[bold yellow]Retrieved User Memories:[/bold yellow]")
        console.print(Panel(json.dumps(memory.user_memories, indent=2)))
    else:
        console.print("[bold red]No user memories found[/bold red]")
    
    # List previous sessions
    sessions = memory.memory_db.list_sessions(user_id)
    console.print(f"[bold yellow]Previous Sessions:[/bold yellow] {', '.join(sessions)}")
    
    # New interaction
    console.print(Panel("[bold cyan]User:[/bold cyan] I'm looking for moderate risk investments", 
                        title="User Message"))
    memory.add_message(Message(
        role=MessageRole.USER,
        content="I'm looking for moderate risk investments"
    ))
    
    # Add response that references previous context
    assistant_response = """
Based on your interest in tech stocks from our previous conversation, here are some moderate risk tech investment options:

1. Tech-focused index funds like VGT or QQQ
2. Established tech companies with strong cash flows like Microsoft or Apple
3. A mix of growth and value tech stocks
4. Cloud computing focused ETFs

These provide exposure to the tech sector with more moderate risk profiles than individual growth stocks.
"""
    console.print(Panel(Markdown(assistant_response), title="Assistant Response"))
    memory.add_message(Message(
        role=MessageRole.ASSISTANT,
        content=assistant_response
    ))
    
    # Update user memories
    memory.user_memories["risk_profile"] = "Moderate risk tolerance"
    memory.save_user_memories()
    
    console.print("\n[bold green]Second session completed with updated memories[/bold green]")


def retrieve_conversation_history(db_path, user_id, session_id):
    """
    Demonstrate how to retrieve conversation history from a previous session.
    
    Args:
        db_path: Path to the SQLite database
        user_id: User identifier
        session_id: Session identifier of the conversation to retrieve
    """
    console.print(f"\n[bold]Retrieving Conversation History[/bold] (Session ID: {session_id})\n")
    
    # Create memory system
    memory_db = SqliteMemoryDb(
        table_name="agent_memories",
        db_file=db_path
    )
    
    memory = AgentMemory(
        session_id=session_id,
        user_id=user_id,
        memory_db=memory_db
    )
    
    # Display messages from the session
    console.print("[bold yellow]Retrieved Messages:[/bold yellow]")
    
    for i, msg in enumerate(memory.messages):
        role_color = {
            MessageRole.SYSTEM: "magenta",
            MessageRole.USER: "cyan",
            MessageRole.ASSISTANT: "green"
        }.get(msg.role, "white")
        
        console.print(Panel(
            f"[bold {role_color}]{msg.role}:[/bold {role_color}] {msg.content}",
            title=f"Message {i+1}"
        ))


def main():
    """Run the memory persistence example."""
    # Create database
    db_path = "example_persistence.db"
    
    # Generate user ID that will be consistent across sessions
    user_id = str(uuid.uuid4())
    
    console.print(f"[bold]Memory Persistence Example[/bold]\n")
    console.print(f"User ID: {user_id}")
    console.print(f"Database: {db_path}\n")
    
    # First conversation session
    first_session_id = first_session(db_path, user_id)
    
    # Simulate time passing between sessions
    console.print("\nWaiting 3 seconds to simulate time between sessions...")
    time.sleep(3)
    
    # Second session with the same user but different session ID
    second_session(db_path, user_id, first_session_id)
    
    # Retrieve conversation history from first session
    retrieve_conversation_history(db_path, user_id, first_session_id)
    
    console.print("\n[bold green]Example completed.[/bold green]")
    console.print(f"SQLite database with memory data saved at: {db_path}")


if __name__ == "__main__":
    main() 