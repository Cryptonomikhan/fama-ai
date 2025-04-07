# Fama-AI Extension Plan

## Overview

This document outlines the comprehensive plan for extending the Fama-AI financial modeling agent system with new capabilities including:

1. Knowledge base integration
2. External storage integration
3. Tools and memory integration
4. Inter-agent communication
5. MCP server integration
6. Containerization and deployment

## Implementation Progress

### Current Status (Updated on: July 2023)
- **Knowledge Base Integration**: 
  - ✅ All agent classes (SearchingAgent, AssumptionGeneratorAgent, MetricsDerivingAgent, FinancialModelingAgent) updated to support knowledge base
  - ✅ TaskRequest model updated with knowledge base parameters
  - ✅ Knowledge base factory implemented
  - ✅ API endpoint integration completed
    - ✅ Modified run_task endpoint to pass knowledge_base to all agents
    - ✅ Knowledge base initialization before agent creation
    - ✅ Knowledge base logging and usage tracking
    - ✅ Error handling for knowledge base integration failures
  - ✅ Knowledge query utilities integrated - Agno's built-in query mechanism handles this automatically
  - ✅ Knowledge retrieval logging implemented
  - ✅ Enhanced flexibility to handle missing dependencies
    - ✅ Robust error handling for missing packages
    - ✅ Graceful fallback when optional features are unavailable
    - ✅ Detailed logging to inform users about fallback behavior
  - ⏳ Full testing and validation pending

- **Tools and Memory Integration**:
  - ✅ TaskRequest model updated with tool and memory parameters
  - ✅ Tool configuration factory implemented
  - ✅ Memory systems integrated with agents
  - ✅ Custom tool registration support added
  - ✅ Memory persistence across sessions implemented
  - ✅ Tests created for tool configuration and memory persistence
  - ⏳ Additional testing for complex memory scenarios pending

- **MCP Integration**:
  - ✅ TaskRequest model updated with MCP server parameters
  - ✅ Integration with Agno's built-in MCPTools and MultiMCPTools
  - ✅ Support for filesystem MCP server
  - ✅ Support for multiple MCP servers
  - ✅ MCP tools integrated with team creation
  - ✅ Error handling and resource cleanup implemented
  - ✅ Comprehensive documentation created
  - ✅ Example scripts demonstrating MCP usage patterns implemented
  - ✅ Testing and validation completed

- **Containerization and Deployment**:
  - ✅ Comprehensive Dockerfile created
  - ✅ Docker Compose configuration implemented
  - ✅ Production environment configuration setup
  - ✅ Deployment documentation and guides created
  - ✅ Environment variable management implemented
  - ✅ Scaling strategies documented
  - ⏳ Docker build testing pending
  - ⏳ Production deployment validation pending

- **Next Steps**:
  - Complete Docker deployment testing and validation
  - Implement monitoring and metrics collection
  - Enhance scalability for cloud deployments
  - Consider adding automated CI/CD pipeline

## 1. Knowledge Base Integration

### Current State
- Agent system lacks explicit knowledge base integration
- Each agent has specific hardcoded instructions without dynamic knowledge

### Target Implementation
- Allow callers to provide custom knowledge sources to agents via API parameters
- Support multiple knowledge vector database integrations
- Enable dynamic loading of domain-specific knowledge

### Example Structure
```python
# All knowledge base parameters will be added directly to TaskRequest
# Keep the request structure flat for simplicity and ease of use
class TaskRequest(BaseModel):
    # Existing parameters
    message: str
    stream: bool = True
    provider: str = "openai"
    model: str = "gpt-4o"
    provider_api_key: str = Field(..., description="API key for the specified provider")
    
    # Knowledge base parameters
    knowledge_urls: Optional[List[str]] = Field(None, description="URLs to documents to use as knowledge sources")
    knowledge_text: Optional[str] = Field(None, description="Raw text to use as knowledge source")
    vector_db_type: str = Field("lancedb", description="Type of vector database to use (lancedb, pgvector, pinecone, etc.)")
    embedder_provider: str = Field("openai", description="Provider for embeddings")
    embedder_model: str = Field("text-embedding-3-small", description="Embedding model to use")
    # ...
```

### Tasks and Subtasks

#### 1.1 Update TaskRequest Model
- [x] 1.1.1 Add knowledge_urls parameter to TaskRequest
- [x] 1.1.2 Add knowledge_text parameter to TaskRequest
- [x] 1.1.3 Add vector_db_type parameter to TaskRequest
- [x] 1.1.4 Add embedder_provider and embedder_model parameters
- [x] 1.1.5 Add validation for knowledge parameters
- [x] 1.1.6 Update API documentation with new parameters

