# Fama AI: Agentic AI for Yield-Generating Investment Vehicle Modeling

An advanced financial modeling platform that uses specialized AI agents to create, analyze, and optimize yield-generating investment vehicle models.

## Project Overview

This application leverages agentic AI to automate the creation of sophisticated financial models for yield-generating investment vehicles such as real estate funds, tokenized assets, and structured products. By decomposing the complex task of financial modeling into specialized sub-tasks performed by purpose-built AI agents, the system produces comprehensive and flexible financial models.

## Project Structure

```
fama-ai/
├── agents/                 # Specialized AI agents
│   ├── __init__.py
│   ├── research.py         # Research Agent for market and domain research
│   ├── modeling.py         # Modeling Agent for financial model creation
│   ├── scenario_planner.py # Scenario Planner Agent for multiple scenario modeling
│   ├── assumption_generator.py # Assumption Generator Agent for model assumptions
│   ├── validator.py        # Validator Agent for model validation
│   ├── agent_coordinator.py # Coordinator for orchestrating agent workflows
├── api/                    # API server
│   ├── __init__.py
│   ├── main.py             # Main API endpoints and routing
├── models/                 # Model configuration and management
│   ├── __init__.py
│   ├── model_factory.py    # Factory for creating LLM instances
├── utils/                  # Utilities and helpers
│   ├── __init__.py
│   ├── logging.py          # Logging utilities
├── examples/               # Example scripts
│   ├── research_example.py # Example of using the Research Agent
│   ├── modeling_example.py # Example of using the Modeling Agent
│   ├── scenario_planning_example.py # Example of using the Scenario Planner Agent
│   ├── assumption_generator_example.py # Example of using the Assumption Generator Agent
│   ├── validator_example.py # Example of using the Validator Agent
│   ├── coordinator_example.py # Example of using the Agent Coordinator
├── tests/                  # Tests
│   ├── test_api.py         # API tests
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── openapi.yaml            # OpenAPI specification
├── README.md               # Project documentation
```

## Specialized Agents

### Research Agent
Responsible for gathering market data, competitor analysis, regulatory information, and historical performance data related to the investment vehicle. This agent synthesizes information from various sources to provide a comprehensive research report.

### Modeling Agent
Creates detailed financial models based on the research data. This includes building pro forma income statements, cash flow projections, and balance sheets. The agent calculates key financial metrics like IRR, NPV, ROI, and payback period.

### Scenario Planner Agent
Generates multiple financial projection scenarios (baseline, bull, bear) to account for different market conditions and risk factors. The agent conducts comparative analysis between scenarios and provides risk assessments and decision frameworks.

### Assumption Generator Agent
Generates and validates critical assumptions that drive the financial models. This includes revenue assumptions, operating expense assumptions, capital expenditure assumptions, market assumptions, and financial assumptions. The agent also identifies critical assumptions and areas of uncertainty.

### Validator Agent
Validates financial models for accuracy, consistency, and compliance with industry standards. The agent identifies issues categorized by severity (critical, major, minor), provides recommendations for improvement, and assesses risk areas. It also validates specific financial metrics and scenario analyses.

### Agent Coordinator
Orchestrates the workflow between specialized agents, ensuring that outputs from one agent feed properly into the inputs of the next. The coordinator manages the overall process and assembles the final output.

## Implementation Status

- [x] Research Agent
- [x] Modeling Agent
- [x] Scenario Planner Agent
- [x] Assumption Generator Agent
- [x] Validator Agent
- [x] Agent Coordinator
- [x] API Server
- [x] Logging System
- [ ] Report Generation

## Optimized Agent Workflow

The Fama AI platform implements an optimized workflow that follows a logical sequence:

```
Research → Assumption Generation → Modeling → Scenario Planning → Validation
```

This sequence ensures that each step has the necessary inputs from previous steps:
- Research informs assumptions
- Assumptions drive financial models
- Financial models enable scenario planning
- Comprehensive validation ensures overall quality

