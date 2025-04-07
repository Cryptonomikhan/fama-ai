# Fama AI Examples

This directory contains example scripts that demonstrate the functionality of the Fama AI system.

## Storage Examples

### Agent and Team Storage

The following examples demonstrate how to use persistent storage with agents and teams:

- **agent_with_storage_example.py**: Shows how to initialize a team with storage and run queries
- **individual_agent_storage_example.py**: Shows how to create individual agents with storage
- **resume_team_with_storage.py**: Demonstrates how to resume a previously saved team session
- **session_cleanup_example.py**: Shows how to manage and clean up stored sessions
- **session_metadata_example.py**: Demonstrates tracking and updating session metadata

### How External State Persistence Works

When you provide storage configuration to agents or teams, the Agno framework automatically handles external state persistence between API calls. Here's how it works:

1. **Initialization**: 
   ```python
   storage = initialize_storage(
       storage_type="sqlite",
       storage_connection="examples/data/agent_sessions.db",
       session_id="unique_session_id",
       user_id="user_123"
   )
   
   # The agent/team will use this storage for persistence
   team = initialize_financial_modeling_team(
       api_key=api_key,
       storage=storage,  # or storage parameters directly
       session_id="unique_session_id"
   )
   ```

2. **Automatic Persistence**:
   - Each time the agent or team processes a query, its state is automatically saved to storage
   - This includes conversation history, tool results, and internal state
   - No explicit save/load calls are needed - Agno handles this internally

3. **Resuming Sessions**:
   - To resume a session, initialize the agent/team with the same session_id and storage configuration
   - Agno will automatically load the previous state from storage
   - Conversations can continue with full context from previous interactions

4. **Storage Backends**:
   The system supports multiple storage backends:
   - SQLite: Simple file-based storage suitable for development
   - PostgreSQL: Robust relational database for production use
   - MongoDB: Document-based storage with flexible schemas
   - DynamoDB: AWS-managed NoSQL database for scalable deployments
   - JSON/YAML: Simple file-based storage options

For more information on Agno's storage capabilities, see the [Agno storage documentation](https://docs.agno.com/storage/introduction).

## Knowledge Base Examples

[Add content about knowledge base examples here]

## Other Examples

[Add content about other examples here]

## Memory Capabilities

The Fama AI system uses Agno's built-in memory systems rather than implementing custom memory functionality. This approach ensures compatibility with Agno's agent architecture while providing robust memory capabilities:

### Memory Examples

These examples demonstrate how to use Agno's memory features within our system:

- `chat_history_memory.py`: Demonstrates basic chat history memory, including message formatting and serialization.
- `advanced_memory_example.py`: Shows all advanced memory capabilities:
  - Chat history persistence
  - User-specific memory extraction
  - Conversation summarization
  - Memory pruning for long conversations
  - Session resumption with memory continuity

### Memory Integration

Our implementation integrates Agno's memory capabilities by:

1. Exposing memory configuration parameters in the API's `TaskRequest` model
2. Properly configuring agent memory when initializing agents
3. Using storage adapters to persist memory across sessions
4. Leveraging Agno's built-in memory creation and management

### Key Memory Features

- **Chat History**: Messages between user and assistant, maintained across sessions
- **User Memories**: Personal information and preferences extracted from conversations
- **Summaries**: Condensed conversation context for handling long interactions
- **Memory Access**: Built-in tools allowing agents to access and reference past exchanges
- **Persistence**: Memory is stored and retrieved using configurable storage backends

To use memory capabilities in the API:

```python
response = requests.post("http://localhost:8000/task/submit", json={
    "message": "Continue our conversation about my retirement investments",
    "provider": "openai",
    "model_id": "gpt-4o",
    "provider_api_key": "your-api-key",
    "storage_type": "sqlite",  # Enable storage
    "storage_connection": "sqlite:///sessions.db",
    "session_id": "user123-session456",  # For session continuity
    "user_id": "user123",  # For user-specific memories
    "enable_chat_history": True,  # Enable chat history memory
    "enable_user_memories": True,  # Enable user-specific memories extraction
    "enable_summaries": True  # Enable conversation summarization
})
```

## MCP Examples

These examples demonstrate how to use Model Context Protocol (MCP) with the Financial Modeling API:

### mcp_filesystem_example.py

Shows how to use filesystem MCP to allow the AI to access local financial data files:
- Creates sample CSV, JSON, and Markdown files with financial data
- Demonstrates configuring filesystem MCP in API requests
- Shows how the AI can read and analyze local files

### mcp_multiple_servers_example.py

Demonstrates using multiple MCP servers simultaneously:
- Configures both filesystem access and custom MCP servers
- Shows how to set up server-specific environment variables
- Demonstrates how the AI can leverage multiple tools through MCP

### mcp_error_handling_example.py

Tests how the API handles MCP server failures and errors:
- Verifies graceful handling of non-existent filesystem directories
- Tests behavior with invalid MCP server commands
- Checks handling of multiple failing servers
- Validates error handling for problematic environment variables
- Provides a summary of API robustness against MCP failures

### mcp_patterns_example.py

Demonstrates recommended patterns and best practices for using MCP:
- Shows 5 common MCP usage patterns with complete examples
- Covers read-only filesystem access for data analysis 
- Demonstrates combining multiple specialized MCP servers
- Provides secure configuration examples for production environments
- Shows streaming with MCP for long-running analyses
- Illustrates combining MCP with knowledge bases for enhanced context
- Includes a summary of best practices and security considerations

To run these examples:
```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key

# Run the examples
python mcp_filesystem_example.py
python mcp_multiple_servers_example.py
python mcp_error_handling_example.py
python mcp_patterns_example.py
``` 