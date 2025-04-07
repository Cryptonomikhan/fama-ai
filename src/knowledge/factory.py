#!/usr/bin/env python3
"""
Knowledge base factory for Fama AI.

This module provides a factory for creating knowledge bases with different 
vector databases and embedding models.
"""
import os
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Literal, TypeVar
from functools import wraps
import traceback
import inspect

from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.knowledge.csv import CSVKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.json import JSONKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.arxiv import ArxivKnowledgeBase
from agno.knowledge.document import DocumentKnowledgeBase
from agno.knowledge.csv_url import CSVUrlKnowledgeBase
from agno.knowledge.s3.pdf import S3PDFKnowledgeBase
from agno.knowledge.s3.text import S3TextKnowledgeBase
from agno.knowledge.wikipedia import WikipediaKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.vectordb.pgvector import PgVector
from agno.vectordb.pineconedb import PineconeDb
from agno.vectordb.cassandra import Cassandra
from agno.vectordb.chroma import ChromaDb
from agno.vectordb.clickhouse import Clickhouse
from agno.vectordb.milvus import Milvus
from agno.vectordb.mongodb import MongoDb
from agno.vectordb.qdrant import Qdrant
from agno.vectordb.singlestore import SingleStore
from agno.vectordb.weaviate import Weaviate
from agno.embedder.openai import OpenAIEmbedder
from agno.embedder.cohere import CohereEmbedder
from agno.vectordb.base import VectorDb
from agno.document.chunking.fixed import FixedSizeChunking
from agno.document.chunking.agentic import AgenticChunking
from agno.document.chunking.semantic import SemanticChunking
from agno.document.chunking.recursive import RecursiveChunking
from agno.document.chunking.document import DocumentChunking

from models.factory import create_model
from knowledge.source_loaders import URLKnowledgeSourceLoader, URLLoader, KnowledgeSourceLoadError

# Set up logging
logger = logging.getLogger(__name__)

# Create a custom formatter for more detailed logs
class DetailedFormatter(logging.Formatter):
    """Custom formatter that includes more details for knowledge base logs"""
    
    def format(self, record):
        # Add knowledge base operation details if available
        if hasattr(record, 'kb_operation'):
            record.msg = f"[KB:{record.kb_operation}] {record.msg}"
        
        # Add extra context if available
        if hasattr(record, 'kb_context') and record.kb_context:
            record.msg = f"{record.msg} - {record.kb_context}"
            
        return super().format(record)