For more details, see [the Agent Workflow documentation](documentation/agent_workflow.md).

## Installation and Setup

### Option 1: Local Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/fama-ai.git
   cd fama-ai
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Copy the example environment file and add your API keys
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys for Formation, OpenAI, or Anthropic.

6. Run the API server
   ```bash
   uvicorn api.main:app --reload
   ```

7. Run the example scripts
   ```bash
   python examples/coordinator_example.py
   ```

### Option 2: Docker Deployment

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/fama-ai.git
   cd fama-ai
   ```

2. Copy the example environment file and add your API keys
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys for Formation, OpenAI, or Anthropic.

3. Build and run the Docker container
   ```bash
   docker-compose up --build
   ```

4. The API server will be available at `http://localhost:8000`

### Environment Variables

Create a `.env` file in the project root with the following variables:

- `FORMATION_API_KEY`: API key for Formation models
- `OPENAI_API_KEY`: API key for OpenAI models
- `ANTHROPIC_API_KEY`: API key for Anthropic models
- `API_KEY`: Authentication key for the Fama AI API
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MODEL_PROVIDER`: Default model provider (formation, openai, anthropic)
- `MODEL_ID`: Default model ID to use with the selected provider

## API Documentation

The Fama AI API follows RESTful principles and provides endpoints for submitting investment vehicle descriptions and retrieving results.

### API Endpoints

#### Submit Investment Vehicle Description

```
POST /api/submit
```

Request body:
```json
{
  "description": "Investment vehicle description (e.g., real estate fund, tokenized asset)",
  "time_horizon": 5,
  "risk_factors": "moderate",
  "output_format": "json",
  "research_context": "Additional context for research"
}
```

Response:
```json
{
  "request_id": "uuid-string",
  "status": "processing",
  "log_stream_url": "/api/logs/{request_id}"
}
```

#### Get Logs for Request

```
GET /api/logs/{request_id}
```

Response:
```json
{
  "request_id": "uuid-string",
  "status": "complete",
  "logs": [...],
  "results": {
    "research_results": {...},
    "assumptions": {...},
    "financial_model": {...},
    "metrics": {...},
    "scenarios": {...},
    "validation": {...}
  }
}
```

### OpenAPI Specification

The API is documented using the OpenAPI specification. You can access the full OpenAPI documentation at `/docs` when the server is running, or view the `openapi.yaml` file in the project root.

## Examples

### Research Agent

```python
from agents.research import ResearchAgent

research_agent = ResearchAgent(provider="formation")

# Research an investment vehicle
research_results = research_agent.research_investment_vehicle(
    description="A real estate fund that focuses on multifamily properties in growing metropolitan areas",
    time_horizon=5,
    additional_context="Focus on demographic trends and rental yield data"
)

# Get market conditions
market_conditions = research_agent.get_market_conditions()

# Get yield data for similar investments
yield_data = research_agent.get_yield_data(
    vehicle_type="real estate fund",
    time_period="last 5 years"
)
```

### Agent Coordinator

```python
from agents.agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator(provider="formation")

# Process an investment vehicle description
results = coordinator.process_investment_vehicle(
    description="A tokenized real estate portfolio with properties in major urban centers",
    time_horizon=5,
    risk_factors="moderate",
    output_format="json",
    research_context="Focus on tokenization regulations and liquidity concerns"
)
```

## Testing

To run the tests:

```bash
pytest
```

To test the API endpoints specifically:

```bash
python tests/test_api.py
```

## Deployment

### Docker

The application includes a Dockerfile and docker-compose.yml for easy deployment. To build and run the Docker container:

```bash
docker-compose up --build
```

### Serverless

For serverless deployment on AWS Lambda, Google Cloud Functions, or Azure Functions, follow these steps:

1. Create the necessary serverless configuration files (e.g., `serverless.yml` for AWS Lambda).

2. Deploy the application using the appropriate serverless framework CLI.

3. Update the API endpoint in your client applications to point to the deployed serverless function.

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited. 