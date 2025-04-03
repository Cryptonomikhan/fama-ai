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
├── reports/                # Report generation
│   ├── __init__.py
│   ├── report_generator.py # Report generation in multiple formats
├── tools/                  # Custom tools for agents
│   ├── __init__.py
│   ├── report_tools.py     # Report generation tools for agents
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
│   ├── report_example.py   # Example of using the Report Generation functionality
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
Orchestrates the workflow between specialized agents, ensuring that outputs from one agent feed properly into the inputs of the next. The coordinator manages the overall process and assembles the final output. It also integrates report generation tools to produce professional reports in various formats.

## Report Generation

The Fama AI platform includes a comprehensive report generation system that produces well-formatted reports in multiple formats:

### Report Formats
- **JSON**: Machine-readable format for API integrations and programmatic access
- **CSV**: Tabular format for financial data that can be imported into spreadsheet software
- **PDF**: Professional-quality document format with tables, charts, and formatted text

### Report Contents
- Executive summary
- Research findings
- Financial models (income statement, cash flow)
- Financial metrics (IRR, NPV, ROI)
- Scenario analysis (baseline, bull, bear)
- Validation results
- Assumption documentation

### Report Generation Methods
- **Direct**: Generate reports directly using the `generate_report` function
- **Tool-based**: Agents can generate reports using the provided report generation tools
- **Team-integrated**: Report generation is integrated into the agent coordination workflow

## Implementation Status

- [x] Research Agent
- [x] Modeling Agent
- [x] Scenario Planner Agent
- [x] Assumption Generator Agent
- [x] Validator Agent
- [x] Agent Coordinator
- [x] API Server
- [x] Logging System
- [x] Report Generation
- [x] Dashboard Builder Agent

## Future Development

### Enhanced Dashboard Builder Features

The Dashboard Builder Agent now creates interactive Next.js dashboards from financial modeling results. Future enhancements include:

- Template Library: Predefined dashboard templates for common investment types
- Interactive Elements: User input components for scenario modification
- Data Export: Export functionality for dashboard data
- Theme Customization: Custom theming options beyond light/dark
- Collaboration Features: Multi-user editing capabilities

**Planned Implementation Timeline:** Q4 2023

## Optimized Agent Workflow

The Fama AI platform implements an optimized workflow that follows a logical sequence:

```
Research → Assumption Generation → Modeling → Scenario Planning → Validation → Report Generation → (Optional) Dashboard Building
```

This sequence ensures that each step has the necessary inputs from previous steps:
- Research informs assumptions
- Assumptions drive financial models
- Financial models enable scenario planning
- Comprehensive validation ensures overall quality
- Validated results are compiled into professional reports
- Reports can be transformed into interactive dashboards (when requested)

For more details, see [the Agent Workflow documentation](documentation/agent_workflow.md).

## Installation and Setup

### Option 1: Local Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/fama-ai.git
cd fama-ai
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure environment variables:
```
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Run the application:
```
python -m api.main
```

### Option 2: Docker Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/fama-ai.git
cd fama-ai
```

2. Configure environment variables:
```
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Build and run with Docker Compose:
```
docker-compose up -d
```

## Usage

### API Endpoints

- `POST /api/submit`: Submit an investment vehicle for analysis
- `GET /api/logs/{request_id}`: Get logs and results for a specific request

### Example Scripts

The `examples/` directory contains scripts demonstrating how to use each component of the system:

- `coordinator_example.py`: Demonstrates the full workflow using the Agent Coordinator
- `research_example.py`: Shows how to use the Research Agent independently
- `modeling_example.py`: Shows how to use the Modeling Agent independently
- `scenario_planning_example.py`: Shows how to use the Scenario Planner Agent independently
- `assumption_generator_example.py`: Shows how to use the Assumption Generator Agent independently
- `validator_example.py`: Shows how to use the Validator Agent independently
- `report_example.py`: Shows how to use the Report Generation functionality independently

## License

This project is licensed under the MIT License - see the LICENSE file for details. 