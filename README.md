# Fama AI Financial Modeling Platform

A sophisticated financial modeling platform built with the Agno framework, providing powerful analysis tools for business research, financial modeling, and visualization.

## Features

- **Multi-Provider LLM Support**: Use any model provider supported by Agno (Formation, OpenAI, Anthropic, Groq, etc.)
- **Formation First**: Built with Formation as the default provider for intelligent model routing
- **Comprehensive Financial Analysis**: Deep market research, KPI analysis, and financial modeling
- **Interactive Visualizations**: Beautiful, data-rich dashboards and charts
- **Plaid Integration**: Connect to real financial data through Plaid API
- **White-Label Ready**: Customize the look and feel for your brand

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fama-ai.git
   cd fama-ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to add your API keys and customize settings.

4. Run the application:
   ```bash
   uvicorn src.api.main:app --reload
   ```

## Model Provider Configuration

Fama-AI supports multiple LLM providers through the Agno framework. By default, it uses Formation for intelligent model routing, but you can easily switch to other providers.

### Supported Providers

- **Formation** - `formation` (Default)
  - Models: `best-quality`, `best-reasoning`, `best-speed`, `best-rag`
  - Set `FORMATION_API_KEY` in your environment variables

- **OpenAI** - `openai`
  - Models: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
  - Set `OPENAI_API_KEY` in your environment variables

- **Anthropic** - `anthropic`
  - Models: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
  - Set `ANTHROPIC_API_KEY` in your environment variables

- **Groq** - `groq`
  - Models: `llama3-70b-8192`, `llama3-8b-8192`, `mixtral-8x7b-32768`
  - Set `GROQ_API_KEY` in your environment variables

- And many more, including Gemini, Mistral, Together, Cohere, AWS Bedrock, Azure, Ollama, and LiteLLM.

### Setting the Provider

You can set the model provider in three ways:

1. **Environment Variables** - Set `LLM_PROVIDER` and `LLM_MODEL_ID` in your `.env` file
2. **API Request** - Include model configuration in your API request
3. **Direct Code** - Pass provider and model ID when initializing agents

## API Usage

### Model Configuration

```python
# In your API request:
{
  "context": { ... },
  "model_config": {
    "provider": "anthropic",
    "model_id": "claude-3-opus"
  }
}
```

### Available Models Endpoint

```bash
GET /api/models
```

Returns information about all available model providers and models.

## Development

### Project Structure

```
fama-ai/
├── src/
│   ├── api/             # FastAPI application
│   │   ├── agents/      # Specialized AI agents
│   │   └── integrations/ # External API integrations 
│   ├── models/          # LLM model implementations
│   ├── tools/           # AI agent tools
│   ├── utils/           # Utilities for the application
│   └── views/           # Data visualization components
├── .env.example         # Example environment variables
└── requirements.txt     # Project dependencies
```

## License

MIT 