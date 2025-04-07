# Financial Modeling API

This API provides financial modeling capabilities using a coordinated team of specialized AI agents to generate comprehensive financial analyses and models.

## Features

- 🧠 **Multi-Agent System**: Coordinated team of specialized financial agents
- 🔍 **Knowledge Base Integration**: Connect custom knowledge sources to enhance analysis
- 💾 **External Storage**: Support for multiple storage backends (SQLite, PostgreSQL, etc.)
- 🛠️ **Tool Integration**: Web search, calculators, and custom tools for financial analysis
- 🧩 **Memory Systems**: Chat history, user-specific memories, and summarization
- 📂 **MCP Integration**: Access file systems and external tools via Model Context Protocol
- 🔄 **Stateless API**: Fully serverless design for easy scaling
- 🤖 **Multi-Provider Support**: Compatible with OpenAI, Anthropic, and Formation models
- 📊 **Streaming Responses**: Get results in real-time as they're generated
- 💰 **Detailed Financial Models**: Comprehensive reports with assumptions, calculations, and projections

## Knowledge Base Integration

The API now supports integration with external knowledge sources:

- Provide URLs to documents as knowledge sources
- Include raw text as knowledge input
- Configure vector database type (lancedb or tantivy)
- Select embedding providers (OpenAI, Anthropic, Cohere, or local)
- Choose specific embedding models based on provider

This functionality allows the financial models to incorporate domain-specific knowledge, market data, and proprietary information.

## MCP Integration Examples

The `examples/` directory contains scripts demonstrating MCP (Model Context Protocol) integration with the Financial Modeling API:

- **mcp_filesystem_example.py**: Shows how to use filesystem MCP to enable the AI to access local financial data files
- **mcp_multiple_servers_example.py**: Demonstrates connecting to multiple MCP servers simultaneously, including filesystem access and custom MCP servers

These examples show how to:
```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key

# Run the filesystem MCP example
python examples/mcp_filesystem_example.py

# Run the multiple MCP servers example
python examples/mcp_multiple_servers_example.py
```

## Containerization & Deployment

The Fama API can be easily deployed using Docker:

```bash
# Deploy API only (recommended for production)
docker compose up -d

# Or with development database (for testing)
docker compose --profile dev up -d

# Or use the deployment script
./scripts/deploy.sh       # API only
./scripts/deploy.sh --with-db  # With PostgreSQL
```

The containerized API is completely stateless - all configuration including API keys, storage connection strings, and other settings are provided by callers in their API requests. This makes the deployment simple and secure.

For detailed deployment instructions, see [documentation/deployment.md](documentation/deployment.md).

## Getting Started

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt`
3. Set up your environment variables (see `.env.example`)
4. Run the server with `python -m src.api.main`

## API Documentation

Complete API documentation is available in:
- OpenAPI specification: `openapi.yaml`
- API Reference: `documentation/api_reference.md`
- Quick examples: `QUICKSTART.md`

## Example Usage

```bash
curl -X POST http://localhost:8000/task/submit \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a financial model for a rental property investment",
    "provider": "openai",
    "model": "gpt-4o",
    "provider_api_key": "your-api-key",
    "knowledge_urls": ["https://example.com/rental-rates-2023.pdf"],
    "knowledge_text": "2023 rental yield averages: Manhattan 3.2%, Brooklyn 4.1%, Queens 4.5%",
    "vector_db_type": "lancedb",
    "embedder_provider": "openai",
    "embedder_model": "text-embedding-3-small"
  }'
```

## License

[MIT License](LICENSE)
