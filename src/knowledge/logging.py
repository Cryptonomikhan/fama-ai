#!/usr/bin/env python3
"""
Knowledge base logging utilities for Fama AI.

This module provides specialized logging utilities for tracking knowledge base
usage, queries, and retrievals across the system.
"""
import logging
import time
import uuid
import datetime
import json
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

# Set up a dedicated logger for knowledge base operations
logger = logging.getLogger("fama.knowledge")
kb_handler = logging.StreamHandler()
kb_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [KB:%(kb_operation)s] [ID:%(kb_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
kb_handler.setFormatter(kb_formatter)
logger.addHandler(kb_handler)
logger.propagate = True  # Also send logs to root logger

# In-memory storage for recent knowledge operation logs
# Limited to prevent memory issues
MAX_MEMORY_LOGS = 1000
kb_operation_logs = []

def get_knowledge_logs(limit: int = 100, operation_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve knowledge operation logs from memory.
    
    Args:
        limit: Maximum number of logs to return
        operation_type: Filter logs by operation type (query, retrieval, etc.)
        
    Returns:
        List of log entries as dictionaries
    """
    if operation_type:
        filtered_logs = [log for log in kb_operation_logs if log.get('operation') == operation_type]
        return filtered_logs[-limit:]
    return kb_operation_logs[-limit:]

def log_kb_operation(log_dict: Dict[str, Any]):
    """
    Add a log entry to the in-memory log storage.
    
    Args:
        log_dict: Dictionary with log data
    """
    # Add timestamp if not present
    if 'timestamp' not in log_dict:
        log_dict['timestamp'] = datetime.datetime.now().isoformat()
    
    # Add to in-memory logs
    kb_operation_logs.append(log_dict)
    
    # Trim if needed
    if len(kb_operation_logs) > MAX_MEMORY_LOGS:
        del kb_operation_logs[0]

class KnowledgeLogger:
    """
    Logger for knowledge base operations with context tracking.
    """
    
    def __init__(self, agent_name: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize a knowledge logger.
        
        Args:
            agent_name: Name of the agent using this logger
            session_id: Session ID for grouping related operations
        """
        self.agent_name = agent_name
        self.session_id = session_id or str(uuid.uuid4())
        self.operation_count = 0
    
    def log_query(self, query_text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a knowledge base query.
        
        Args:
            query_text: The query text
            metadata: Additional metadata about the query
            
        Returns:
            Query ID for tracking
        """
        self.operation_count += 1
        query_id = f"query_{self.session_id}_{self.operation_count}"
        
        # Create log entry
        log_entry = {
            'id': query_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': 'query',
            'agent': self.agent_name,
            'session_id': self.session_id,
            'query_text': query_text[:500] + ('...' if len(query_text) > 500 else ''),
            'metadata': metadata or {}
        }
        
        # Log to file and memory
        logger.info(
            f"Query from {self.agent_name}: {query_text[:100]}...",
            extra={
                'kb_operation': 'query',
                'kb_id': query_id,
                'kb_agent': self.agent_name
            }
        )
        log_kb_operation(log_entry)
        
        return query_id
    
    def log_results(self, query_id: str, results: Any, duration: float, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log knowledge base query results.
        
        Args:
            query_id: The query ID from log_query
            results: The results returned by the knowledge base
            duration: Query duration in seconds
            metadata: Additional metadata about the results
        """
        # Count results
        if isinstance(results, list):
            result_count = len(results)
            sample_result = results[0] if results else None
        else:
            result_count = 1
            sample_result = results
            
        # Create log entry
        log_entry = {
            'id': f"results_{query_id}",
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': 'results',
            'agent': self.agent_name,
            'session_id': self.session_id,
            'query_id': query_id,
            'result_count': result_count,
            'duration': duration,
            'metadata': metadata or {}
        }
        
        # Add sample of first result if available
        if sample_result:
            try:
                if isinstance(sample_result, dict):
                    content = sample_result.get('content', str(sample_result)[:100])
                    similarity = sample_result.get('similarity', None)
                    if similarity is not None:
                        log_entry['sample_similarity'] = similarity
                else:
                    content = str(sample_result)[:100]
                
                log_entry['sample_content'] = content[:100] + ('...' if len(content) > 100 else '')
            except Exception as e:
                log_entry['sample_error'] = str(e)
        
        # Log to file and memory
        logger.info(
            f"Query {query_id} returned {result_count} results in {duration:.3f}s",
            extra={
                'kb_operation': 'results',
                'kb_id': f"results_{query_id}",
                'kb_agent': self.agent_name
            }
        )
        log_kb_operation(log_entry)
    
    def log_error(self, query_id: Optional[str], error: Exception, 
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a knowledge base operation error.
        
        Args:
            query_id: The related query ID if available
            error: The exception that occurred
            metadata: Additional metadata about the error
        """
        # Create log entry
        error_id = f"error_{self.session_id}_{self.operation_count}"
        log_entry = {
            'id': error_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': 'error',
            'agent': self.agent_name,
            'session_id': self.session_id,
            'query_id': query_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'metadata': metadata or {}
        }
        
        # Log to file and memory
        logger.error(
            f"Knowledge base error in {self.agent_name}: {str(error)}",
            extra={
                'kb_operation': 'error',
                'kb_id': error_id,
                'kb_agent': self.agent_name
            }
        )
        log_kb_operation(log_entry)


def wrap_knowledge_base(kb, agent_name: Optional[str] = None, session_id: Optional[str] = None):
    """
    Wrap a knowledge base object with logging.
    
    Args:
        kb: The knowledge base object to wrap
        agent_name: Name of the agent using this knowledge base
        session_id: Session ID for grouping related operations
        
    Returns:
        The wrapped knowledge base with logging
    """
    if not hasattr(kb, 'query'):
        logger.warning(f"Knowledge base does not have a query method, cannot wrap for logging")
        return kb
    
    # Create a logger for this knowledge base
    kb_logger = KnowledgeLogger(agent_name=agent_name, session_id=session_id)
    
    # Keep a reference to the original query method
    original_query = kb.query
    
    @wraps(original_query)
    def query_with_logging(*args, **kwargs):
        """
        Wrapper for the knowledge base query method with detailed logging.
        """
        query_text = args[0] if args else kwargs.get('text', 'No query text available')
        
        # Log the query
        query_id = kb_logger.log_query(query_text, {
            'kwargs': {k: v for k, v in kwargs.items() if k != 'self'},
            'args_count': len(args)
        })
        
        # Execute the query with timing
        start_time = time.time()
        try:
            results = original_query(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log the results
            kb_logger.log_results(query_id, results, duration)
            
            return results
        except Exception as e:
            duration = time.time() - start_time
            kb_logger.log_error(query_id, e, {'duration': duration})
            raise
    
    # Replace the query method with our logged version
    kb.query = query_with_logging
    
    logger.info(f"Knowledge base wrapped with logging for agent {agent_name}")
    return kb

def trace_kb_usage(func: Callable) -> Callable:
    """
    Decorator to trace knowledge base usage in a function or method.
    Useful for monitoring advanced knowledge base operations that aren't simple queries.
    
    Args:
        func: The function to trace
        
    Returns:
        Wrapped function with knowledge base usage tracing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        agent_name = args[0].__class__.__name__ if args and hasattr(args[0], '__class__') else 'unknown'
        operation_id = f"{agent_name}_{func.__name__}_{int(time.time()*1000)}"
        
        logger.debug(
            f"Starting KB operation: {func.__name__}",
            extra={
                'kb_operation': 'trace',
                'kb_id': operation_id,
                'kb_agent': agent_name
            }
        )
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.debug(
                f"Completed KB operation: {func.__name__} in {duration:.3f}s",
                extra={
                    'kb_operation': 'trace',
                    'kb_id': operation_id,
                    'kb_agent': agent_name
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error in KB operation: {func.__name__}: {str(e)}",
                extra={
                    'kb_operation': 'trace_error',
                    'kb_id': operation_id,
                    'kb_agent': agent_name,
                    'error': str(e),
                    'duration': f"{duration:.3f}s"
                }
            )
            raise
    
    return wrapper 