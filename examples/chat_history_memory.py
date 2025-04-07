#!/usr/bin/env python3
"""
Example demonstrating chat history memory with Agno agents.

This example shows how to use Agno's built-in memory capabilities to maintain
conversation context, format messages for models, and serialize/deserialize
the memory.

Run this example with:
   python examples/chat_history_memory.py
"""
import json
import uuid
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.markdown import Markdown
from rich.syntax import Syntax

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.memory.agent import AgentMemory, MessageRole

# Rich console for pretty output
console = Console()

def print_section(title, content=None):
    """Print a section header with optional content."""
    console.print(f"\n[bold cyan]{'='*20} {title} {'='*20}[/bold cyan]")
    if content:
        console.print(content)

def add_system_message(memory, content):
    """Add a system message to the memory."""
    print_section("Adding System Message", f"[blue]{content}[/blue]")
    memory.add_message(MessageRole.SYSTEM, content)
    return memory

def add_user_message(memory, content):
    """Add a user message to the memory."""
    print_section("Adding User Message", f"[green]{content}[/green]")
    memory.add_message(MessageRole.USER, content)
    return memory

def add_assistant_message(memory, content):
    """Add an assistant message to the memory."""
    print_section("Adding Assistant Message", f"[yellow]{content}[/yellow]")
    memory.add_message(MessageRole.ASSISTANT, content)
    return memory

def print_chat_history(memory):
    """Print the chat history in a formatted manner."""
    print_section("Chat History")
    
    # Print each message in the memory
    for i, message in enumerate(memory.messages):
        role_colors = {
            "system": "bold blue",
            "user": "bold green", 
            "assistant": "bold yellow"
        }
        color = role_colors.get(message.role, "white")
        
        console.print(Panel(
            message.content,
            title=f"{message.role.capitalize()} (Message {i+1})",
            border_style=color
        ))

def print_formatted_messages(memory):
    """Print the messages formatted for a model prompt."""
    print_section("Formatted Messages for Model")
    
    formatted = memory.get_formatted_messages()
    console.print(Syntax(
        json.dumps(formatted, indent=2),
        "json",
        theme="monokai",
        line_numbers=True
    ))

def main():
    """Run the memory example."""
    # Create a unique session ID for this example
    session_id = str(uuid.uuid4())
    user_id = "user-123"
    
    print_section("Initializing Memory", f"Session ID: {session_id}\nUser ID: {user_id}")
    
    # Initialize the memory with a maximum of 10 messages
    memory = AgentMemory(max_messages=10)
    
    # Add system message (prompt)
    memory = add_system_message(
        memory,
        "You are a helpful financial assistant that provides accurate information about investments."
    )
    
    # Add a user message
    memory = add_user_message(
        memory, 
        "What are the best strategies for long-term investing?"
    )
    
    # Add an assistant response
    memory = add_assistant_message(
        memory,
        "Long-term investing typically benefits from diversification, regular contributions, and patience. "
        "Some proven strategies include index investing, dollar-cost averaging, and maintaining an "
        "appropriate asset allocation based on your risk tolerance and time horizon."
    )
    
    # Print the chat history
    print_chat_history(memory)
    
    # Show how the messages would be formatted for a model
    print_formatted_messages(memory)
    
    # Add another exchange
    memory = add_user_message(
        memory,
        "How should I think about asset allocation?"
    )
    
    memory = add_assistant_message(
        memory,
        "Asset allocation involves dividing your portfolio among different asset classes like stocks, bonds, "
        "and cash equivalents. The right allocation depends on your goals, time horizon, and risk tolerance. "
        "Generally, a longer time horizon allows for more stock exposure, while shorter timeframes may "
        "require more conservative allocations with bonds and cash."
    )
    
    # Print the updated chat history
    print_chat_history(memory)
    
    # Demonstrate serialization
    print_section("Serializing Memory to Dictionary")
    memory_dict = memory.to_dict()
    console.print(Syntax(
        json.dumps(memory_dict, indent=2),
        "json",
        theme="monokai",
        line_numbers=True
    ))
    
    # Demonstrate deserialization
    print_section("Restoring Memory from Dictionary")
    restored_memory = AgentMemory.from_dict(memory_dict)
    print_chat_history(restored_memory)
    
    print_section("Conclusion")
    console.print("[bold green]This example demonstrated how to use Agno's built-in memory capabilities to:[/bold green]")
    console.print("1. Create and manage chat history")
    console.print("2. Add different types of messages (system, user, assistant)")
    console.print("3. Format messages for model prompts")
    console.print("4. Serialize and deserialize memory for storage")
    console.print("\n[italic]For persistent memory across sessions, use Agno's storage adapters like SqliteStorage, PostgresStorage, etc.[/italic]")

if __name__ == "__main__":
    main() 