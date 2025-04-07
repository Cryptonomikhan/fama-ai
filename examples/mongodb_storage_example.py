#!/usr/bin/env python3
"""
Example demonstrating MongoDB storage usage with Agno agents.

This example shows how to initialize and use MongoDB storage for persistent 
agent sessions based on the Agno framework.
"""
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Import our storage factory
from src.storage.factory import initialize_storage

# Database URL for MongoDB
# The syntax follows the format: mongodb://username:password@host:port/db
# Note: You'll need to have MongoDB running, you can set it up with Docker:
# docker run -d \
#   -e MONGO_INITDB_ROOT_USERNAME=ai \
#   -e MONGO_INITDB_ROOT_PASSWORD=ai \
#   -p 27017:27017 \
#   --name mongodb \
#   mongo:latest
DB_URL = "mongodb://ai:ai@localhost:27017/agno"

# Rich console for pretty output
console = Console()

def print_chat_history(agent):
    """Print the agent's chat history"""
    # Print history
    console.print(
        Panel(
            JSON(json.dumps([m.model_dump(include={"role", "content"}) for m in agent.memory.messages]), indent=4),
            title=f"Chat History for session_id: {agent.session_id}",
            expand=True,
        )
    )

def main():
    """Run the example"""
    # Initialize storage using our factory
    storage = initialize_storage(
        storage_type="mongodb",
        storage_connection=DB_URL,
        table_name="agent_sessions" # In MongoDB, this becomes the collection name
    )
    
    # Create an agent with the storage
    agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        # Pass the initialized storage
        storage=storage,
        # Add DuckDuckGo search tools
        tools=[DuckDuckGoTools()],
        # Set add_history_to_messages=true to add previous chat history to the messages
        add_history_to_messages=True,
        # Number of historical responses to add to the messages.
        num_history_responses=3,
        # Description creates a system prompt for the agent
        description="You are a helpful assistant that always responds in a polite, upbeat and positive manner.",
    )
    
    # Create a run and ask a question
    agent.print_response("Share a 2 sentence horror story", stream=True)
    
    # Print the chat history
    print_chat_history(agent)
    
    # Ask a follow up question that continues the conversation
    agent.print_response("What was my first message?", stream=True)
    
    # Print the updated chat history
    print_chat_history(agent)
    
    # Display the session ID for future reference
    console.print(f"\nTo continue this conversation in the future, use session_id: {agent.session_id}")
    
if __name__ == "__main__":
    main() 