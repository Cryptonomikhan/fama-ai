# Financial Modeling API Quick Start Guide

This guide will help you get started with the Financial Modeling API, which uses AI agent teams to generate comprehensive financial models for investment opportunities.

## Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/fama-ai.git
   cd fama-ai
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` to include:
   ```
   OPENAI_API_KEY=your_openai_api_key
   API_KEY=your_api_key_for_authentication
   ```

## Start the API Server

```bash
python -m src.api.main
```

The server will start on http://localhost:8000

## Using the API

### Basic Example with cURL

```bash
curl -X POST http://localhost:8000/api/model \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_api_key" \
  -d '{
    "description": "A tokenized real estate fund that invests in multifamily properties in emerging tech hubs across the U.S. The fund targets properties that can be renovated to increase NOI by 15-20%. Initial capital raise is $10M with a target IRR of 18-22% over a 5-year hold period.",
    "openai_api_key": "your_openai_api_key"
  }'
```

### Example with Python

```python
import requests
import json

url = "http://localhost:8000/api/model"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "your_api_key"
}
payload = {
    "description": "A tokenized real estate fund that invests in multifamily properties in emerging tech hubs across the U.S. The fund targets properties that can be renovated to increase NOI by 15-20%. Initial capital raise is $10M with a target IRR of 18-22% over a 5-year hold period.",
    "openai_api_key": "your_openai_api_key",
    "model_id": "gpt-4o",
    "temperature": 0.1
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(json.dumps(result, indent=2))
```

## Using the Agent Team Directly

For more control, you can use the agent team directly in your code without going through the API:

```python
from src.agents.init_agents import initialize_financial_modeling_team
import os

# Initialize the agent team
agent_team = initialize_financial_modeling_team(
    api_key=os.environ["OPENAI_API_KEY"],
    model_id="gpt-4o",
    temperature=0.1
)

# Define your investment
investment_description = """
A tokenized real estate fund that invests in multifamily properties
in emerging tech hubs across the U.S. The fund targets properties that
can be renovated to increase NOI by 15-20%. Initial capital raise is
$10M with a target IRR of 18-22% over a 5-year hold period.
"""

# Run the search agent
searcher = agent_team["searcher"]
search_prompt = f"Gather information for {investment_description}"
search_results = searcher.agent.run(search_prompt).content

# Run the assumption generator
assumption_generator = agent_team["assumption_generator"]
assumptions = assumption_generator.agent.run(
    f"Build assumptions for {investment_description}",
    data=search_results
).content

# Run the metrics deriver
metrics_deriver = agent_team["metrics_deriver"]
metrics = metrics_deriver.agent.run(
    f"Derive metrics for {investment_description}",
    searcher_data=search_results,
    assumption_data=assumptions
).content

# Run the financial modeler
financial_modeler = agent_team["financial_modeler"]
financial_model = financial_modeler.agent.run(
    f"Build a model for {investment_description}",
    searcher_data=search_results,
    assumption_data=assumptions,
    metrics_data=metrics
).content

print(financial_model)
```

## Run the Example Script

We've included an example script that demonstrates how to use the agent team:

```bash
python examples/team_example.py
```

This script shows both the sequential approach (running each agent in order) and the team approach (letting the team coordinate).

## Advanced Features

The API supports several advanced features:

```python
payload = {
    "description": "Your investment description",
    "openai_api_key": "your_openai_api_key",
    "model_id": "gpt-4o",
    "temperature": 0.1,
    "use_knowledge": True,  # Use knowledge base
    "use_memory": True,     # Use memory for storing interactions
    "use_history": True,    # Track history
    "use_storage": True,    # Persist data
    "mcp_server_url": "http://your-mcp-server.com"  # For distributed processing
}
```

## Customizing the Financial Model

To customize the financial model, you can adjust the prompts sent to each agent. For example:

```python
# For more detailed income statements
model_prompt = """
Based on the provided data, build a financial model with:
1. Detailed monthly income statements for year 1
2. Quarterly statements for years 2-5
3. Bull, bear, and baseline scenarios
4. Sensitivity analysis for key variables
"""

model_response = financial_modeler.agent.run(
    model_prompt,
    searcher_data=search_results,
    assumption_data=assumptions,
    metrics_data=metrics
)
```

## Advanced Usage: Memory Systems

The API supports persistent memory systems that allow conversations to continue across multiple API calls:

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Continue our analysis of the rental property investment",
  "provider_api_key": "your-api-key",
  "storage_type": "sqlite",
  "storage_connection": "financial_models.db",
  "session_id": "session-123",
  "user_id": "user-456",
  "enable_chat_history": true,
  "enable_user_memories": true,
  "memory_depth": 10
}
```

## Advanced Usage: MCP Integration

The API supports Model Context Protocol (MCP) integration to access file systems and external tools:

### Filesystem Access

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Analyze the financial data in the Excel file and create a financial model",
  "provider_api_key": "your-api-key",
  "use_filesystem_mcp": true,
  "filesystem_root_path": "/path/to/financial_data"
}
```

### Custom MCP Tools

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Create a financial model with advanced market data",
  "provider_api_key": "your-api-key",
  "mcp_servers": [
    {
      "command": "npx",
      "args": ["-y", "@financialtools/mcp-server"]
    }
  ]
}
```

For detailed documentation on MCP integration, refer to the `documentation/mcp_integration.md` file.

## Next Steps

- Check the API documentation in `src/api/README.md` for more details
- Explore the example scripts in the `examples/` directory
- Customize agent instructions in `src/agents/init_agents.py` 