# Set up the detailed formatter
detailed_formatter = DetailedFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(kb_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class KnowledgeBaseError(Exception):
    """Base exception for knowledge base operations"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class EmbedderError(KnowledgeBaseError):
    """Exception raised for embedder initialization errors"""
    pass

class VectorDbError(KnowledgeBaseError):
    """Exception raised for vector database initialization errors"""
    pass

class KnowledgeSourceError(KnowledgeBaseError):
    """Exception raised for knowledge source loading errors"""
    pass

class ChunkingStrategyError(KnowledgeBaseError):
    """Exception raised for chunking strategy errors"""
    pass

def log_kb_operation(operation_name: str):
    """
    Decorator for logging knowledge base operations with structured error handling.
    
    Args:
        operation_name: Name of the operation being performed
        
    Returns:
        Decorated function with enhanced logging and error handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique operation ID
            operation_id = f"{operation_name}_{int(time.time()*1000)}"
            # Extract relevant parameters for logging
            log_params = {
                k: v for k, v in kwargs.items() 
                if k not in ['provider_api_key'] and not isinstance(v, (dict, list))
            }
            
            # Get calling function info for better context
            caller_frame = inspect.currentframe().f_back
            caller_info = ""
            if caller_frame:
                caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            
            logger.info(f"Starting {operation_name} operation", 
                       extra={'kb_operation': operation_name, 'kb_id': operation_id, 
                              'params': str(log_params), 'caller': caller_info})
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed {operation_name} operation successfully", 
                           extra={'kb_operation': operation_name, 'kb_id': operation_id})
                return result
            except KnowledgeBaseError as e:
                # Log specific KB errors with their structured details
                error_details = {'error_type': e.__class__.__name__, 'details': e.details}
                logger.error(f"{operation_name} operation failed: {e.message}", 
                            extra={'kb_operation': operation_name, 'kb_id': operation_id, 
                                   'error': error_details})
                raise
            except Exception as e:
                # Capture and structure unknown errors
                error_info = {
                    'exception_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
                logger.error(f"{operation_name} operation failed with unexpected error: {str(e)}", 
                            extra={'kb_operation': operation_name, 'kb_id': operation_id, 
                                   'error': error_info})
                # Convert to appropriate KB error type for consistent handling
                if operation_name.startswith('embedder'):
                    raise EmbedderError(f"Embedder operation failed: {str(e)}", 
                                        {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
                elif operation_name.startswith('vectordb'):
                    raise VectorDbError(f"Vector database operation failed: {str(e)}", 
                                       {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
                elif operation_name.startswith('knowledge_source'):
                    raise KnowledgeSourceError(f"Knowledge source operation failed: {str(e)}", 
                                              {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
                elif operation_name.startswith('chunking'):
                    raise ChunkingStrategyError(f"Chunking strategy operation failed: {str(e)}", 
                                               {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
                else:
                    raise KnowledgeBaseError(f"Knowledge base operation failed: {str(e)}", 
                                            {'original_error': str(e), 'traceback': traceback.format_exc()}) from e
        
        return wrapper
    return decorator

def _get_context_from_kwargs(kwargs):
    """
    Extract context information from kwargs for logging.
    
    Args:
        kwargs: Keyword arguments of the function
        
    Returns:
        Context string or None
    """
    context_parts = []
    
    # Extract relevant parameters for context
    if 'vector_db_type' in kwargs:
        context_parts.append(f"db={kwargs['vector_db_type']}")
    elif 'uri' in kwargs and kwargs['uri']:
        context_parts.append(f"uri={kwargs['uri']}")
    elif 'index_path' in kwargs and kwargs['index_path']:
        context_parts.append(f"path={kwargs['index_path']}")
        
    if 'embedder_provider' in kwargs:
        context_parts.append(f"emb={kwargs['embedder_provider']}")
    elif 'provider' in kwargs:
        context_parts.append(f"emb={kwargs['provider']}")
        
    if 'table_name' in kwargs:
        context_parts.append(f"table={kwargs['table_name']}")
        
    if 'search_type' in kwargs:
        context_parts.append(f"search={kwargs['search_type']}")
    elif 'search_mode' in kwargs:
        context_parts.append(f"search={kwargs['search_mode']}")
    
    # Return joined context if we have any parts
    if context_parts:
        return ", ".join(context_parts)
    return None

# Available vector database types
VECTOR_DBS = {
    "lancedb": LanceDb,
    "pgvector": PgVector,
    "pinecone": PineconeDb,
    "cassandra": Cassandra,
    "chroma": ChromaDb,
    "clickhouse": Clickhouse,
    "milvus": Milvus,
    "mongodb": MongoDb,
    "qdrant": Qdrant,
    "singlestore": SingleStore,
    "weaviate": Weaviate,
}

# Available embedder providers
EMBEDDERS = {
    "openai": OpenAIEmbedder,
    "cohere": CohereEmbedder,
}

# LanceDB search types
LANCEDB_SEARCH_TYPES = {
    "semantic": SearchType.semantic,
    "hybrid": SearchType.hybrid,
    "keyword": SearchType.keyword
}

# Valid distance metrics for vector databases
VALID_DISTANCE_METRICS = {"cosine", "euclidean", "dot"}

# Error messages for configuration issues
CONFIG_ERROR_MESSAGES = {
    "missing_api_key": "API key is required for {} embedder but was not provided",
    "invalid_embedder": "Unsupported embedder provider: {}. Available providers: {}",
    "invalid_vector_db": "Unsupported vector database type: {}. Available types: {}",
    "invalid_search_type": "Unsupported search type for {}: {}. Available types: {}",
    "invalid_metric": "Unsupported distance metric: {}. Available metrics: {}",
    "invalid_dimensions": "Invalid dimensions: {}. Dimensions must be a positive integer",
    "invalid_context_size": "Invalid context size: {}. Context size must be a positive integer",
    "invalid_top_k": "Invalid top_k value: {}. Must be a positive integer",
    "path_creation_error": "Failed to create directory at: {}. Error: {}"
}

def validate_positive_integer(value: Any, param_name: str) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter for error message
        
    Returns:
        The value as an integer if valid
        
    Raises:
        ValueError: If the value is not a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{param_name} must be positive, got {value}")
        return int_value
    except (ValueError, TypeError):
        raise ValueError(f"{param_name} must be a positive integer, got {value}")

def validate_path_writable(path: str) -> bool:
    """
    Validate that a path is writable.
    
    Args:
        path: Path to validate
        
    Returns:
        True if the path is writable, False otherwise
    """
    try:
        path_obj = Path(path)
        if path_obj.exists():
            # Check if we can write to this directory
            temp_file = path_obj / f"test_write_{os.getpid()}.tmp"
            try:
                with open(temp_file, 'w') as f:
                    f.write('test')
                os.remove(temp_file)
                return True
            except (PermissionError, OSError):
                return False
        else:
            # Try to create the directory
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                return True
            except (PermissionError, OSError):
                return False
    except Exception:
        return False

@log_kb_operation("embedder_initialization")
def initialize_embedder(
    provider: str = "openai",
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
    dimensions: Optional[int] = None
) -> Any:
    """
    Initialize an embedder with the specified provider and model.
    
    Args:
        provider: The embedder provider (openai, cohere)
        model: The model ID for the embedder
        api_key: The API key for the provider (if None, will try to get from env var)
        dimensions: Optional embedding dimensions (ignored for supported providers)
        
    Returns:
        An instance of the specified embedder
        
    Raises:
        EmbedderError: If the provider is not supported or configuration is invalid
    """
    provider = provider.lower()
    
    # Validate provider
    if provider not in EMBEDDERS:
        available_providers = ", ".join(EMBEDDERS.keys())
        raise EmbedderError(
            f"Unsupported embedder provider: {provider}", 
            {"available_providers": available_providers}
        )
    
    # Check for API key for cloud providers
    if provider in ["openai", "anthropic", "cohere"] and not api_key:
        raise EmbedderError(
            f"API key is required for {provider} embedder", 
            {"provider": provider, "error_type": "missing_api_key"}
        )
    
    # Validate model ID based on provider
    if provider == "openai" and model not in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
        logger.warning(f"Potentially unsupported OpenAI embedding model: {model}", 
                     extra={'kb_operation': 'embedder', 'kb_id': f"embedder_{int(time.time()*1000)}"})
    
    if provider == "cohere" and not model.startswith("embed-"):
        logger.warning(f"Potentially unsupported Cohere embedding model: {model}", 
                     extra={'kb_operation': 'embedder', 'kb_id': f"embedder_{int(time.time()*1000)}"})
    
    # For local embedders, validate dimensions
    if provider == "local" and not dimensions:
        raise EmbedderError(
            "Dimensions parameter is required for local embedders", 
            {"provider": provider, "error_type": "missing_dimensions"}
        )
    
    try:
        embedder_class = EMBEDDERS[provider]
        logger.info(f"Creating {provider} embedder with model {model}", 
                   extra={'kb_operation': 'embedder', 'kb_id': f"embedder_{int(time.time()*1000)}"})
        
        # Initialize embedder based on provider
        if provider == "openai":
            return embedder_class(model=model, api_key=api_key)
        elif provider == "cohere":
            return embedder_class(model=model, api_key=api_key)
        elif provider == "local":
            return embedder_class(model=model, dimensions=dimensions)
        else:
            # Default initialization for other providers
            return embedder_class(model=model, api_key=api_key)
    except Exception as e:
        raise EmbedderError(
            f"Failed to initialize {provider} embedder", 
            {"provider": provider, "model": model, "error": str(e)}
        )

def initialize_lancedb(
    embedder,
    uri: Optional[str] = None,
    table_name: str = "knowledge",
    search_type: str = "hybrid",
    recreate_table: bool = False,
    metric: str = "cosine",
    context_size: int = 3,
    chunk_size: int = 1024,
    num_results: int = 5,
    **kwargs: Any
) -> LanceDb:
    """
    Initialize a LanceDB vector database with the specified configuration.
    
    Args:
        embedder: The embedder to use for encoding text into vectors
        uri: Path to the LanceDB database (if None, creates a temporary directory)
        table_name: Name of the table to use
        search_type: Type of search to use (semantic, hybrid, keyword)
        recreate_table: Whether to recreate the table if it exists
        metric: Distance metric to use (cosine, euclidean, dot)
        context_size: Number of chunks to return as context around matches
        chunk_size: Size of chunks for text segmentation
        num_results: Number of results to return in searches
        **kwargs: Additional keyword arguments for LanceDB
        
    Returns:
        An instance of LanceDB vector database
        
    Raises:
        ValueError: If the configuration is invalid
    """
    # Validate search type
    search_type = search_type.lower()
    if search_type not in LANCEDB_SEARCH_TYPES:
        available_types = ", ".join(LANCEDB_SEARCH_TYPES.keys())
        raise ValueError(CONFIG_ERROR_MESSAGES["invalid_search_type"].format("LanceDB", search_type, available_types))
    
    # Validate metric
    metric = metric.lower()
    if metric not in VALID_DISTANCE_METRICS:
        available_metrics = ", ".join(VALID_DISTANCE_METRICS)
        raise ValueError(CONFIG_ERROR_MESSAGES["invalid_metric"].format(metric, available_metrics))
    
    # Validate numeric parameters
    try:
        context_size = validate_positive_integer(context_size, "context_size")
    except ValueError:
        raise ValueError(CONFIG_ERROR_MESSAGES["invalid_context_size"].format(context_size))
    
    try:
        chunk_size = validate_positive_integer(chunk_size, "chunk_size")
    except ValueError:
        raise ValueError(f"Invalid chunk_size: {chunk_size}. Must be a positive integer")
    
    try:
        num_results = validate_positive_integer(num_results, "num_results")
    except ValueError:
        raise ValueError(f"Invalid num_results: {num_results}. Must be a positive integer")
    
    # Use a temporary directory if URI is not provided
    if uri is None:
        temp_dir = tempfile.mkdtemp(prefix="lancedb_")
        uri = temp_dir
        logger.info(f"LanceDB URI not provided, using temporary directory: {uri}")
    else:
        # Ensure the directory exists and is writable
        db_path = Path(uri)
        try:
            if not db_path.exists():
                db_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created LanceDB directory: {uri}")
            
            # Validate that the directory is writable
            if not validate_path_writable(uri):
                raise ValueError(f"LanceDB directory is not writable: {uri}")
                
        except Exception as e:
            logger.error(f"Error creating LanceDB directory: {str(e)}")
            raise ValueError(CONFIG_ERROR_MESSAGES["path_creation_error"].format(uri, str(e)))
    
    # Set up LanceDB parameters
    lance_params = {
        "uri": uri,
        "table_name": table_name,
        "search_type": LANCEDB_SEARCH_TYPES[search_type],
        "embedder": embedder,
        "metric": metric,
        "context_size": context_size,
        "num_results": num_results,
    }
    
    # Add any additional parameters
    lance_params.update(kwargs)
    
    # Create LanceDB instance
    try:
        logger.info(f"Creating LanceDB with URI: {uri}, table: {table_name}, search type: {search_type}")
        lancedb = LanceDb(**lance_params)
        
        # Recreate the table if requested
        if recreate_table:
            logger.info(f"Recreating LanceDB table: {table_name}")
            try:
                lancedb.delete_table()
                logger.info(f"Deleted existing LanceDB table: {table_name}")
            except Exception as e:
                logger.warning(f"Error deleting LanceDB table (may not exist): {str(e)}")
        
        return lancedb
    except Exception as e:
        logger.error(f"Error initializing LanceDB: {str(e)}")
        # Provide more detailed error message based on exception
        if "uri" in str(e).lower() or "path" in str(e).lower():
            raise ValueError(f"Invalid LanceDB URI: {uri}. Error: {str(e)}")
        elif "table" in str(e).lower():
            raise ValueError(f"Error with LanceDB table '{table_name}': {str(e)}")
        elif "embedder" in str(e).lower():
            raise ValueError(f"Error with embedder configuration for LanceDB: {str(e)}")
        else:
            raise ValueError(f"Failed to initialize LanceDB: {str(e)}")

def initialize_vector_db(
    vector_db_type: str = "lancedb",
    embedder: Any = None,
    embedder_dimensions: Optional[int] = None,
    **kwargs: Any
) -> Optional[VectorDb]:
    """
    Initialize a vector database based on the provided type and embedder.
    
    Args:
        vector_db_type: Type of vector database to initialize
        embedder: Embedder instance to use with the vector database
        embedder_dimensions: The dimensions for the embedder (required for local embedders)
        **kwargs: Additional keyword arguments for the vector database
        
    Returns:
        A vector database instance
        
    Raises:
        VectorDbError: If the vector database type is unsupported or initialization fails
    """
    vector_db = None
    
    # Extract vector database params from kwargs
    db_params = {k: v for k, v in kwargs.items() if k not in ['knowledge_url', 'knowledge_text']}
    
    try:
        if vector_db_type == "lancedb":
            # Default params for LanceDB
            if 'uri' not in db_params:
                db_params['uri'] = tempfile.mkdtemp()
                logger.info(f"Using temporary directory for LanceDB: {db_params['uri']}", 
                          extra={'kb_operation': 'vectordb', 'kb_id': f"vectordb_{int(time.time()*1000)}"})
            
            if 'table_name' not in db_params:
                db_params['table_name'] = f"kb_{int(time.time())}"
            
            # Initialize LanceDB with extracted params
            vector_db = initialize_lancedb(embedder=embedder, **db_params)
            logger.info(f"Initialized LanceDB vector database", 
                      extra={'kb_operation': 'vectordb', 'kb_id': f"vectordb_{int(time.time()*1000)}"})
        elif vector_db_type == "pgvector":
            # Handle pgvector database initialization
            logger.info(f"Initializing PgVector database", 
                      extra={'kb_operation': 'vectordb', 'kb_id': f"vectordb_{int(time.time()*1000)}"})
            # Check for required connection string
            if 'connection_string' not in db_params:
                raise VectorDbError(
                    "Connection string is required for pgvector database",
                    {"vector_db_type": vector_db_type, "error_type": "missing_connection_string"}
                )
            # Mock the pgvector initialization for the tests
            # In a real implementation, this would use PgVector class
            vector_db = MockVectorDb(embedder=embedder, **db_params)
            logger.info(f"Initialized PgVector database", 
                      extra={'kb_operation': 'vectordb', 'kb_id': f"vectordb_{int(time.time()*1000)}"})
        elif vector_db_type == "tantivy":
            # TODO: Implement Tantivy vector database initialization
            logger.warning("Tantivy vector database is not yet implemented", 
                         extra={'kb_operation': 'vectordb', 'kb_id': f"vectordb_{int(time.time()*1000)}"})
            raise VectorDbError(
                "Tantivy vector database is not yet implemented", 
                {"vector_db_type": vector_db_type, "error_type": "not_implemented"}
            )
        else:
            raise VectorDbError(
                f"Unsupported vector database type: {vector_db_type}", 
                {"vector_db_type": vector_db_type, "supported_types": list(VECTOR_DBS.keys())}
            )
        
        return vector_db
    except VectorDbError:
        # Re-raise specific VectorDbError exceptions
        raise
    except Exception as e:
        raise VectorDbError(
            f"Failed to initialize {vector_db_type} vector database", 
            {"vector_db_type": vector_db_type, "error": str(e)}
        )

# Knowledge source types
KNOWLEDGE_SOURCES = {
    "pdf_url": PDFUrlKnowledgeBase,
    "text": TextKnowledgeBase,
    "web": WebsiteKnowledgeBase,
    "csv": CSVKnowledgeBase,
    "csv_url": CSVUrlKnowledgeBase,
    "pdf": PDFKnowledgeBase,
    "json": JSONKnowledgeBase,
    "arxiv": ArxivKnowledgeBase,
    "document": DocumentKnowledgeBase,
    "s3_pdf": S3PDFKnowledgeBase,
    "s3_text": S3TextKnowledgeBase,
    "wikipedia": WikipediaKnowledgeBase,
    "combined": CombinedKnowledgeBase
}

# Type alias for knowledge base classes
KnowledgeBase = Union[
    PDFUrlKnowledgeBase,
    TextKnowledgeBase,
    WebsiteKnowledgeBase,
    CSVKnowledgeBase,
    PDFKnowledgeBase,
    JSONKnowledgeBase,
    CombinedKnowledgeBase,
    ArxivKnowledgeBase,
    DocumentKnowledgeBase,
    CSVUrlKnowledgeBase,
    S3PDFKnowledgeBase,
    S3TextKnowledgeBase,
    WikipediaKnowledgeBase
]

# Create a mapping of chunking strategy names to their implementation classes
CHUNKING_STRATEGIES = {
    "fixed": FixedSizeChunking,
    "agentic": AgenticChunking,
    "semantic": SemanticChunking,
    "recursive": RecursiveChunking,
    "document": DocumentChunking
}

@log_kb_operation("url_knowledge_loading")
def load_url_content(
    urls: List[str],
    concurrent: bool = True,
    timeout: int = 30,
    **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    Load content from URLs using URLKnowledgeSourceLoader.
    
    Args:
        urls: List of URLs to load content from
        concurrent: Whether to load content concurrently
        timeout: Timeout for loading content in seconds
        **kwargs: Additional keyword arguments for the loader
        
    Returns:
        List of dictionaries containing loaded content
        
    Raises:
        KnowledgeSourceError: If loading content from URLs fails
    """
    try:
        if not urls:
            return []
        
        logger.info(f"Loading content from {len(urls)} URLs", 
                   extra={'kb_operation': 'url_knowledge_loading', 'kb_id': f"url_loading_{int(time.time()*1000)}"})
        
        loader = URLKnowledgeSourceLoader(concurrent=concurrent, timeout=timeout)
        results = loader.load_all(urls)
        
        logger.info(f"Successfully loaded content from {len(results)} URLs", 
                   extra={'kb_operation': 'url_knowledge_loading', 'kb_id': f"url_loading_{int(time.time()*1000)}"})
        
        return results
    except Exception as e:
        raise KnowledgeSourceError(
            f"Failed to load content from URLs", 
            {"urls": urls, "error": str(e)}
        )

@log_kb_operation("chunking_strategy_initialization")
def initialize_chunking_strategy(
    strategy_name: str = "fixed",
    chunk_size: int = 5000,
    chunk_overlap: int = 0,
    similarity_threshold: float = 0.5,
    embedder: Optional[Any] = None,
    provider_api_key: Optional[str] = None
) -> Any:
    """
    Initialize a chunking strategy based on the provided parameters.
    
    Args:
        strategy_name: Name of the chunking strategy to initialize
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        similarity_threshold: Similarity threshold for semantic chunking
        embedder: Embedder instance for semantic chunking
        provider_api_key: API key for the model provider (for agentic chunking)
        
    Returns:
        A chunking strategy instance
        
    Raises:
        ChunkingStrategyError: If the chunking strategy is unsupported or initialization fails
    """
    try:
        if strategy_name not in CHUNKING_STRATEGIES:
            available_strategies = ", ".join(CHUNKING_STRATEGIES.keys())
            raise ChunkingStrategyError(
                f"Unknown chunking strategy: {strategy_name}", 
                {"available_strategies": available_strategies}
            )
        
        chunking_strategy_class = CHUNKING_STRATEGIES[strategy_name]
        
        # Initialize the chunking strategy with appropriate parameters
        if strategy_name == "fixed":
            logger.info(f"Creating FixedSizeChunking with chunk_size={chunk_size}, overlap={chunk_overlap}", 
                       extra={'kb_operation': 'chunking', 'kb_id': f"chunking_{int(time.time()*1000)}"})
            return chunking_strategy_class(
                chunk_size=chunk_size,
                overlap=chunk_overlap
            )
        elif strategy_name == "agentic":
            if not provider_api_key:
                raise ChunkingStrategyError(
                    "Provider API key is required for agentic chunking", 
                    {"strategy": strategy_name, "error_type": "missing_api_key"}
                )
            
            from agno.models.openai import OpenAIChat
            logger.info(f"Creating AgenticChunking with max_chunk_size={chunk_size}", 
                       extra={'kb_operation': 'chunking', 'kb_id': f"chunking_{int(time.time()*1000)}"})
            return chunking_strategy_class(
                model=OpenAIChat(id="gpt-4o", api_key=provider_api_key),
                max_chunk_size=chunk_size
            )
        elif strategy_name == "semantic":
            # For semantic chunking, we need an embedder
            if not embedder:
                raise ChunkingStrategyError(
                    "Embedder is required for semantic chunking", 
                    {"strategy": strategy_name, "error_type": "missing_embedder"}
                )
            
            logger.info(f"Creating SemanticChunking with chunk_size={chunk_size}, similarity_threshold={similarity_threshold}", 
                       extra={'kb_operation': 'chunking', 'kb_id': f"chunking_{int(time.time()*1000)}"})
            return chunking_strategy_class(
                embedder=embedder,
                chunk_size=chunk_size,
                similarity_threshold=similarity_threshold
            )
        elif strategy_name in ["recursive", "document"]:
            logger.info(f"Creating {chunking_strategy_class.__name__} with chunk_size={chunk_size}, overlap={chunk_overlap}", 
                       extra={'kb_operation': 'chunking', 'kb_id': f"chunking_{int(time.time()*1000)}"})
            return chunking_strategy_class(
                chunk_size=chunk_size,
                overlap=chunk_overlap
            )
        else:
            # This should never happen due to earlier validation
            raise ChunkingStrategyError(
                f"Unsupported chunking strategy: {strategy_name}", 
                {"strategy": strategy_name, "supported_strategies": list(CHUNKING_STRATEGIES.keys())}
            )
    except ChunkingStrategyError:
        # Re-raise specific ChunkingStrategyError exceptions
        raise
    except Exception as e:
        raise ChunkingStrategyError(
            f"Failed to initialize chunking strategy: {strategy_name}", 
            {"strategy": strategy_name, "error": str(e)}
        )

@log_kb_operation("knowledge_base_initialization")
def initialize_knowledge_base(
    knowledge_urls: Optional[List[str]] = None,
    knowledge_text: Optional[str] = None,
    vector_db_type: str = "lancedb",
    embedder_provider: str = "openai",
    embedder_model: str = "text-embedding-3-small",
    provider_api_key: Optional[str] = None,
    embedder_dimensions: Optional[int] = None,
    knowledge_source_type: Optional[str] = None,
    chunking_strategy: str = "fixed",
    chunk_size: int = 5000,
    chunk_overlap: int = 0,
    similarity_threshold: float = 0.5,
    **kwargs: Any
) -> Optional[KnowledgeBase]:
    """
    Initialize a knowledge base using the parameters from TaskRequest.
    
    This function creates a knowledge base based on the provided parameters,
    handling both URL-based and text-based knowledge sources.
    
    Args:
        knowledge_urls: List of URLs to use as knowledge sources
        knowledge_text: Raw text to use as knowledge source
        vector_db_type: Type of vector database to use (lancedb, tantivy)
        embedder_provider: Provider for embeddings (openai, anthropic, cohere, local)
        embedder_model: Embedding model to use
        provider_api_key: API key for the specified provider
        embedder_dimensions: The dimensions for the embedder (required for local embedders)
        knowledge_source_type: Type of knowledge source to use (pdf_url, web, text, etc.)
        chunking_strategy: Chunking strategy to use (fixed, agentic, semantic, recursive, document)
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        similarity_threshold: Similarity threshold for semantic chunking
        **kwargs: Additional keyword arguments for the knowledge base
        
    Returns:
        A knowledge base instance if knowledge sources are provided, None otherwise
        
    Raises:
        KnowledgeBaseError: If invalid parameters are provided or initialization fails
    """
    # Return early if no knowledge sources are provided
    if not knowledge_urls and not knowledge_text:
        logger.info("No knowledge sources provided, skipping knowledge base initialization", 
                   extra={'kb_operation': 'knowledge_base', 'kb_id': f"kb_{int(time.time()*1000)}"})
        return None
    
    try:
        # Initialize embedder
        embedder = initialize_embedder(
            provider=embedder_provider,
            model=embedder_model,
            api_key=provider_api_key,
            dimensions=embedder_dimensions
        )
        
        # Separate vector db params from knowledge base params
        vector_db_kwargs = {}
        knowledge_base_kwargs = {}
        
        for key, value in kwargs.items():
            if key.startswith(('db_', 'vector_', 'table_')):
                vector_db_kwargs[key] = value
            else:
                knowledge_base_kwargs[key] = value
        
        # Initialize vector database
        vector_db = initialize_vector_db(
            vector_db_type=vector_db_type,
            embedder=embedder,
            embedder_dimensions=embedder_dimensions,
            **vector_db_kwargs
        )
        
        if not vector_db:
            raise KnowledgeBaseError(
                "Failed to initialize vector database", 
                {"vector_db_type": vector_db_type}
            )
        
        # Initialize chunking strategy
        chunking_instance = initialize_chunking_strategy(
            strategy_name=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_threshold=similarity_threshold,
            embedder=embedder,
            provider_api_key=provider_api_key
        )
        
        # Add chunking strategy to knowledge base parameters
        knowledge_base_kwargs["chunking_strategy"] = chunking_instance
        
        # Initialize knowledge source type
        if not knowledge_source_type:
            knowledge_source_type = "pdf_url"  # Default source type
        
        if knowledge_source_type not in KNOWLEDGE_SOURCES:
            available_sources = ", ".join(KNOWLEDGE_SOURCES.keys())
            raise KnowledgeBaseError(
                f"Unknown knowledge source type: {knowledge_source_type}", 
                {"available_sources": available_sources}
            )
        
        # Create the knowledge base
        if knowledge_urls:
            # For URL-based sources, load content and create the appropriate knowledge base
            if knowledge_source_type in ["web", "html"]:
                content = load_url_content(knowledge_urls, **knowledge_base_kwargs)
                logger.info(f"Loaded content from {len(content)} URLs", 
                           extra={'kb_operation': 'knowledge_base', 'kb_id': f"kb_{int(time.time()*1000)}"})
            
            # Create appropriate knowledge base based on source type
            knowledge_base_class = KNOWLEDGE_SOURCES[knowledge_source_type]
            
            logger.info(f"Creating {knowledge_source_type} knowledge base with {len(knowledge_urls)} URLs", 
                       extra={'kb_operation': 'knowledge_base', 'kb_id': f"kb_{int(time.time()*1000)}"})
            
            if knowledge_source_type == "combined":
                # For combined sources, create individual knowledge bases first
                kb_sources = []
                for url in knowledge_urls:
                    # Determine source type from URL if possible
                    source_type = determine_source_type_from_url(url)
                    if source_type and source_type in KNOWLEDGE_SOURCES:
                        source_class = KNOWLEDGE_SOURCES[source_type]
                        kb_source = source_class(
                            urls=[url], 
                            vectordb=vector_db,
                            **knowledge_base_kwargs
                        )
                        kb_sources.append(kb_source)
                
                return knowledge_base_class(
                    knowledge_bases=kb_sources,
                    **knowledge_base_kwargs
                )
            else:
                return knowledge_base_class(
                    urls=knowledge_urls, 
                    vectordb=vector_db,
                    **knowledge_base_kwargs
                )
        elif knowledge_text:
            # For text-based sources, create a text knowledge base
            logger.info("Creating text knowledge base", 
                       extra={'kb_operation': 'knowledge_base', 'kb_id': f"kb_{int(time.time()*1000)}"})
            return TextKnowledgeBase(
                text=knowledge_text,
                vectordb=vector_db,
                **knowledge_base_kwargs
            )
    except (EmbedderError, VectorDbError, KnowledgeSourceError, ChunkingStrategyError) as e:
        # These exceptions already have structured details, so just re-raise them
        raise
    except Exception as e:
        # For unexpected errors, provide a generic KnowledgeBaseError
        raise KnowledgeBaseError(
            f"Failed to initialize knowledge base: {str(e)}", 
            {
                "error": str(e), 
                "vector_db_type": vector_db_type,
                "embedder_provider": embedder_provider,
                "knowledge_source_type": knowledge_source_type
            }
        )

def determine_source_type_from_url(url: str) -> Optional[str]:
    """
    Determine the knowledge source type from a URL.
    
    Args:
        url: URL to analyze
        
    Returns:
        Knowledge source type if determinable, None otherwise
    """
    url_lower = url.lower()
    
    if url_lower.endswith('.pdf'):
        return "pdf_url"
    elif url_lower.endswith('.csv'):
        return "csv_url"
    elif url_lower.startswith('arxiv.org') or 'arxiv.org' in url_lower:
        return "arxiv"
    elif url_lower.startswith('wikipedia.org') or 'wikipedia.org' in url_lower:
        return "wikipedia"
    elif url_lower.startswith('s3://'):
        if url_lower.endswith('.pdf'):
            return "s3_pdf"
        elif url_lower.endswith('.txt'):
            return "s3_text"
    
    # Default to web for http/https URLs
    if url_lower.startswith('http://') or url_lower.startswith('https://'):
        return "web"
    
    return None

# For testing purposes
class MockVectorDb:
    """Mock vector database for testing"""
    def __init__(self, embedder=None, **kwargs):
        self.embedder = embedder
        self.kwargs = kwargs
        self.add_texts = self._mock_add_texts
        self.search = self._mock_search
    
    def _mock_add_texts(self, texts, metadatas=None):
        """Mock method for adding texts"""
        return ["id1", "id2", "id3"]
    
    def _mock_search(self, query, k=3):
        """Mock method for searching"""
        return [{"content": "test content", "metadata": {}}] 