#### 1.2 Create Knowledge Base Factory
- [x] 1.2.1 Create `initialize_knowledge_base` function that uses parameters from TaskRequest
- [x] 1.2.2 Add support for different embedder providers
- [x] 1.2.3 Implement LanceDB integration
- [x] 1.2.4 Support different chunking strategies
- [x] 1.2.5 Add error handling and reporting
- [x] 1.2.6 Write tests

#### 1.3 Implement Knowledge Source Handling
- [x] 1.3.1 Create URL-based knowledge source loader
- [x] 1.3.2 Support PDF document extraction
- [x] 1.3.3 Support HTML document extraction
- [x] 1.3.4 Create text-based knowledge source loader
- [x] 1.3.5 Implement document chunking for effective indexing
- [x] 1.3.6 Add progress tracking for document processing

#### 1.4 Integrate Knowledge with Agents
- [x] 1.4.1 Modify SearchingAgent to use knowledge base
- [x] 1.4.2 Modify AssumptionGeneratorAgent to use knowledge base
- [x] 1.4.3 Modify MetricsDerivingAgent to use knowledge base
- [x] 1.4.4 Modify FinancialModelingAgent to use knowledge base
- [x] 1.4.5 Update agent creation in the API endpoint for all agent types
  - [x] 1.4.5.1 Modify run_task endpoint to pass knowledge_base to all agents
  - [x] 1.4.5.2 Ensure knowledge base initialization happens before agent creation
  - [x] 1.4.5.3 Add logging for knowledge base usage in the API endpoint
  - [x] 1.4.5.4 Add error handling for knowledge base integration failures
- [x] 1.4.6 Knowledge query utilities - Using Agno's built-in functionality
- [x] 1.4.7 Add knowledge retrieval logging

#### 1.5 Testing and Validation
- [x] 1.5.1 Create test cases for knowledge base initialization
- [x] 1.5.2 Test URL-based knowledge sources
- [x] 1.5.3 Test text-based knowledge sources
- [x] 1.5.4 Validate vector database integrations
- [x] 1.5.5 Test knowledge retrieval with each agent type
- [x] 1.5.6 Benchmark performance with different knowledge sources

## 2. External Storage Integration

### Current State
- System doesn't persist agent state or session information in external storage
- All agent interactions are stateless

### Target Implementation
- Allow callers to provide storage configuration for persistent agent state
- Support multiple storage backends (SQLite, PostgreSQL) via Agno's storage API
- Enable session resumption and context persistence

### Example Structure
```python
# All storage parameters will be added directly to TaskRequest
# Instead of a separate StorageRequest model
class TaskRequest(BaseModel):
    # Existing parameters...
    
    # Storage parameters
    storage_type: Optional[str] = Field(None, description="Storage type (sqlite, postgres)")
    storage_connection: Optional[str] = Field(None, description="Connection string for storage")
    session_id: Optional[str] = Field(None, description="Session ID for resuming conversations")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    # ...
```

### Tasks and Subtasks

#### 2.1 Update TaskRequest Model
- [x] 2.1.1 Add storage_type parameter to TaskRequest
- [x] 2.1.2 Add storage_connection parameter to TaskRequest
- [x] 2.1.3 Add session_id parameter to TaskRequest
- [x] 2.1.4 Add user_id parameter for personalization
- [x] 2.1.5 Add validation for storage parameters
- [x] 2.1.6 Update API documentation with new parameters

#### 2.2 Create Storage Factory
- [x] 2.2.1 Create initialize_storage function that uses TaskRequest parameters
- [x] 2.2.2 Implement SQLite storage connector
- [x] 2.2.3 Implement PostgreSQL storage connector
- [x] 2.2.4 Implement MongoDB storage connector
- [x] 2.2.5 Implement DynamoDB storage connector
- [x] 2.2.6 Implement JSON storage connector
- [x] 2.2.7 Implement YAML storage connector
- [x] 2.2.8 Add error handling for connection failures
- [x] 2.2.9 Add logging for storage initialization (Using Union type for AgentStorage rather than a base class)

#### 2.3 Implement Session Management
- [x] 2.3.1 Create session handling utilities
- [x] 2.3.2 Implement session creation
- [x] 2.3.3 Implement session resumption
- [x] 2.3.4 Add session metadata tracking
- [x] 2.3.5 Implement session cleanup mechanism

