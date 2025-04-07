# Financial Modeling API Reference

This document provides detailed information about the Financial Modeling API endpoints, request parameters, and response formats.

## Base URL

```
http://localhost:8000
```

## Authentication

All API requests require provider-specific API keys (OpenAI, Anthropic, or Formation) to be included in the request.

## Endpoints

### Health Check

#### `GET /`

Returns basic information about the API including its status and supported features.

**Response Example:**

```json
{
  "status": "ok", 
  "message": "Financial Modeling API is running",
  "supported_providers": ["openai", "anthropic", "formation"],
  "api_version": "1.0.0",
  "features": {
    "knowledge_base": "Supported - allows integration with external knowledge sources via URLs or text",
    "vector_databases": ["lancedb", "tantivy"],
    "embedding_providers": ["openai", "anthropic", "cohere", "local"]
  }
}
```

#### `GET /health`

Returns detailed health information about the API and model providers.

**Response Example:**

```json
{
  "status": "healthy",
  "api": "operational",
  "timestamp": "2023-04-05T20:47:00.123456",
  "providers": {
    "openai": "requires_api_key",
    "anthropic": "requires_api_key",
    "formation": "requires_api_key"
  },
  "message": "Use the /task/check-api-key endpoint to verify specific provider API keys"
}
```

### Task Submission

#### `POST /task/submit`

Submits a financial modeling task for processing by the agent team.

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| message | string | Yes | - | The natural language description of the financial modeling task |
| stream | boolean | No | true | Whether to stream the response or return it all at once |
| provider | string | No | "openai" | The model provider to use (openai, anthropic, formation) |
| model | string | No | "gpt-4o" | The specific model to use |
| provider_api_key | string | Yes | - | API key for the specified provider |
| verbose_logging | boolean | No | false | Enable detailed logging of the entire process |

**Knowledge Base Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| knowledge_urls | array of strings | No | null | List of URLs to documents that will be used as knowledge sources |
| knowledge_text | string | No | null | Raw text content to use as a knowledge source |
| vector_db_type | string | No | "lancedb" | Type of vector database to use (lancedb, tantivy) |
| embedder_provider | string | No | "openai" | Provider for embedding models (openai, anthropic, cohere, local) |
| embedder_model | string | No | "text-embedding-3-small" | Specific embedding model to use (varies by provider) |

**MCP Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| mcp_servers | array of objects | No | null | List of MCP servers to connect to. Each object contains `command`, `args` (optional), and `env` (optional) |
| use_filesystem_mcp | boolean | No | false | Enable filesystem MCP for local file access |
| filesystem_root_path | string | No | current directory | Root path for filesystem MCP |

**Request Example:**

```json
{
  "message": "Create a financial model for a rental property investment",
  "provider": "openai",
  "model": "gpt-4o",
  "provider_api_key": "your-api-key",
  "knowledge_urls": ["https://example.com/rental-rates-2023.pdf"],
  "knowledge_text": "2023 rental yield averages: Manhattan 3.2%, Brooklyn 4.1%, Queens 4.5%",
  "vector_db_type": "lancedb",
  "embedder_provider": "openai", 
  "embedder_model": "text-embedding-3-small",
  "use_filesystem_mcp": true,
  "filesystem_root_path": "/path/to/financial_data",
  "mcp_servers": [
    {
      "command": "npx",
      "args": ["-y", "@financialtools/mcp-server"],
      "env": {
        "API_KEY": "your-financial-tools-api-key"
      }
    }
  ]
}
```

**Response:**

If `stream` is `true`, the response will be a streaming response with text chunks delivered as they are generated.

If `stream` is `false`, the response will be the complete generated financial analysis.

### API Key Validation

#### `POST /task/check-api-key`

Checks if a provider API key is valid.

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| provider | string | Yes | Provider to check the API key for |
| api_key | string | Yes | The API key to validate |

**Response Example (valid key):**

```json
{
  "status": "valid",
  "provider": "openai"
}
```

**Response Example (invalid key):**

```json
{
  "status": "invalid",
  "provider": "openai",
  "error": "Invalid authentication token."
}
```

### Log Retrieval

#### `GET /task/logs/{request_id}`

Retrieves logs for a specific request ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| request_id | string | Yes | The ID of the request to retrieve logs for |

**Response Example:**

```json
{
  "request_id": "openai_20230405_204700",
  "logs": [
    "2023-04-05 20:47:00 - Starting new task request ID: openai_20230405_204700",
    "2023-04-05 20:47:01 - Creating agents with provider: openai, model: gpt-4o",
    "2023-04-05 20:47:02 - Team created with 4 members",
    "2023-04-05 20:47:03 - Starting streaming response"
  ]
}
```

## Validation Rules

### Knowledge Parameters Validation

The API performs the following validations on knowledge-related parameters:

**knowledge_urls:**
- If provided, cannot be an empty list
- Each URL must start with "http://" or "https://"
- Each URL must be at least 10 characters long

**knowledge_text:**
- If provided, cannot be empty or just whitespace

**vector_db_type:**
- Must be one of: "lancedb" or "tantivy"
- Values are normalized to lowercase

**embedder_provider:**
- Must be one of: "openai", "anthropic", "cohere", or "local"
- Values are normalized to lowercase

**embedder_model:**
- For OpenAI: must be one of "text-embedding-3-small", "text-embedding-3-large", or "text-embedding-ada-002"
- For Anthropic: must start with "claude-"
- For Cohere: must be one of "embed-english-v3.0" or "embed-multilingual-v3.0"

## Error Handling

The API returns standard HTTP status codes to indicate success or failure:

- 200 OK: Request successful
- 400 Bad Request: Invalid request parameters
- 401 Unauthorized: Invalid API key
- 404 Not Found: Resource not found
- 500 Internal Server Error: Server-side error

Error responses include a JSON object with an error message:

```json
{
  "error": "Detailed error message"
}
```

## Rate Limiting

The API is currently not rate-limited, but excessive usage may be throttled in the future. 