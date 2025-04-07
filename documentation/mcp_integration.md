# Model Context Protocol (MCP) Integration

This document provides detailed information about the Model Context Protocol (MCP) integration in the Financial Modeling API, explaining how to use MCP servers with your financial modeling requests.

## What is MCP?

The Model Context Protocol (MCP) enables our AI agents to interact with external systems through a standardized interface. This allows agents to:

- Access file systems to read and process financial data files
- Connect to specialized tools and services
- Extend the capabilities of the AI beyond its built-in functionality

## MCP Parameters

When submitting a task to the `/task/submit` endpoint, you can include the following MCP-related parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| mcp_servers | array of objects | No | null | List of MCP servers to connect to |
| use_filesystem_mcp | boolean | No | false | Enable filesystem MCP for local file access |
| filesystem_root_path | string | No | current directory | Root path for filesystem MCP |

### MCP Server Configuration Object

Each object in the `mcp_servers` array can contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| command | string | Yes | Command to run the MCP server |
| args | array of strings | No | Arguments to pass to the command |
| env | object | No | Environment variables to pass to the server |

## Usage Examples

### Basic Filesystem Access

This example enables filesystem access to read financial data from a local directory:

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Create a financial model using data from the financial_data directory",
  "provider_api_key": "your-api-key",
  "use_filesystem_mcp": true,
  "filesystem_root_path": "/path/to/financial_data"
}
```

### Custom MCP Server

This example connects to a custom MCP server that provides specialized financial analysis tools:

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Create a financial model for a rental property using the financial analysis tools",
  "provider_api_key": "your-api-key",
  "mcp_servers": [
    {
      "command": "npx",
      "args": ["-y", "@financialtools/mcp-server"],
      "env": {
        "API_KEY": "your-financial-tools-api-key",
        "ANALYSIS_MODE": "detailed"
      }
    }
  ]
}
```

### Multiple MCP Servers

You can connect to multiple MCP servers simultaneously:

```json
{
  "model_id": "gpt-4o",
  "model_provider": "openai",
  "task": "Create a comprehensive financial model using all available tools",
  "provider_api_key": "your-api-key",
  "use_filesystem_mcp": true,
  "filesystem_root_path": "/path/to/data",
  "mcp_servers": [
    {
      "command": "npx",
      "args": ["-y", "@financialtools/mcp-server"]
    },
    {
      "command": "npx -y @marketdata/mcp-server"
    }
  ]
}
```

## How MCP Works in the API

1. When you include MCP configuration in your request, the API initializes the specified MCP servers
2. The servers are connected to the AI agents as tools they can use during the analysis
3. The team is configured with access to these tools, and special instructions are added
4. When the analysis is complete, the MCP resources are properly cleaned up

## Features and Capabilities

### Filesystem MCP

When `use_filesystem_mcp` is enabled, the agents can:

- List files and directories
- Read file contents
- Check file metadata
- Process data files directly (CSV, Excel, JSON, etc.)

This is particularly useful for financial modeling tasks that require analyzing data from files.

### Custom MCP Servers

Custom MCP servers can provide specialized tools for:

- Market data retrieval
- Financial calculations and analysis
- Visualization generation
- Database access
- API integrations

## Best Practices

1. **Security**: Be cautious about which directories you expose through filesystem MCP. Only provide access to directories containing data relevant to the task.

2. **Resource Management**: The API automatically manages MCP resources, ensuring servers are properly started and terminated.

3. **Error Handling**: If an MCP server fails to initialize, the API will log the error but continue without that server's functionality.

4. **Permissions**: When using custom MCP servers, ensure they have the necessary permissions to access required resources.

5. **Data Privacy**: Be mindful of the data you make available through MCP servers, especially when processing sensitive financial information.

## Limitations

- MCP servers run on the server side, so they need to be available and accessible to the API
- Large file operations might impact performance
- Some specialized MCP servers may require additional setup or credentials

## Troubleshooting

If you encounter issues with MCP integration:

1. Check that any required NPM packages for your MCP servers are installed on the system
2. Verify that paths in `filesystem_root_path` are accessible to the API service
3. Ensure commands in `mcp_servers` are executable on the system
4. Review the API logs for specific error messages related to MCP initialization

For more detailed assistance, contact the API administrators with the request ID where the MCP issue occurred. 