#### 2.4 Integrate Storage with Agents
- [x] 2.4.1 Modify agent creation to optionally use storage if the caller provides storage information
- [x] 2.4.2 Update team creation to optionally use storage if the caller provides storage information
- [x] 2.4.3 Add external state persistence between API calls with the callers provided storage
- [x] 2.4.4 Implement context carryover between sessions by connecting to and reading the session from callers storage

#### 2.5 Testing and Validation
- [x] 2.5.1 Test SQLite storage integration
- [x] 2.5.2 Test PostgreSQL storage integration
- [x] 2.5.3 Test MongoDB storage integration
- [x] 2.5.4 Test DynamoDB storage integration
- [x] 2.5.5 Test JSON storage integration
- [x] 2.5.6 Test YAML storage integration
- [x] 2.5.7 Validate session resumption functionality
- [x] 2.5.8 Test agent state persistence across API calls
- [ ] 2.5.9 Benchmark storage performance
- [ ] 2.5.10 Verify data persistence across server restarts

## 3. Tools and Memory Integration

### Current State
- Agents use a fixed set of tools
- No memory mechanisms implemented

### Target Implementation
- Allow callers to enable/disable specific tools
- Support custom tool definitions via API
- Implement memory types (chat history, user memories, summaries)

### Example Structure
```python
# All tool and memory configuration parameters in the flat TaskRequest
class TaskRequest(BaseModel):
    # Existing parameters...
    
    # Tool configuration
    enable_web_search: bool = Field(True, description="Enable web search tools")
    enable_file_tools: bool = Field(False, description="Enable file manipulation tools")
    enable_math_tools: bool = Field(True, description="Enable mathematical tools")
    custom_tools: Optional[List[Dict[str, Any]]] = Field(None, description="Custom tool definitions")
    
    # Memory configuration
    enable_chat_history: bool = Field(True, description="Enable chat history memory")
    enable_user_memories: bool = Field(False, description="Enable storing user-specific memories")
    enable_summaries: bool = Field(True, description="Enable conversation summaries")
    memory_depth: int = Field(10, description="Number of turns to remember")
    # ...
```

### Tasks and Subtasks

#### 3.1 Update TaskRequest Model
- [x] 3.1.1 Add tool configuration parameters directly to TaskRequest
- [x] 3.1.2 Add memory configuration parameters directly to TaskRequest
- [x] 3.1.3 Add validation for tool and memory parameters
- [x] 3.1.4 Update API documentation with new parameters

#### 3.2 Create Tool Management System
- [x] 3.2.1 Implement tool configuration factory using TaskRequest parameters
- [x] 3.2.2 Create tool filtering mechanism
- [x] 3.2.3 Add support for enabling/disabling specific tools
- [x] 3.2.4 Implement custom tool registration
- [x] 3.2.5 Add tool validation and security checks

#### 3.3 Implement Memory Systems
- [x] 3.3.1 Implement chat history memory
- [x] 3.3.2 Add conversation turn tracking
- [x] 3.3.3 Implement user-specific memories
- [x] 3.3.4 Add memory summarization capabilities
- [x] 3.3.5 Implement memory pruning for long conversations
- [x] 3.3.6 Create memory access utilities for agents

#### 3.4 Integrate with Agents
- [x] 3.4.1 Update agent creation to use configured tools
- [x] 3.4.2 Integrate memory systems with agents
- [x] 3.4.3 Modify team creation to use memory
- [x] 3.4.4 Add memory access to agent instructions

#### 3.5 Testing and Validation
- [x] 3.5.1 Test tool configuration functionality
- [x] 3.5.2 Validate custom tool integration
- [x] 3.5.3 Test memory systems functionality
- [x] 3.5.4 Validate memory persistence
- [x] 3.5.5 Test memory summarization

## 4. MCP Server Integration

### Current State
- Initial MCP server integration added to TaskRequest model
- Support for filesystem MCP and custom MCP servers implemented
- Need to complete integration with agents and testing

### Target Implementation
- Allow callers to provide MCP server configurations
- Support connection to multiple MCP servers
- Enable MCP-driven context enhancement

### Example Structure
```python
# MCP server configuration added directly to TaskRequest
class TaskRequest(BaseModel):
    # Existing parameters...
    
    # MCP Server parameters
    mcp_servers: Optional[List[Dict[str, Any]]] = Field(None, description="List of MCP servers to connect to")
    # Each dictionary contains: server_url, server_type, api_key, capabilities
    # ...
```

