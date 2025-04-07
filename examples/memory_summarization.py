#!/usr/bin/env python3
"""
Memory Summarization Example

This example demonstrates how to use Agno's memory systems to create and utilize
conversation summaries. It shows:
1. How to initialize a memory system with summarization enabled
2. How conversation summaries are generated automatically
3. How to access and use these summaries in subsequent interactions
"""

import os
import sys
import uuid
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.memory.agent import AgentMemory
from agno.memory.storage import SqliteMemoryDb
from agno.memory.message import Message, MessageRole
from agno.storage import initialize_storage


# Create a console for pretty output
console = Console()


def create_memory_system(db_path, session_id, user_id):
    """
    Create a memory system with summarization capabilities.
    
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
    
    # Create the agent memory with summarization enabled
    memory = AgentMemory(
        session_id=session_id,
        user_id=user_id,
        memory_db=memory_db,
        max_messages=10,
        create_session_summary=True,
        update_session_summary_after_run=True,
        create_user_memories=True
    )
    
    return memory


def simulate_conversation(memory):
    """
    Simulate a conversation with memory being updated.
    
    Args:
        memory: An AgentMemory instance
    """
    # Add system message
    memory.add_message(Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful AI assistant specializing in financial modeling."
    ))
    
    # First user question
    console.print(Panel("[bold cyan]User:[/bold cyan] Tell me about DCF models", 
                        title="User Message"))
    memory.add_message(Message(
        role=MessageRole.USER,
        content="Tell me about DCF models"
    ))
    
    # Assistant response
    assistant_response1 = """
Discounted Cash Flow (DCF) models are used to estimate the value of an investment 
based on its expected future cash flows. The process involves:

1. Forecasting future cash flows
2. Determining an appropriate discount rate (typically WACC)
3. Calculating the present value of those cash flows
4. Adding terminal value

DCF is widely used in investment banking, equity research, and corporate finance.
"""
    console.print(Panel(Markdown(assistant_response1), title="Assistant Response"))
    memory.add_message(Message(
        role=MessageRole.ASSISTANT,
        content=assistant_response1
    ))
    
    # Second user question
    console.print(Panel("[bold cyan]User:[/bold cyan] What discount rate should I use?", 
                        title="User Message"))
    memory.add_message(Message(
        role=MessageRole.USER,
        content="What discount rate should I use?"
    ))
    
    # Assistant response
    assistant_response2 = """
The appropriate discount rate depends on several factors:

- For companies, you typically use the Weighted Average Cost of Capital (WACC)
- WACC incorporates both the cost of equity and cost of debt
- For cost of equity, you can use CAPM: Risk-free rate + Beta × Market risk premium
- For stable companies, discount rates often range from 8-12%
- For riskier ventures or growth companies, rates of 15-25% may be appropriate

The key is to match the discount rate to the risk profile of the cash flows being valued.
"""
    console.print(Panel(Markdown(assistant_response2), title="Assistant Response"))
    memory.add_message(Message(
        role=MessageRole.ASSISTANT,
        content=assistant_response2
    ))
    
    # Generate a summary after the conversation
    # In real scenarios, this would be triggered by the LLM
    console.print("\n[bold green]Generating conversation summary...[/bold green]")
    memory.generate_summary()
    memory.save_session_summary()


def demonstrate_memory_usage(db_path, session_id, user_id):
    """
    Demonstrate how to use memory summarization in a new session.
    
    Args:
        db_path: Path to the SQLite database
        session_id: Session identifier from previous conversation
        user_id: User identifier
    """
    # Create a new memory instance that will load from the database
    memory_db = SqliteMemoryDb(
        table_name="agent_memories",
        db_file=db_path
    )
    
    memory = AgentMemory(
        session_id=session_id,
        user_id=user_id,
        memory_db=memory_db,
        create_session_summary=True,
        update_session_summary_after_run=True
    )
    
    # Get the summary of the previous conversation
    summary = memory.get_summary()
    
    if summary:
        console.print("\n[bold yellow]Conversation Summary:[/bold yellow]")
        console.print(Panel(summary))
    else:
        console.print("\n[bold red]No summary found[/bold red]")
    
    # Simulate a new user question referencing the previous conversation
    console.print(Panel("[bold cyan]User:[/bold cyan] Can you remind me what we discussed about DCF models?", 
                        title="New User Message"))
    
    # In a real application, the LLM would use the summary to generate a response
    console.print("\n[bold green]Assistant would use this summary to contextualize the response...[/bold green]")
    
    # Display user memories if they exist
    if memory.user_memories:
        console.print("\n[bold yellow]User Memories:[/bold yellow]")
        console.print(Panel(json.dumps(memory.user_memories, indent=2)))


def main():
    """Run the memory summarization example."""
    # Create temporary database
    db_path = "example_memory.db"
    
    # Generate unique IDs
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    console.print(f"[bold]Memory Summarization Example[/bold]\n")
    console.print(f"Session ID: {session_id}")
    console.print(f"User ID: {user_id}")
    console.print(f"Database: {db_path}\n")
    
    # Create and populate memory
    memory = create_memory_system(db_path, session_id, user_id)
    
    # Simulate a conversation
    console.print("[bold]Simulating conversation...[/bold]\n")
    simulate_conversation(memory)
    
    # Demonstrate using the summary in a new session
    console.print("\n[bold]Demonstrating memory usage in a subsequent session...[/bold]\n")
    demonstrate_memory_usage(db_path, session_id, user_id)
    
    console.print("\n[bold green]Example completed.[/bold green]")
    console.print(f"SQLite database with memory data saved at: {db_path}")


if __name__ == "__main__":
    main() 