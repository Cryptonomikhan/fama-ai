import sys
import os

from textwrap import dedent
from typing import AsyncGenerator, Union, Optional, List, Dict, Any
import uvicorn
import logging
import json
from http import HTTPStatus
import datetime
import os
import sys
import time
import uuid

from agno.agent import Agent
from agno.team.team import Team
from fastapi import APIRouter, status, FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
from src.agents.financial_modeler import FinancialModelingAgent
from pydantic import BaseModel, Field, field_validator

from src.models.factory import create_model
from src.storage.factory import initialize_storage

# Import our knowledge logging module
from src.knowledge.logging import wrap_knowledge_base, get_knowledge_logs

# Add imports for MCP
from agno.tools.mcp import MCPTools, MultiMCPTools

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"financial_api_{datetime.datetime.now().strftime('%Y%m%d')}.log")

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)

# Store logs in memory for easy retrieval (limited to recent logs)
MAX_IN_MEMORY_LOGS = 100
request_logs = {}

# Set up logger
logger = logging.getLogger(__name__)

task_router = APIRouter(prefix="/task", tags=["Tasks"])


async def chat_response_streamer(
    agent: Union[Agent, Team],
    message: str
) -> AsyncGenerator:
    """
    Stream agent responses chunk by chunk

    Args:
        agent: The agent instance to interact with
        message: User message to process

    Yields:
        Text chunks from the agent response
    """
    logger.info("Starting streaming response")
    
    run_response = await agent.arun(message, stream=True)
    
    chunk_count = 0
    async for chunk in run_response:
        chunk_count += 1
        if chunk_count % 20 == 0:  # Log every 20th chunk to avoid excessive logging
            logger.debug(f"Streaming chunk {chunk_count}: {chunk.content[:50]}...")
        yield chunk.content
    
    logger.info(f"Completed streaming response with {chunk_count} chunks")


