# Financial Modeling API

The Financial Modeling API provides endpoints for generating detailed financial models from natural language descriptions of investment opportunities. The API uses specialized AI agents to gather information, generate assumptions, derive metrics, and build comprehensive financial models.

## API Structure

The API follows the Agno pattern with the following structure:

```
src/api/
├── main.py              # FastAPI application entry point
├── settings.py          # API configuration settings
├── models/              # Pydantic models for requests/responses
│   ├── __init__.py
│   └── model_request.py # Models for financial modeling requests/responses
├── routes/              # API routes
│   ├── __init__.py
│   ├── v1_router.py     # Main v1 router that includes sub-routers
│   ├── health.py        # Health check endpoints
│   └── modeling.py      # Financial modeling endpoints
```

## Endpoints

### POST /api/v1/model

Generates a financial model based on a description of an investment opportunity.

#### Request Body

```json
{
  "description": "A 50-unit apartment building in downtown Austin with a purchase price of $10M",
  "provider": "formation",
  "api_key": "your-provider-api-key",
  "model_id": "llama-3-sonar-large-32k-online",
  "stream": true,
  "temperature": 0.1,
  "timeout": 300,
  "knowledge_urls": [
    "https://example.com/market-report.pdf"
  ],
  
  "storage_type": "sqlite",
  "storage_connection": "database/sessions.db",
  "session_id": "user123-session456",
  "user_id": "user123",
  
  "tools": [
    "web_search",
    {
      "tool_name": "calculator",
      "tool_args": {"precision": 4},
      "enabled": true
    }
  ],
  "web_search_enabled": true,
  "data_analysis_enabled": true,
  "calculator_enabled": true,
  
  "memory_window_size": 10,
  "summarize_memory": true,
  "memory_type": "buffer",
  
  "mcp_server_url": "https://mcp.example.com"
}
```

#### Request Parameters

| Parameter | Type | Description | Required | Default |
| --- | --- | --- | --- | --- |
| description | string | Description of the investment opportunity | Yes | - |
| provider | string | Model provider (formation, openai, anthropic, openrouter) | No | formation |
| api_key | string | API key for the selected provider | No | - |
| model_id | string | Model ID to use (provider-specific) | No | - |
| stream | boolean | Whether to stream the response | No | true |
| temperature | number | Temperature for generation | No | 0.1 |
| timeout | number | Timeout for the request in seconds | No | 300 |
| knowledge_urls | array | List of URLs to use as knowledge sources | No | - |

| storage_type | string | Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml) | No | - |
| storage_connection | string | Connection string or path for the storage | No | - |
| session_id | string | Session ID for persistent sessions | No | - |
| user_id | string | User ID for multi-user systems | No | - |

| tools | array | List of tools to use (strings or objects with tool_name, tool_args, enabled) | No | - |
| web_search_enabled | boolean | Whether web search capability is enabled | No | false |
| data_analysis_enabled | boolean | Whether data analysis capability is enabled | No | false |
| calculator_enabled | boolean | Whether calculator capability is enabled | No | true |

| memory_window_size | number | Number of messages to keep in memory window | No | - |
| summarize_memory | boolean | Whether to summarize long conversations | No | false |
| memory_type | string | Type of memory to use (default, buffer, summary, window, none) | No | default |

| mcp_server_url | string | URL for MCP server | No | - |

#### Response (Non-Streaming)

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "search_results": "...",
  "assumptions": { ... },
  "metrics": [ ... ],
  "financial_model": { ... }
}
```

#### Response (Streaming)

The streaming response is delivered as Server-Sent Events (SSE) with the following event types:

```
data: {"event":"start","request_id":"550e8400-e29b-41d4-a716-446655440000","message":"Starting financial modeling process"}

data: {"event":"progress","request_id":"550e8400-e29b-41d4-a716-446655440000","agent":"searcher","message":"Running search agent","progress":10}

data: {"event":"progress","request_id":"550e8400-e29b-41d4-a716-446655440000","agent":"searcher","message":"Search completed","data":{"search_results":"..."},"progress":30}

data: {"event":"complete","request_id":"550e8400-e29b-41d4-a716-446655440000","message":"Financial modeling complete","data":{...},"progress":100}
```

### POST /api/v1/model/upload

Uploads files to use as knowledge sources for the financial modeling process.

#### Request

- Multipart form with file field

#### Response

```json
{
  "filename": "market-report.pdf",
  "path": "uploads/market-report.pdf",
  "status": "success"
}
```

### GET /api/v1/health

Health check endpoint to verify the API is operational.

#### Response

```json
{
  "status": "ok"
}
```

## Authentication

All endpoints except `/api/v1/health` require authentication with an API key.

The API key should be provided in the `x-api-key` header.

## Streaming Client Example

For JavaScript clients, you can consume the streaming API like this:

```javascript
async function streamFinancialModel(description) {
  const response = await fetch('https://api.example.com/api/v1/model', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': 'your-api-key'
    },
    body: JSON.stringify({
      description: description,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const events = chunk.split('\n\n').filter(event => event.startsWith('data: '));
    
    for (const event of events) {
      const json = JSON.parse(event.replace('data: ', ''));
      
      switch (json.event) {
        case 'start':
          console.log('Started processing:', json.message);
          break;
        case 'progress':
          console.log(`${json.agent}: ${json.message} (${json.progress}%)`);
          break;
        case 'complete':
          console.log('Completed:', json.message);
          console.log('Result:', json.data);
          break;
        case 'error':
          console.error('Error:', json.error);
          break;
      }
    }
  }
}
```

## Advanced Features

### MCP Server Support

The API supports distributed processing via MCP (Multi-Context Processing) servers. Provide the `mcp_server_url` parameter to enable this feature.

### Knowledge Base Integration

The API can use both uploaded files and URLs as knowledge sources for enriching the financial models. Provide the `knowledge_urls` parameter or upload files using the `/api/v1/model/upload` endpoint.

### Memory Integration

The API supports persistent memory for agents to recall previous interactions and data. Configure memory using the following parameters:

- `memory_type`: Type of memory to use (default, buffer, summary, window, none)
- `memory_window_size`: Number of messages to keep in memory window
- `summarize_memory`: Whether to summarize long conversations

### Tools Integration

The API supports various tools that agents can use to perform tasks. Configure tools using the following parameters:

- `tools`: List of specific tools to enable, which can be simple strings or detailed configurations
- `web_search_enabled`: Whether web search capability is enabled
- `data_analysis_enabled`: Whether data analysis capability is enabled
- `calculator_enabled`: Whether calculator capability is enabled

Supported tools include:
- `web_search`: Search the web for information
- `calculator`: Perform calculations
- `data_analysis`: Analyze datasets and create charts
- `financial_data`: Access financial data and metrics
- `code_interpreter`: Run code snippets
- `json_explorer`: Explore and manipulate JSON data
- `file_browser`: Browse and read files
- `url_fetcher`: Fetch content from URLs

### Storage Integration

The API supports persistent storage for agent state, enabling session continuity across API calls. Configure storage using the following parameters:

- `storage_type`: Type of storage backend (sqlite, postgres, mongodb, dynamodb, json, yaml)
- `storage_connection`: Connection string or path for the storage
- `session_id`: Session ID for persistent sessions
- `user_id`: User ID for multi-user systems

### History Tracking

The API can track conversation history across multiple sessions using the storage functionality.

## Error Handling

The API returns standard HTTP status codes:

- 200: Successful request
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 429: Too many requests (rate limit exceeded)
- 500: Internal server error

Error responses include a `detail` field with a description of the error. 