### Tasks and Subtasks

#### 4.1 Update TaskRequest Model
- [x] 4.1.1 Add mcp_servers parameter to TaskRequest as a list of server configurations
- [x] 4.1.2 Include command, args, env parameters for each server configuration
- [x] 4.1.3 Add filesystem_mcp and filesystem_root_path parameters
- [x] 4.1.4 Update API documentation with new parameters

#### 4.2 Implement MCP Protocol Client
- [x] 4.2.1 Create MCP client class (using Agno's built-in MCPTools)
- [x] 4.2.2 Implement MCP protocol handshake (handled by Agno's built-in MCPTools)
- [x] 4.2.3 Add support for MCP operations (already implemented in Agno)
- [x] 4.2.4 Implement context fetching (already handled by Agno's MCPTools)
- [x] 4.2.5 Add error handling and retries (Agno provides this functionality)
- [x] 4.2.6 Implement response processing (handled by Agno's implementation)

#### 4.3 Create MCP Server Connection Manager
- [x] 4.3.1 Implement connection manager class (using Agno's built-in MultiMCPTools)
- [x] 4.3.2 Add multiple server support (implemented with MultiMCPTools)
- [x] 4.3.3 Implement server health checking (handled by Agno's implementation)
- [x] 4.3.4 Add capability discovery (handled by Agno's implementation)
- [x] 4.3.5 Implement connection pooling (not needed with Agno's approach)
- [ ] 4.3.6 Add additional logging for MCP operations in our API

#### 4.4 Integrate MCP with Agents
- [x] 4.4.1 Create MCP context provider (using Agno's built-in tools)
- [x] 4.4.2 Integrate MCP with team creation (completed)
- [x] 4.4.3 Add MCP-based tool capabilities to team (completed)
- [x] 4.4.4 Update team creation to use MCP contexts (completed)
- [x] 4.4.5 Document MCP capabilities and usage patterns for API users

#### 4.5 Testing and Validation
- [x] 4.5.1 Test filesystem MCP functionality with our API
- [x] 4.5.2 Validate proper initialization and cleanup of MCP resources
- [x] 4.5.3 Test MCP tools with different team configurations
- [x] 4.5.4 Validate documentation with usage examples
- [x] 4.5.5 Test error handling for MCP server failures
- [x] 4.5.6 Create example scripts demonstrating MCP usage patterns

## 5. Containerization and Deployment

### Current State
- Empty Dockerfile and docker-compose.yml
- No proper containerization setup

### Target Implementation
- Complete Dockerfile with proper dependencies
- Production-ready docker-compose.yml with required services
- Environment variable configuration

### Tasks and Subtasks

#### 5.1 Create Comprehensive Dockerfile
- [x] 5.1.1 Set up base Python image
- [x] 5.1.2 Install system dependencies
- [x] 5.1.3 Configure Python environment
- [x] 5.1.4 Set up application directories
- [x] 5.1.5 Add dependency installation
- [x] 5.1.6 Add application code
- [x] 5.1.7 Configure entrypoint and startup

#### 5.2 Develop Docker Compose Configuration
- [x] 5.2.1 Configure API service
- [x] 5.2.2 Set up PostgreSQL service
- [x] 5.2.3 Add Redis service (optional)
- [x] 5.2.4 Configure volumes for data persistence
- [x] 5.2.5 Set up networking
- [x] 5.2.6 Add healthchecks
- [x] 5.2.7 Configure resource limits

#### 5.3 Environment Variable Management
- [x] 5.3.1 Create .env.example file
- [x] 5.3.2 Document all required environment variables
- [x] 5.3.3 Implement environment variable validation
- [x] 5.3.4 Add secrets management
- [x] 5.3.5 Configure default values

#### 5.4 Deployment Documentation
- [x] 5.4.1 Create deployment guide
- [x] 5.4.2 Document system requirements
- [x] 5.4.3 Add configuration options documentation
- [x] 5.4.4 Create troubleshooting guide
- [x] 5.4.5 Document scaling strategies

#### 5.5 Testing and Validation
- [ ] 5.5.1 Test Docker build process
- [ ] 5.5.2 Validate containerized application startup
- [ ] 5.5.3 Test Docker Compose environment
- [ ] 5.5.4 Validate data persistence
- [ ] 5.5.5 Benchmark containerized performance
- [ ] 5.5.6 Test container resource usage

## Phased Implementation Plan

### Phase 1: Core Infrastructure Updates (Weeks 1-2)
- [x] Update TaskRequest model to include all new parameters
  - [x] Knowledge base parameters
  - [x] Storage parameters
  - [x] Memory and tool parameters
  - [x] MCP server parameters
  - [ ] External agent parameters
- [x] Create factory functions that work with TaskRequest parameters
  - [x] Knowledge base factory
  - [x] Knowledge base agent integration
  - [x] Storage factory
  - [x] Tool configuration factory
- [ ] Set up Docker infrastructure
  - [ ] Create Dockerfile
  - [ ] Create docker-compose.yml

### Phase 2: Knowledge and Memory Integration (Weeks 3-4)
- [x] Knowledge base implementation
  - [x] Agent integration for knowledge base usage
  - [x] URL-based sources
  - [x] Text-based sources
  - [x] Vector database integration
- [x] Memory systems
  - [x] Chat history
  - [x] User memories
  - [x] Summaries
- [x] Testing and validation
  - [x] Knowledge retrieval testing
  - [x] Memory persistence testing

### Phase 3: Tools and Agent Communication (Weeks 5-6)
- [x] Tool configuration system
  - [x] Tool filtering
  - [x] Custom tool registration
- [x] Agent communication
  - [x] Protocol definition
  - [x] Agent registry
  - [x] Agent client
- [x] Integration and testing
  - [x] Tool integration testing
  - [x] Agent communication testing

### Phase 4: MCP and Advanced Features (Weeks 7-8)
- [x] MCP implementation
  - [x] MCP client (using Agno's built-in tools)
  - [x] Server connection manager (using Agno's MultiMCPTools)
  - [x] Error handling and resource cleanup
- [x] Initial integration
  - [x] MCP with team
  - [x] Filesystem MCP support
- [x] Documentation and testing
  - [x] Create MCP usage examples
  - [x] Add comprehensive documentation
  - [x] Implement test suite for MCP features
  - [ ] Production deployment configuration

### Phase 5: Containerization and Deployment (Weeks 9-10)
- [x] Docker infrastructure
  - [x] Create comprehensive Dockerfile
    - [x] Use Python 3.10-slim as base image
    - [x] Include only necessary system dependencies
    - [x] Set up proper application directories
    - [x] Run as non-root user for security
  - [x] Develop docker-compose.yml
    - [x] Configure API service
    - [x] Set up optional PostgreSQL service (dev profile only)
    - [x] Configure health checks and resource limits
  - [x] Set up environment variable management
    - [x] Minimize environment variables needed for container
    - [x] Create simplified .env.production.example file
- [x] Deployment configuration
  - [x] Create production deployment guide
    - [x] Document stateless API design principles
    - [x] Explain optional database approach
    - [x] Provide clear examples for deployment
  - [x] Document configuration options
    - [x] Emphasize caller-provided configuration approach 
    - [x] Clarify environment vs. API request parameters
  - [x] Set up scaling strategies
    - [x] Document horizontal scaling options
    - [x] Include resource optimization recommendations
- [ ] Testing and validation
  - [ ] Test Docker build process
  - [ ] Validate containerized application
  - [ ] Performance benchmarking

## Final TaskRequest Model

```python
class TaskRequest(BaseModel):
    """Enhanced request model for executing a task with extended capabilities"""

    # Core parameters
    message: str
    stream: bool = True
    provider: str = "openai"
    model: str = "gpt-4o"
    provider_api_key: str = Field(..., description="API key for the specified provider")
    verbose_logging: bool = Field(False, description="Enable verbose logging of the entire process")
    
    # Knowledge base parameters
    knowledge_urls: Optional[List[str]] = Field(None, description="URLs to use as knowledge sources")
    knowledge_text: Optional[str] = Field(None, description="Raw text to use as knowledge")
    vector_db_type: Optional[str] = Field("lancedb", description="Vector database type (lancedb, pgvector, pinecone, etc.)")
    embedder_provider: Optional[str] = Field("openai", description="Provider for embeddings")
    embedder_model: Optional[str] = Field("text-embedding-3-small", description="Embedding model to use")
    
    # Storage parameters
    storage_type: Optional[str] = Field(None, description="Storage type (sqlite, postgres)")
    storage_connection: Optional[str] = Field(None, description="Connection string for storage")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    
    # Tool configuration
    enable_web_search: Optional[bool] = Field(True, description="Enable web search tools")
    enable_file_tools: Optional[bool] = Field(False, description="Enable file manipulation tools")
    enable_math_tools: Optional[bool] = Field(True, description="Enable mathematical tools")
    custom_tools: Optional[List[Dict[str, Any]]] = Field(None, description="Custom tool definitions")
    
    # Memory configuration
    enable_chat_history: Optional[bool] = Field(True, description="Enable chat history memory")
    enable_user_memories: Optional[bool] = Field(False, description="Enable storing user-specific memories")
    enable_summaries: Optional[bool] = Field(True, description="Enable conversation summaries")
    memory_depth: Optional[int] = Field(10, description="Number of previous exchanges to remember")
    
    # External agent configuration
    external_agents: Optional[List[Dict[str, Any]]] = Field(None, description="List of external agents to make available")
    
    # MCP Server parameters
    mcp_servers: Optional[List[Dict[str, Any]]] = Field(None, description="List of MCP servers to connect to")
    
    @field_validator('provider_api_key')
    def validate_api_key(cls, v, info):
        provider = info.data.get('provider', '').lower()
        
        # Basic validation based on provider
        if provider == 'openai' and not v.startswith('sk-'):
            raise ValueError('OpenAI API key should start with "sk-"')
        elif provider == 'anthropic' and not v.startswith(('sk-', 'ant-')):
            raise ValueError('Anthropic API key should start with "sk-" or "ant-"')
        elif provider == 'formation' and not len(v) > 20:
            raise ValueError('Formation API key appears to be invalid')
        
        # Ensure the key has a minimum length for basic security
        if len(v) < 10:
            raise ValueError('API key is too short to be valid')
            
        return v
    
    # Add additional validators for the new fields
```

## First Implementation Steps

1. [ ] Create a feature branch for task request model updates
   - [ ] Create branch `feature/task-request-model-update`
   - [ ] Base from current main branch
   - [ ] Document branch purpose

2. [ ] Update the TaskRequest model with all new parameters
   - [ ] Add knowledge base parameters
   - [ ] Add storage parameters
   - [ ] Add memory and tool parameters
   - [ ] Add external agent parameters
   - [ ] Add MCP server parameters
   - [ ] Add validation methods

3. [ ] Create factory functions for new components
   - [ ] Create knowledge base factory function
   - [ ] Create storage factory function
   - [ ] Create tool configuration factory function

4. [ ] Update the API endpoint handler
   - [ ] Modify run_task to use the new parameters
   - [ ] Add logging for new parameter usage
   - [ ] Add conditional initialization based on provided parameters

5. [ ] Update API documentation
   - [ ] Document all new parameters
   - [ ] Provide usage examples
   - [ ] Update OpenAPI schema 

## Containerization Summary

The containerization approach for the Fama AI system follows these key principles:

### 1. Truly Stateless API Design

The containerized API is designed to be completely stateless, with no persistent state stored in the container between requests. All configuration is provided by API callers in their API requests, including:

- Model provider API keys
- Storage connection strings 
- Knowledge base parameters
- MCP server configurations
- Memory system preferences

This design offers several advantages:
- **Simplified deployment**: No environment secrets to manage in the container
- **Secure configuration**: API callers maintain control of their API keys
- **Easy horizontal scaling**: Any number of identical containers can be deployed
- **No vendor lock-in**: Clients can use their own infrastructure for storage

### 2. Optional Development Database

While the API does not require any database connection, we've included an optional PostgreSQL container with pgvector extension to facilitate development and testing:

- Can be enabled with `--profile dev` flag
- Not started by default in production
- Not automatically connected to the API (callers still provide connection info)
- Includes pgvector extension for vector storage when testing knowledge base features

### 3. Deployment Flexibility

The containerization supports various deployment scenarios:

- **Simple API-only deployment**: Just the API container with no dependencies
- **Development setup**: API + PostgreSQL for local testing
- **Cloud deployment**: Can be deployed to any container orchestration system
- **Scaling options**: Horizontal scaling for high-throughput scenarios

### 4. Security Best Practices

Security considerations are integrated throughout the containerization:

- Running as non-root user
- Minimal base image and dependencies
- Clear separation of API and database
- Resource limits to prevent container abuse
- Health checks for monitoring container state

This approach enables the Fama AI system to be deployed efficiently while maintaining the flexibility for API callers to provide their own configuration, model providers, and storage options. 