class TaskRequest(BaseModel):
    """Request model for executing a task"""
    
    model_id: str = Field(..., description="ID of the model to use")
    model_provider: str = Field("openai", description="Provider of the model")
    task: str = Field(..., description="Task description to be executed")
    enable_semantic_search: bool = Field(False, description="Enable semantic search for knowledge retrieval")
    vector_db_type: str = Field("lancedb", description="Type of vector database to use (lancedb, tantivy, etc.)")
    knowledge_urls: Optional[List[str]] = Field(None, description="URLs to use as knowledge sources")
    knowledge_text: Optional[str] = Field(None, description="Raw text to use as knowledge source")
    embedder_provider: str = Field("openai", description="Provider for embeddings (openai, cohere)")
    embedder_model: str = Field("text-embedding-3-small", description="Embedding model to use")
    provider_api_key: Optional[str] = Field(None, description="API key for the specified provider")
    embedder_dimensions: Optional[int] = Field(None, description="The dimensions for the embedder (required for local embedders)")
    knowledge_source_type: Optional[str] = Field(None, description="Type of knowledge source to use (pdf_url, web, text, etc.)")
    chunking_strategy: str = Field("fixed", description="Chunking strategy to use (fixed, agentic, semantic, recursive, document)")
    chunk_size: int = Field(5000, description="Maximum size of each chunk")
    chunk_overlap: int = Field(0, description="Number of characters to overlap between chunks")
    similarity_threshold: float = Field(0.5, description="Similarity threshold for semantic chunking")
    verbose_logging: bool = Field(False, description="Enable verbose logging of the entire process")
    # Storage parameters
    storage_type: Optional[str] = Field(None, description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: Optional[str] = Field(None, description="Connection string or configuration for storage. Format depends on storage_type: \
        sqlite: 'sqlite:///data.db' or path to db file, \
        postgres: 'postgresql://user:pass@host:port/db', \
        mongodb: 'mongodb://user:pass@host:port/db', \
        dynamodb: JSON string with AWS credentials and region, \
        json/yaml: Directory path for storing files")
    session_id: Optional[str] = Field(None, description="Session ID for resuming conversations across multiple API calls")
    user_id: Optional[str] = Field(None, description="User ID for personalization and tracking user-specific data")
    # Memory parameters
    enable_chat_history: bool = Field(True, description="Enable chat history memory")
    enable_user_memories: bool = Field(False, description="Enable storing user-specific memories")
    enable_summaries: bool = Field(True, description="Enable conversation summaries")
    memory_depth: int = Field(10, description="Number of messages to keep in memory")
    # Tool parameters
    enable_web_search: bool = Field(True, description="Enable web search tools")
    enable_file_tools: bool = Field(False, description="Enable file manipulation tools")
    enable_math_tools: bool = Field(True, description="Enable mathematical tools")
    custom_tools: Optional[List[Dict[str, Any]]] = Field(None, description="Custom tool definitions")
    # MCP parameters
    mcp_servers: Optional[List[Dict[str, Any]]] = Field(None, description="List of MCP servers to connect to. Each server should include: \
        command: Command to run the MCP server (or full command including args), \
        args: Arguments to pass to the command (optional if included in command), \
        env: Environment variables to pass to the server (optional)")
    use_filesystem_mcp: bool = Field(False, description="Enable filesystem MCP server for local file access")
    filesystem_root_path: Optional[str] = Field(None, description="Root path for filesystem MCP server (defaults to current directory)")
    
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
    
    @field_validator('knowledge_urls')
    def validate_knowledge_urls(cls, v):
        if v is not None:
            # Check if we have at least one URL
            if len(v) == 0:
                raise ValueError('knowledge_urls cannot be an empty list')
            
            # Validate that each URL is properly formatted
            for url in v:
                if not url.startswith(('http://', 'https://')):
                    raise ValueError(f'Invalid URL format: {url}. URLs must start with http:// or https://')
                if len(url) < 10:  # Basic length check
                    raise ValueError(f'URL is too short to be valid: {url}')
        return v
    
    @field_validator('knowledge_text')
    def validate_knowledge_text(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('knowledge_text cannot be empty')
        return v
    
    @field_validator('vector_db_type')
    def validate_vector_db_type(cls, v):
        allowed_types = ['lancedb', 'pgvector', 'pinecone', 'cassandra', 
                         'chroma', 'clickhouse', 'milvus', 'mongodb', 'qdrant', 
                         'singlestore', 'weaviate']
        if v.lower() not in allowed_types:
            raise ValueError(f'vector_db_type must be one of {allowed_types}')
        return v.lower()
    
    @field_validator('embedder_provider')
    def validate_embedder_provider(cls, v):
        allowed_providers = ['openai', 'cohere']
        if v.lower() not in allowed_providers:
            raise ValueError(f'embedder_provider must be one of {allowed_providers}')
        return v.lower()
    
    @field_validator('embedder_model')
    def validate_embedder_model(cls, v, info):
        embedder_provider = info.data.get('embedder_provider', '').lower()
        
        # Validate based on provider
        if embedder_provider == 'openai':
            allowed_models = ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002']
            if v not in allowed_models:
                raise ValueError(f'For OpenAI embeddings, model must be one of {allowed_models}')
        elif embedder_provider == 'cohere':
            allowed_models = ['embed-english-v3.0', 'embed-multilingual-v3.0']
            if v not in allowed_models:
                raise ValueError(f'For Cohere embeddings, model must be one of {allowed_models}')
        
        return v

    @field_validator('chunking_strategy')
    def validate_chunking_strategy(cls, v):
        allowed_strategies = ['fixed', 'agentic', 'semantic', 'recursive', 'document']
        if v.lower() not in allowed_strategies:
            raise ValueError(f'chunking_strategy must be one of {allowed_strategies}')
        return v.lower()
    
    @field_validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v <= 0:
            raise ValueError('chunk_size must be positive')
        return v
    
    @field_validator('chunk_overlap')
    def validate_chunk_overlap(cls, v, info):
        chunk_size = info.data.get('chunk_size', 5000)
        if v < 0:
            raise ValueError('chunk_overlap must be non-negative')
        if v >= chunk_size:
            raise ValueError(f'chunk_overlap ({v}) must be less than chunk_size ({chunk_size})')
        return v
    
    @field_validator('similarity_threshold')
    def validate_similarity_threshold(cls, v):
        if v is not None and (v <= 0 or v >= 1):
            raise ValueError('similarity_threshold must be between 0 and 1')
        return v
    
    @field_validator('storage_type')
    def validate_storage_type(cls, v):
        if v is not None:
            allowed_types = ['sqlite', 'postgres', 'mongodb', 'dynamodb', 'json', 'yaml']
            if v.lower() not in allowed_types:
                raise ValueError(f'storage_type must be one of {allowed_types}')
        return v.lower() if v is not None else v
    
    @field_validator('storage_connection')
    def validate_storage_connection(cls, v, info):
        if v is not None:
            storage_type = info.data.get('storage_type')
            
            if not storage_type:
                raise ValueError('storage_type must be provided when storage_connection is specified')
            
            # Validate connection string based on storage type
            if storage_type == 'sqlite':
                # Check for either sqlite:/// format or a valid file path
                if not (v.startswith('sqlite:///') or v.endswith('.db') or '/' in v or '\\' in v):
                    raise ValueError('SQLite connection must be either a sqlite:/// URL or a valid file path (e.g., "tmp/data.db")')
            
            elif storage_type == 'postgres':
                # Check for postgresql:// format
                if not (v.startswith('postgresql://') or v.startswith('postgresql+psycopg://')):
                    raise ValueError('PostgreSQL connection must start with postgresql:// or postgresql+psycopg:// (e.g., "postgresql+psycopg://ai:ai@localhost:5532/ai")')
            
            elif storage_type == 'mongodb':
                # Check for mongodb:// format
                if not v.startswith('mongodb://'):
                    raise ValueError('MongoDB connection must start with mongodb:// (e.g., "mongodb://ai:ai@localhost:27017/agno")')
            
            elif storage_type == 'dynamodb':
                # For DynamoDB, we expect a JSON string with aws credentials
                try:
                    import json
                    config = json.loads(v)
                    required_keys = ['region_name']
                    optional_keys = ['aws_access_key_id', 'aws_secret_access_key', 'endpoint_url', 'table_name']
                    
                    # Check required keys
                    for key in required_keys:
                        if key not in config:
                            raise ValueError(f'DynamoDB connection JSON must contain {key}')
                    
                    # Validate that all keys are recognized
                    for key in config.keys():
                        if key not in required_keys and key not in optional_keys:
                            raise ValueError(f'Unrecognized key in DynamoDB config: {key}')
                            
                except json.JSONDecodeError:
                    raise ValueError('DynamoDB connection must be a valid JSON string with AWS configuration')
            
            elif storage_type in ['json', 'yaml']:
                # For JSON and YAML, we expect a directory path
                if not ('/' in v or '\\' in v):
                    raise ValueError(f'{storage_type.upper()} storage connection must be a valid directory path (e.g., "tmp/agent_sessions_{storage_type}")')
        
        return v
    
    @field_validator('session_id')
    def validate_session_id(cls, v, info):
        if v is not None:
            # Basic validation for session_id format
            if len(v.strip()) == 0:
                raise ValueError('session_id cannot be empty')
            
            # If storage is specified, session_id should be provided
            storage_type = info.data.get('storage_type')
            if storage_type and not v:
                # This is just a warning, not an error, as session_id is optional
                logger.warning('storage_type is specified but session_id is not provided; a new session will be created')
        return v
    
    @field_validator('user_id')
    def validate_user_id(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('user_id cannot be empty')
        return v


# Log retrieval endpoint
@task_router.get("/logs/{request_id}", status_code=status.HTTP_200_OK, tags=["Logs"])
async def get_request_logs(request_id: str):
    """
    Retrieve logs for a specific request
    """
    if request_id in request_logs:
        return {"request_id": request_id, "logs": request_logs[request_id]}
    else:
        # Try to read from log file
        try:
            all_logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    for line in f:
                        if request_id in line:
                            all_logs.append(line.strip())
            
            if all_logs:
                return {"request_id": request_id, "logs": all_logs}
            else:
                return JSONResponse(
                    content={"error": f"No logs found for request ID: {request_id}"},
                    status_code=HTTPStatus.NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error retrieving logs for request ID {request_id}: {str(e)}")
            return JSONResponse(
                content={"error": f"Error retrieving logs: {str(e)}"},
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )

# Knowledge log retrieval endpoint
@task_router.get("/knowledge-logs", status_code=status.HTTP_200_OK, tags=["Logs"])
async def get_kb_logs(limit: int = 100, operation_type: Optional[str] = None):
    """
    Retrieve knowledge base operation logs
    
    Args:
        limit: Maximum number of logs to return (default: 100)
        operation_type: Filter logs by operation type (query, results, error)
        
    Returns:
        List of knowledge base operation logs
    """
    try:
        logs = get_knowledge_logs(limit=limit, operation_type=operation_type)
        return {
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error retrieving knowledge logs: {str(e)}")
        return JSONResponse(
            content={"error": f"Error retrieving knowledge logs: {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@task_router.post("/submit", status_code=status.HTTP_200_OK)
async def run_task(body: TaskRequest):
    """
    Execute a financial modeling task with a coordinated team of specialized agents.
    
    This endpoint processes a natural language task description and generates a comprehensive 
    financial analysis using a team of specialized agents.
    
    ## Knowledge Base Parameters
    
    The API supports integration with external knowledge sources, with robust error handling:
    
    - **knowledge_urls**: List of URLs to documents that will be used as knowledge sources
    - **knowledge_text**: Raw text content to use as a knowledge source
    - **vector_db_type**: Type of vector database to use ("lancedb", "pgvector", "pinecone", etc.)
    - **embedder_provider**: Provider for embedding models ("openai", "cohere")
    - **embedder_model**: Specific embedding model to use (varies by provider)
    
    ## Storage Parameters
    
    The API supports persistent storage for conversations and agent state:
    
    - **storage_type**: Type of storage backend to use ("sqlite", "postgres", "mongodb", "dynamodb", "json", "yaml")
    - **storage_connection**: Connection string or configuration for the selected storage type:
      - SQLite: "sqlite:///data.db" or path to db file
      - PostgreSQL: "postgresql://user:pass@host:port/db"
      - MongoDB: "mongodb://user:pass@host:port/db"
      - DynamoDB: JSON string with AWS credentials and region
      - JSON/YAML: Directory path for storing files
    - **session_id**: Session ID for resuming conversations across multiple API calls
    - **user_id**: User ID for personalization and tracking user-specific data
    
    ## Fault Tolerance
    
    The API is designed to be robust and continue operation even when:
    
    - Knowledge base initialization fails due to missing dependencies
    - Requested vector database or embedder is not available
    - Document formats are not supported by the current installation
    - API will automatically fall back to operating without knowledge base support
    
    This ensures maximum flexibility for callers, while providing detailed logs about any fallback behavior.
    
    ## Chunking Parameters
    
    The API supports various document chunking strategies:
    
    - **chunking_strategy**: Strategy to use ("fixed", "agentic", "semantic", "recursive", "document")
    - **chunk_size**: Maximum size of each chunk (default: 5000)
    - **chunk_overlap**: Number of characters to overlap between chunks (default: 0)
    - **similarity_threshold**: Threshold for semantic chunking (default: 0.5, only used with semantic chunking)
    
    Example with chunking parameters:
    ```json
    {
      "message": "Create a financial model for a rental property investment",
      "provider": "openai",
      "model": "gpt-4o",
      "provider_api_key": "your-api-key",
      "knowledge_urls": ["https://example.com/rental-rates-2023.pdf"],
      "vector_db_type": "lancedb",
      "chunking_strategy": "semantic", 
      "chunk_size": 2000,
      "similarity_threshold": 0.7
    }
    ```
    
    Example with storage parameters for session persistence:
    ```json
    {
      "message": "Continue our discussion about the tokenized GPU investment",
      "provider": "openai",
      "model": "gpt-4o",
      "provider_api_key": "your-api-key",
      "storage_type": "sqlite",
      "storage_connection": "sqlite:///sessions.db",
      "session_id": "user123-session456",
      "user_id": "user123"
    }
    ```
    
    Returns:
        Financial analysis based on the provided task description
    """
    request_id = f"{body.provider}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Create session ID for knowledge logging
    session_id = str(uuid.uuid4())
    
    # Initialize log storage for this request
    request_logs[request_id] = []
    
    # Custom log handler to store logs in memory too
    def log_to_memory(log_message):
        if len(request_logs) > MAX_IN_MEMORY_LOGS:
            # Remove oldest request logs if we exceed the limit
            oldest_key = next(iter(request_logs))
            request_logs.pop(oldest_key)
        
        request_logs[request_id].append(log_message)
    
    try:
        logger.info(f"Starting new task request ID: {request_id}")
        log_to_memory(f"Starting new task request ID: {request_id}")
        
        # Set log level based on verbose flag
        if body.verbose_logging:
            logger.setLevel(logging.DEBUG)
            logger.info("Verbose logging enabled")
            log_to_memory("Verbose logging enabled")
        
        # Create the model with the provided API key
        model_kwargs = {"api_key": body.provider_api_key}
        
        # Initialize knowledge base if knowledge sources are provided
        knowledge_base = None
        if body.knowledge_urls or body.knowledge_text:
            logger.info("Initializing knowledge base")
            log_to_memory("Initializing knowledge base")
            
            try:
                from src.knowledge.factory import initialize_knowledge_base, KnowledgeBaseError
                
                # Extract knowledge base parameters from the request
                kb_params = {
                    "knowledge_urls": body.knowledge_urls,
                    "knowledge_text": body.knowledge_text,
                    "vector_db_type": body.vector_db_type,
                    "embedder_provider": body.embedder_provider,
                    "embedder_model": body.embedder_model,
                    "provider_api_key": body.provider_api_key,
                    "chunking_strategy": body.chunking_strategy,
                    "chunk_size": body.chunk_size,
                    "chunk_overlap": body.chunk_overlap,
                    "similarity_threshold": body.similarity_threshold
                }
                
                # Initialize the knowledge base
                logger.info("Starting knowledge base initialization with parameters:")
                log_to_memory("Starting knowledge base initialization with parameters:")
                
                # Log knowledge base parameters (excluding sensitive information)
                safe_params = kb_params.copy()
                if "provider_api_key" in safe_params:
                    safe_params["provider_api_key"] = "***REDACTED***"
                
                for key, value in safe_params.items():
                    if key not in ["knowledge_text"]:  # Don't log potentially large text content
                        logger.info(f"  - {key}: {value}")
                        log_to_memory(f"  - {key}: {value}")
                
                try:
                    # Initialize the knowledge base
                    knowledge_base = initialize_knowledge_base(**kb_params)
                    
                    # Wrap the knowledge base with our logging wrapper
                    if knowledge_base:
                        logger.info("Wrapping knowledge base with detailed logging")
                        log_to_memory("Wrapping knowledge base with detailed logging")
                        knowledge_base = wrap_knowledge_base(
                            knowledge_base,
                            agent_name="APIEndpoint",
                            session_id=session_id
                        )
                except KnowledgeBaseError as kbe:
                    # Handle known knowledge base errors with specific error handling
                    error_message = f"Knowledge base initialization error: {str(kbe)}"
                    logger.error(error_message)
                    log_to_memory(error_message)
                    
                    # Log detailed error information if available
                    if hasattr(kbe, 'details') and kbe.details:
                        logger.error(f"Knowledge base error details: {kbe.details}")
                        log_to_memory(f"Knowledge base error details: {kbe.details}")
                        
                    # Continue without knowledge base but explicitly log the failure impact
                    logger.warning("Proceeding with agents without knowledge base support due to initialization failure")
                    log_to_memory("Proceeding with agents without knowledge base support due to initialization failure")
                    knowledge_base = None
                except ValueError as ve:
                    # Handle validation errors separately
                    error_message = f"Knowledge base parameter validation error: {str(ve)}"
                    logger.error(error_message)
                    log_to_memory(error_message)
                    
                    # Continue without knowledge base
                    logger.warning("Proceeding with agents without knowledge base support due to validation error")
                    log_to_memory("Proceeding with agents without knowledge base support due to validation error")
                    knowledge_base = None
                except ImportError as ie:
                    # Handle missing dependency errors
                    error_message = f"Missing dependency for knowledge base: {str(ie)}"
                    logger.error(error_message)
                    log_to_memory(error_message)
                    
                    # Continue without knowledge base
                    logger.warning("Proceeding with agents without knowledge base support due to missing dependency")
                    log_to_memory("Proceeding with agents without knowledge base support due to missing dependency")
                    knowledge_base = None
                
                if knowledge_base:
                    # Add additional information about the knowledge base
                    try:
                        kb_info = {}
                        
                        # Get knowledge base details if available
                        if hasattr(knowledge_base, 'metadata'):
                            kb_info['metadata'] = knowledge_base.metadata
                        
                        if hasattr(knowledge_base, 'vectordb') and knowledge_base.vectordb:
                            kb_info['vector_db_type'] = type(knowledge_base.vectordb).__name__
                            
                            # Log vector database details if available
                            if hasattr(knowledge_base.vectordb, 'get_stats'):
                                stats = knowledge_base.vectordb.get_stats()
                                kb_info['vector_db_stats'] = stats
                        
                        # Log source information if available
                        if hasattr(knowledge_base, 'urls') and knowledge_base.urls:
                            kb_info['url_count'] = len(knowledge_base.urls)
                            
                        if hasattr(knowledge_base, 'chunking_strategy') and knowledge_base.chunking_strategy:
                            kb_info['chunking_strategy'] = type(knowledge_base.chunking_strategy).__name__
                            if hasattr(knowledge_base.chunking_strategy, 'chunk_size'):
                                kb_info['chunk_size'] = knowledge_base.chunking_strategy.chunk_size
                                
                        # Log the knowledge base info
                        logger.info(f"Knowledge base initialized successfully with the following details:")
                        for key, value in kb_info.items():
                            logger.info(f"  - {key}: {value}")
                            log_to_memory(f"  - {key}: {value}")
                    except Exception as e:
                        # Log any errors during info collection, but don't fail
                        logger.warning(f"Error collecting knowledge base details: {str(e)}")
                        log_to_memory(f"Error collecting knowledge base details: {str(e)}")
                else:
                    logger.warning("No knowledge base created - no knowledge sources provided")
                    log_to_memory("No knowledge base created - no knowledge sources provided")
            except Exception as e:
                # Catch-all for any unexpected errors
                error_message = f"Unexpected error initializing knowledge base: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                # Log traceback for debugging
                import traceback
                traceback_str = traceback.format_exc()
                logger.error(f"Knowledge base initialization traceback: {traceback_str}")
                log_to_memory(f"Knowledge base initialization traceback (summary): {str(e)}")
                
                # Add context to error response
                if hasattr(body, 'verbose_logging') and body.verbose_logging:
                    # Only log full traceback to memory if verbose logging is enabled
                    log_to_memory(f"Knowledge base initialization traceback: {traceback_str}")
                
                # Continue without knowledge base but explicitly log the failure impact
                logger.warning("Proceeding with agents without knowledge base support due to unexpected error")
                log_to_memory("Proceeding with agents without knowledge base support due to unexpected error")
                knowledge_base = None
                
                # Attempt to close/cleanup any partially initialized resources
                try:
                    if 'knowledge_base' in locals() and knowledge_base is not None and hasattr(knowledge_base, 'close'):
                        knowledge_base.close()
                        logger.info("Successfully closed knowledge base connection after error")
                except Exception as cleanup_error:
                    logger.warning(f"Error during resource cleanup after knowledge base failure: {str(cleanup_error)}")
        
        # Initialize storage if provided
        storage = None
        if body.storage_type and body.storage_connection:
            try:
                logger.info(f"Initializing {body.storage_type} storage with connection: {body.storage_connection[:20]}...")
                log_to_memory(f"Initializing {body.storage_type} storage with connection: {body.storage_connection[:20]}...")
                
                storage = initialize_storage(
                    storage_type=body.storage_type,
                    storage_connection=body.storage_connection,
                    table_name="agent_sessions",
                    session_id=body.session_id,
                    user_id=body.user_id
                )
                
                logger.info(f"Storage initialized successfully: {type(storage).__name__}")
                log_to_memory(f"Storage initialized successfully: {type(storage).__name__}")
            except Exception as e:
                error_message = f"Error initializing storage: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                logger.warning("Continuing without storage")
                log_to_memory("Continuing without storage")
                storage = None
        
        # Validate that knowledge base is operational if it exists
        if knowledge_base:
            logger.info("Agents will be initialized with knowledge base")
            log_to_memory("Agents will be initialized with knowledge base")
            
            # Validate that the knowledge base is operational
            try:
                # Perform a simple test query to verify knowledge base functionality
                test_query = "test query to verify knowledge base is operational"
                logger.debug(f"Testing knowledge base with query: {test_query}")
                _ = knowledge_base.query(test_query)
                logger.info("Knowledge base test query succeeded")
            except Exception as e:
                # If test query fails, log error but continue without knowledge base
                error_message = f"Knowledge base test query failed: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                logger.warning("Disabling knowledge base due to test query failure")
                log_to_memory("Disabling knowledge base due to test query failure")
                knowledge_base = None
        else:
            logger.info("Agents will be initialized without knowledge base")
            log_to_memory("Agents will be initialized without knowledge base")
        
        # Set up knowledge base query logging if it exists
        if knowledge_base:
            # Create a wrapper to log knowledge base queries
            original_query = knowledge_base.query
            
            def query_with_logging(*args, **kwargs):
                query_text = args[0] if args else kwargs.get('text', 'No query text available')
                query_id = f"kb_query_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                
                logger.info(f"Knowledge base query {query_id}: {query_text[:100]}...")
                log_to_memory(f"Knowledge base query {query_id}: {query_text[:100]}...")
                
                try:
                    # Track query start time
                    start_time = time.time()
                    
                    # Call the original query method
                    results = original_query(*args, **kwargs)
                    
                    # Track query end time and calculate duration
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Log the results
                    result_count = len(results) if isinstance(results, list) else 1
                    logger.info(f"Knowledge base query {query_id} returned {result_count} results in {duration:.2f}s")
                    log_to_memory(f"Knowledge base query {query_id} returned {result_count} results in {duration:.2f}s")
                    
                    # Log snippets of returned content, avoiding excessive logging
                    if body.verbose_logging:
                        if isinstance(results, list):
                            for i, result in enumerate(results[:3]):  # Log only the first 3 results
                                content = result.get('content', str(result))
                                content_preview = content[:100] + "..." if len(content) > 100 else content
                                logger.debug(f"Knowledge base query {query_id} result {i+1}: {content_preview}")
                                log_to_memory(f"Knowledge base query {query_id} result {i+1}: {content_preview}")
                            
                            if len(results) > 3:
                                logger.debug(f"Knowledge base query {query_id}: {len(results) - 3} more results not shown")
                                log_to_memory(f"Knowledge base query {query_id}: {len(results) - 3} more results not shown")
                        else:
                            content = getattr(results, 'content', str(results))
                            content_preview = content[:100] + "..." if len(content) > 100 else content
                            logger.debug(f"Knowledge base query {query_id} result: {content_preview}")
                            log_to_memory(f"Knowledge base query {query_id} result: {content_preview}")
                    
                    return results
                except Exception as e:
                    error_message = f"Error during knowledge base query {query_id}: {str(e)}"
                    logger.error(error_message)
                    log_to_memory(error_message)
                    # Re-raise the exception
                    raise
            
            # Replace the original query method with our logging wrapper
            knowledge_base.query = query_with_logging
            
            logger.info("Knowledge base query logging enabled")
            log_to_memory("Knowledge base query logging enabled")

        # Initialize memory configuration
        memory = None
        if storage and (body.enable_chat_history or body.enable_user_memories or body.enable_summaries):
            try:
                from agno.memory.agent import AgentMemory
                from agno.memory.db.sqlite import SqliteMemoryDb
                
                logger.info("Initializing AgentMemory with requested capabilities")
                log_to_memory("Initializing AgentMemory with requested capabilities")
                
                # Determine appropriate memory DB from storage type
                # Default to SQLite for simplicity if needed
                memory_db = None
                if body.storage_type == "sqlite":
                    from agno.memory.db.sqlite import SqliteMemoryDb
                    memory_db = SqliteMemoryDb(
                        table_name="agent_memories",
                        db_file=body.storage_connection
                    )
                elif body.storage_type == "postgres":
                    from agno.memory.db.postgres import PgMemoryDb
                    memory_db = PgMemoryDb(
                        table_name="agent_memories",
                        db_url=body.storage_connection
                    )
                elif body.storage_type == "mongodb":
                    from agno.memory.db.mongodb import MongoMemoryDb
                    memory_db = MongoMemoryDb(
                        collection_name="agent_memories",
                        connection_string=body.storage_connection
                    )
                else:
                    # Default to SQLite in-memory for other storage types
                    from agno.memory.db.sqlite import SqliteMemoryDb
                    memory_db = SqliteMemoryDb(
                        table_name="agent_memories",
                        db_file=":memory:"
                    )
                    
                memory = AgentMemory(
                    db=memory_db,
                    create_user_memories=body.enable_user_memories,
                    update_user_memories_after_run=body.enable_user_memories,
                    create_session_summary=body.enable_summaries,
                    update_session_summary_after_run=body.enable_summaries,
                    max_messages=body.memory_depth if body.memory_depth else 10
                )
                
                logger.info(f"Memory initialized with user_memories={body.enable_user_memories}, summaries={body.enable_summaries}")
                log_to_memory(f"Memory initialized with user_memories={body.enable_user_memories}, summaries={body.enable_summaries}")
                
            except Exception as e:
                error_message = f"Error initializing memory: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                logger.warning("Continuing without advanced memory features")
                log_to_memory("Continuing without advanced memory features")
                memory = None
        
        # Configure tools for agents
        additional_tools = []
        try:
            from src.tools.factory import create_tools
            
            logger.info("Configuring tools based on request parameters")
            log_to_memory("Configuring tools based on request parameters")
            
            # Convert any custom tools from dict to ToolConfig
            custom_tool_configs = []
            if body.custom_tools:
                from src.api.models.model_request import ToolConfig
                for tool_dict in body.custom_tools:
                    try:
                        custom_tool_configs.append(ToolConfig(**tool_dict))
                    except Exception as e:
                        logger.warning(f"Invalid custom tool configuration: {str(e)}")
            
            # Create the tools
            additional_tools = create_tools(
                tools=custom_tool_configs,
                web_search_enabled=body.enable_web_search,
                data_analysis_enabled=getattr(body, 'enable_data_analysis', False),
                calculator_enabled=body.enable_math_tools
            )
            
            logger.info(f"Created {len(additional_tools)} tools for agents")
            log_to_memory(f"Created {len(additional_tools)} tools for agents")
            
        except Exception as e:
            error_message = f"Error configuring tools: {str(e)}"
            logger.error(error_message)
            log_to_memory(error_message)
            logger.warning("Continuing with default tools only")
            log_to_memory("Continuing with default tools only")
            additional_tools = []
        
        # Initialize MCP tools if configured
        mcp_tools = None
        try:
            if body.mcp_servers or body.use_filesystem_mcp:
                # Create the list of MCP server commands
                mcp_commands = []
                
                # Add filesystem MCP if enabled
                if body.use_filesystem_mcp:
                    fs_path = body.filesystem_root_path or os.getcwd()
                    filesystem_command = f"npx -y @modelcontextprotocol/server-filesystem {fs_path}"
                    mcp_commands.append(filesystem_command)
                
                # Add other configured MCP servers
                if body.mcp_servers:
                    for server_config in body.mcp_servers:
                        if "command" in server_config:
                            if "args" in server_config and server_config["args"]:
                                # If args are provided separately, combine them with the command
                                cmd = f"{server_config['command']} {' '.join(server_config['args'])}"
                            else:
                                # Use the command as is
                                cmd = server_config["command"]
                            mcp_commands.append(cmd)
                
                # Set up environment variables
                env_vars = os.environ.copy()
                if body.mcp_servers:
                    for server_config in body.mcp_servers:
                        if "env" in server_config and server_config["env"]:
                            env_vars.update(server_config["env"])
                
                # Initialize MCP tools
                if len(mcp_commands) == 1:
                    # Use single MCPTools for better efficiency if only one server
                    mcp_tools = await MCPTools(mcp_commands[0], env=env_vars).__aenter__()
                elif len(mcp_commands) > 1:
                    # Use MultiMCPTools for multiple servers
                    mcp_tools = await MultiMCPTools(mcp_commands, env=env_vars).__aenter__()
                
                logger.info(f"Initialized MCP tools with {len(mcp_commands)} servers")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP tools: {str(e)}")
            # Continue without MCP tools if initialization fails
        
        # Create agents with knowledge base, storage, memory and tools
        searcher = SearchingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            knowledge_base=knowledge_base,
            search_knowledge=True if knowledge_base else False,
            session_id=body.session_id,  # Pass session ID for tracking
            storage=storage,  # Pass storage for persistence
            additional_tools=additional_tools,  # Pass configured tools
            **model_kwargs
        )
        assumption_generator = AssumptionGeneratorAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            knowledge_base=knowledge_base,
            search_knowledge=True if knowledge_base else False,
            session_id=body.session_id,
            storage=storage,
            additional_tools=additional_tools,
            **model_kwargs
        )
        metrics_deriver = MetricsDerivingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            knowledge_base=knowledge_base,
            search_knowledge=True if knowledge_base else False,
            session_id=body.session_id,
            storage=storage,
            additional_tools=additional_tools,
            **model_kwargs
        )
        modeler = FinancialModelingAgent(
            provider=body.provider,
            model_id=body.model,
            temperature=0.025,
            knowledge_base=knowledge_base,
            search_knowledge=True if knowledge_base else False,
            session_id=body.session_id,
            storage=storage,
            additional_tools=additional_tools,
            **model_kwargs
        )

        logger.info("Creating team with all agents")
        log_to_memory("Creating team with all agents")
        
        # Determine if we need to add memory access to instructions
        memory_instructions = ""
        if body.enable_chat_history or body.enable_user_memories or body.enable_summaries:
            memory_instructions = dedent("""
                ## Memory Access
                
                You have access to the conversation history and can reference previous interactions.
                If the user has shared personal details in previous messages, you can use this information
                to provide more personalized assistance.
                
                The system will automatically maintain relevant information about the user's preferences
                and needs to ensure continuity across conversations.
            """)
        
        # Create the team with all agents
        team_kwargs = {
            "name": "Financial Modeling Team",
            "members": [
                searcher.agent,
                assumption_generator.agent,
                metrics_deriver.agent,
                modeler.agent
            ],
            "mode": "coordinate",
            "model": create_model(
                provider=body.provider,
                model_id=body.model,
                **model_kwargs
            ),
            "instructions": dedent("""\
                You are a senior financial analyst with over 20 years of experience in investment banking and private equity.
                You hold a Chartered Financial Analyst (CFA) designation and a Chartered Alternative Investment Analyst (CAIA) designation.
                
                ## Your Task
                You are tasked with managing a team to build an institutional-quality, comprehensive financial model for the investment opportunity provided.
                This model must meet the standards of top-tier investment firms like Goldman Sachs, BlackRock, or KKR.
                
                ## ⛔️ MANDATORY CALCULATION DEMONSTRATION ⛔️
                
                You MUST provide a step-by-step demonstration showing EXACTLY how EVERY significant number in your model was calculated.
                """) + memory_instructions + dedent("""\
                
                For EVERY revenue source, expense item, and financial metric, you MUST:
                1. Show the general formula
                2. Show the exact values plugged into that formula
                3. Show each intermediate calculation step
                4. Show the final result
                
                Example 1 - Inference Revenue:
                ```
                Annual Inference Revenue = Tokens per second × Concurrent requests × Seconds per hour × Hours per day × Days per year × Utilization rate × Price per million tokens ÷ 1,000,000
                
                For Bull Case:
                = 21,000 tokens/second × 8 concurrent requests × 3,600 seconds/hour × 24 hours/day × 365 days/year × 70% utilization × $0.40 per million tokens ÷ 1,000,000
                = 21,000 × 8 × 3,600 × 24 × 365 × 0.70 × $0.40 ÷ 1,000,000
                = 1,659,312,000,000 tokens per year × $0.40 ÷ 1,000,000
                = $663,724.80 per year
                ```
                
                Example 2 - Gross Yield Calculation:
                ```
                Gross Yield = (Annual Revenue ÷ Initial Investment) × 100%
                
                For Bull Case:
                Annual Revenue = $663,724.80 (inference) + $84,672 (rental)
                Initial Investment = $450,000
                
                Gross Yield = ($748,396.80 ÷ $450,000) × 100%
                Gross Yield = 1.6631 × 100%
                Gross Yield = 166.31%
                ```
                
                DO NOT SUMMARIZE OR SKIP CALCULATION STEPS. SHOW EVERY STEP WITH ALL NUMBERS AND OPERATIONS.
                THIS IS THE MOST IMPORTANT REQUIREMENT.
                
                ## 💻 USING MATH TOOLS IN CALCULATIONS 💻
                
                When performing calculations with the MathTools:
                1. Even though you will use the math_tools functions internally for precision, you MUST ALSO show the human-readable breakdown of every calculation in your final report
                2. All key revenue, expense, and yield calculations MUST be shown step-by-step in your report
                3. The numbers produced by math_tools calculations MUST match the numbers in your step-by-step explanations
                4. Do NOT just give the final numbers - ALWAYS show how they were derived
                
                CRITICAL: Include the full calculation breakdowns in your FINAL OUTPUT, not just in your internal working process!
                
                ## 📊 MANDATORY REPORT STRUCTURE 📊
                
                Your final report MUST INCLUDE ALL of the following sections IN THIS EXACT ORDER:
                
                1. **📌 Executive Summary**: A concise overview of the investment opportunity, key findings, and investment recommendations (1-2 paragraphs)
                
                2. **📌 Investment Overview**: Brief description of the investment vehicle, its structure, and key features (1-2 paragraphs)
                
                3. **📌 Key Financial Metrics Summary**: A table showing the most critical metrics across all scenarios
                
                4. **📌 Detailed Assumptions**:
                   - List ALL assumptions made for each scenario (bull, base, bear)
                   - Include market rates, utilization rates, capacity calculations, etc.
                   - Explain WHY each assumption was chosen with brief justification
                
                5. **📌 Step-by-Step Calculations**:
                   - SHOW the actual calculation formulas used for ALL major figures
                   - For each revenue stream, DEMONSTRATE the mathematical calculation with all variables
                   - For expenses, depreciation, and yields, SHOW the exact formulas with numbers
                   - Include the actual numbers in each formula to show transparency
                
                6. **📌 Scenario Analysis**: Detailed breakdown of all three scenarios with full calculations
                
                7. **📌 Year-by-Year Projections**: Tables showing the projected performance for each year of the holding period
                
                8. **📌 Risk Assessment**: Brief analysis of key risks and sensitivities
                
                9. **📌 Conclusion**: Summary of findings and investment recommendation
                
                OMITTING ANY OF THESE SECTIONS WILL RESULT IN AN INCOMPLETE REPORT.
                
                ## Your Team
                You have a team of expert specialized agents:
                
                1. **Expert Research Agent**: Has advanced web scraping capabilities to gather accurate market data, industry benchmarks, and comparable investment metrics.
                
                2. **Expert Assumption Generator**: Takes inputs from both the initial request and the Research Agent to generate realistic, defensible assumptions. These assumptions must be:
                   - Grounded in current market realities
                   - Consistent with historical patterns
                   - Reflective of the specific asset class characteristics
                   - Properly cited with sources when possible
                
                3. **Expert Metrics Deriver**: Determines the most relevant financial metrics for the specific investment opportunity and how they should be calculated. This agent ensures:
                   - All metrics are directly relevant to the asset class
                   - Calculations follow industry-standard methodologies
                   - Key metrics are presented across multiple timeframes (annual, cumulative, etc.)
                   - Risk-adjusted returns are properly calculated
                
                4. **Expert Financial Modeler**: Creates detailed financial projections incorporating all inputs. The model must include:
                   - Comprehensive cash flow statements showing all revenue streams and expenses
                   - Realistic capital depreciation schedules
                   - Clear distinction between gross and net yields
                   - Proper time-value adjustments
                   - Sensitivity analyses across different variables
                
                ## Report Structure Requirements
                
                Your final output MUST include the following sections in this order:
                
                1. **Executive Summary**: A concise overview of the investment opportunity, key findings, and investment recommendations (1-2 paragraphs)
                
                2. **Investment Overview**: Brief description of the investment vehicle, its structure, and key features (1-2 paragraphs)
                
                3. **Key Financial Metrics Summary**: A table showing the most critical metrics across all scenarios
                
                4. **Detailed Assumptions**:
                   - List ALL assumptions made for each scenario (bull, base, bear)
                   - Include market rates, utilization rates, capacity calculations, etc.
                   - Explain WHY each assumption was chosen with brief justification
                
                5. **Step-by-Step Calculations**:
                   - SHOW the actual calculation formulas used for ALL major figures
                   - For each revenue stream, DEMONSTRATE the mathematical calculation with all variables
                   - For expenses, depreciation, and yields, SHOW the exact formulas with numbers
                   - Example: "Annual Inference Revenue = Tokens per second × Concurrent requests × Seconds per hour × Hours per day × Days per year × Utilization rate × Price per token"
                   - Include the actual numbers in each formula to show transparency
                
                6. **Scenario Analysis**: Detailed breakdown of all three scenarios with full calculations
                
                7. **Year-by-Year Projections**: Tables showing the projected performance for each year of the holding period
                
                8. **Risk Assessment**: Brief analysis of key risks and sensitivities
                
                9. **Conclusion**: Summary of findings and investment recommendation
                
                ## Critical Requirements for the Output
                
                1. **Calculation Transparency**: You MUST show ALL formulas and calculations used to derive key figures. Do not just present the final numbers - show HOW they were calculated.
                
                2. **Scenario Modeling**: You MUST create three distinct scenarios:
                   - **Bull Case**: Represents optimistic but realistic outcomes (NOT extreme best-case)
                   - **Base Case**: Represents the most likely/expected outcome based on current data
                   - **Bear Case**: Represents challenging conditions that should result in minimal or negative returns
                   
                   The scenarios should show MEANINGFUL differences in outcomes, especially between bull and bear cases.
                
                3. **Yield Calculations**: 
                   - Gross Yield must accurately represent total returns before subtracting expenses
                   - Net Yield must properly account for ALL costs including depreciation, maintenance, and operating expenses
                   - The relationship between gross and net yield must be mathematically consistent and realistic
                   - SHOW the exact calculation for BOTH gross and net yield with the formula and numbers used
                
                4. **Validation Steps**:
                   - Cross-check all calculations for mathematical accuracy
                   - Verify that the model adheres to the specific parameters in the request
                   - Ensure all assumptions are explicitly stated and justified
                   - Confirm that depreciation schedules match the asset type and holding period
                   - Verify that bear case scenarios reflect genuinely challenging conditions (near breakeven or negative returns)
                
                5. **Output Format**:
                   - Present a comprehensive executive summary
                   - Include detailed tables for each scenario
                   - Provide clear year-by-year projections
                   - Highlight key metrics that would most influence an investment decision
                   - Include sensitivity analysis showing how changes in key variables affect outcomes
                   - Use proper markdown formatting for all tables and sections
                   - Make all numbers easy to read with proper comma formatting for thousands
                
                ## Explanation Requirements
                
                1. **Narrative Quality**: Provide clear, professional narrative explanations that an institutional investor would expect
                
                2. **Assumption Justification**: For EACH major assumption, provide a brief justification of why that value was chosen
                
                3. **Calculation Walkthrough**: For each major financial figure, provide the step-by-step calculation that shows exactly how it was derived
                
                4. **Scenario Differences**: Clearly explain what factors drive the differences between scenarios
                
                5. **Investment Thesis**: Provide a clear investment thesis based on the model results
                
                ## Your Workflow
                1. First, ensure you understand the investment opportunity completely
                2. Direct your Research Agent to gather relevant market data
                3. Have your Assumption Generator create properly calibrated assumptions based on the research
                4. Direct your Metrics Deriver to identify and define the critical metrics
                5. Have your Financial Modeler build the comprehensive model
                6. CRITICALLY REVIEW the final output for errors, inconsistencies, or unrealistic projections
                7. If the output fails any validation criteria, require the team to revise their work
                
                ## Quality Control
                The buck stops with you. Your professional reputation depends on producing accurate, realistic, and valuable financial models. 
                If anything seems incorrect, overly optimistic, or mathematically inconsistent, you must address it before presenting the final output.
                
                CRITICAL: Before finalizing any model, verify that:
                1. The model accurately reflects the specific assets, costs, and revenue streams described in the request
                2. The scenarios show meaningful differences with the bear case presenting genuinely challenging conditions
                3. All calculations can be traced and verified
                4. No reinvestment or additional purchases are included unless specifically requested
                5. The time period matches exactly what was requested
                6. ALL calculations are shown with both the formula AND the actual numbers
                
                Remember: Institutional investors rely on your analysis to make multi-million dollar decisions. Accuracy, transparency, and comprehensive detail are paramount.
            """),
            "storage": storage,
            "memory": memory,
            "add_history_to_messages": body.enable_chat_history if memory else False,
            "num_history_responses": body.memory_depth if body.enable_chat_history and memory else 10,
            "read_chat_history": body.enable_chat_history if memory else False,
            "session_id": body.session_id,
            "user_id": body.user_id,
            "add_datetime_to_instructions": True,
            "enable_agentic_context": True,
            "share_member_interactions": True,
            "show_tool_calls": True,
            "markdown": True
        }
        
        # Add MCP tools to the team if available
        if mcp_tools:
            team_kwargs["tools"] = [mcp_tools]
            # Update instructions to include MCP capabilities
            mcp_instructions = "\n\n### MCP Tool Access\n"
            
            if body.use_filesystem_mcp:
                mcp_instructions += dedent("""
                You have access to a filesystem tool that allows you to:
                - Explore directories and list files
                - Read file contents
                - Check file metadata
                
                Use these tools when you need to access or analyze files and directories.
                """)
            
            if body.mcp_servers:
                mcp_instructions += "\nYou also have access to additional MCP tools based on the configuration.\n"
            
            team_kwargs["instructions"] = team_kwargs["instructions"] + mcp_instructions
        
        # Create the team using team_kwargs
        team = Team(**team_kwargs)
        
        message = f"Team created with {len(team.members)} members"
        logger.info(message)
        log_to_memory(message)
        
        message = f"Processing message (length: {len(body.message)})"
        logger.info(message)
        log_to_memory(message)
        
        # Log the input message
        message_preview = body.message[:150] + "..." if len(body.message) > 150 else body.message
        message = f"Input message: {message_preview}"
        logger.info(message)
        log_to_memory(message)

        # Create a streaming wrapper that captures chunks into memory
        async def memory_streaming_wrapper(team, message):
            logger.info("Starting streaming response")
            log_to_memory("Starting streaming response")
            
            run_response = await team.arun(message, stream=True)
            
            chunk_count = 0
            async for chunk in run_response:
                chunk_count += 1
                if chunk_count % 20 == 0:  # Log every 20th chunk to avoid excessive logging
                    debug_message = f"Streaming chunk {chunk_count}: {chunk.content[:50]}..."
                    logger.debug(debug_message)
                    if body.verbose_logging:
                        log_to_memory(debug_message)
                yield chunk.content
            
            complete_message = f"Completed streaming response with {chunk_count} chunks"
            logger.info(complete_message)
            log_to_memory(complete_message)

        if body.stream:
            try:
                message = f"Starting streaming response for request ID: {request_id}"
                logger.info(message)
                log_to_memory(message)
                
                return StreamingResponse(
                    memory_streaming_wrapper(team, body.message),
                    media_type="text/event-stream",
                )
            except Exception as e:
                error_message = f"Error in streaming for request ID {request_id}: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                return JSONResponse(
                    content={"error": f"Streaming error: {str(e)}"},
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        else:
            try:
                message = f"Starting non-streaming response for request ID: {request_id}"
                logger.info(message)
                log_to_memory(message)
                
                response = await team.arun(body.message, stream=False)
                
                complete_message = f"Completed non-streaming response for request ID: {request_id}"
                logger.info(complete_message)
                log_to_memory(complete_message)
                
                return response.content
            except Exception as e:
                error_message = f"Error in non-streaming response for request ID {request_id}: {str(e)}"
                logger.error(error_message)
                log_to_memory(error_message)
                
                return JSONResponse(
                    content={"error": f"Processing error: {str(e)}"},
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR
                )
                
    except ValueError as e:
        # Handle validation errors (e.g., invalid API key format)
        error_message = f"Validation error: {str(e)}"
        logger.warning(error_message)
        log_to_memory(error_message)
        
        return JSONResponse(
            content={"error": f"Validation error: {str(e)}"},
            status_code=HTTPStatus.BAD_REQUEST
        )
    except Exception as e:
        # Handle any other unexpected errors
        error_message = f"Error in run_task: {str(e)}"
        logger.error(error_message)
        log_to_memory(error_message)
        
        return JSONResponse(
            content={"error": "An error occurred while processing the task"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up MCP resources
        if mcp_tools:
            try:
                await mcp_tools.__aexit__(None, None, None)
                logger.info("MCP tools resources cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up MCP tools: {str(e)}")

class APIKeyCheckRequest(BaseModel):
    """Request model for checking API key validity"""
    provider: str
    api_key: str

@task_router.post("/check-api-key", status_code=status.HTTP_200_OK, tags=["Health"])
async def check_api_key(body: APIKeyCheckRequest):
    """
    Check if the provided API key is valid for the specified provider
    """
    try:
        # Create a minimal model to test API key validity
        model = create_model(
            provider=body.provider,
            api_key=body.api_key
        )
        
        # Test a simple query
        test_message = "Hello, are you working?"
        try:
            # Attempt a quick, minimal-token query
            response = await model.aget_completion(test_message, max_tokens=10)
            return {"status": "valid", "provider": body.provider}
        except Exception as e:
            logger.warning(f"API key test failed: {str(e)}")
            return JSONResponse(
                content={"status": "invalid", "provider": body.provider, "error": str(e)},
                status_code=HTTPStatus.BAD_REQUEST
            )
    except Exception as e:
        logger.error(f"Error testing API key: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": f"Could not test API key: {str(e)}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

# Create the FastAPI app
app = FastAPI(
    title="Financial Modeling API",
    description="API for financial modeling using a coordinated team of specialized agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the task router
app.include_router(task_router)

# Add root endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok", 
        "message": "Financial Modeling API is running",
        "supported_providers": ["openai", "anthropic", "formation"],
        "api_version": "1.0.0",
        "features": {
            "knowledge_base": "Supported - allows integration with external knowledge sources via URLs or text",
            "vector_databases": ["lancedb", "pgvector", "pinecone", "cassandra", "chroma", 
                               "clickhouse", "milvus", "mongodb", "qdrant", "singlestore", "weaviate"],
            "embedding_providers": ["openai", "cohere"],
            "chunking_strategies": ["fixed", "agentic", "semantic", "recursive", "document"],
            "storage": {
                "supported": True,
                "backends": ["sqlite", "postgres", "mongodb", "dynamodb", "json", "yaml"],
                "features": ["session_persistence", "user_personalization"]
            }
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Check system health, including model provider availability
    """
    try:
        # This is a simple system health check
        # We're not checking model provider availability here as that requires API keys
        return {
            "status": "healthy",
            "api": "operational",
            "timestamp": datetime.datetime.now().isoformat(),
            "providers": {
                "openai": "requires_api_key",
                "anthropic": "requires_api_key",
                "formation": "requires_api_key"
            },
            "message": "Use the /task/check-api-key endpoint to verify specific provider API keys"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}"
            },
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )

# Run the server when executed directly
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
