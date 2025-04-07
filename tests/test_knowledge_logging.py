import pytest
from unittest.mock import patch, MagicMock
import uuid
from src.knowledge.logging import (
    KnowledgeLogger, 
    wrap_knowledge_base, 
    trace_kb_usage, 
    get_knowledge_logs,
    log_kb_operation
)

def test_knowledge_logger_query_logging():
    """Test that KnowledgeLogger.log_query correctly logs queries"""
    # Create a test logger
    agent_name = "TestAgent"
    session_id = str(uuid.uuid4())
    logger = KnowledgeLogger(agent_name=agent_name, session_id=session_id)
    
    # Log a test query
    query_text = "What is the capital of France?"
    query_id = logger.log_query(query_text)
    
    # Verify the query ID format
    assert query_id.startswith("query_")
    assert session_id in query_id
    
    # Get the logs and verify the query was logged correctly
    logs = get_knowledge_logs(operation_type="query")
    
    # Find our log entry
    query_log = next((log for log in logs if log.get('id') == query_id), None)
    assert query_log is not None
    assert query_log['agent'] == agent_name
    assert query_log['operation'] == "query"
    assert query_log['session_id'] == session_id
    assert query_log['query_text'] == query_text

def test_knowledge_logger_results_logging():
    """Test that KnowledgeLogger.log_results correctly logs query results"""
    # Create a test logger
    agent_name = "TestAgent"
    session_id = str(uuid.uuid4())
    logger = KnowledgeLogger(agent_name=agent_name, session_id=session_id)
    
    # Log a test query and results
    query_text = "What is the capital of France?"
    query_id = logger.log_query(query_text)
    
    test_results = [
        {"content": "Paris is the capital of France", "similarity": 0.95},
        {"content": "The capital city of France is Paris", "similarity": 0.82},
    ]
    
    logger.log_results(query_id, test_results, 0.125)
    
    # Get the logs and verify the results were logged correctly
    logs = get_knowledge_logs(operation_type="results")
    
    # Find our log entry
    results_log = next((log for log in logs if log.get('query_id') == query_id), None)
    assert results_log is not None
    assert results_log['agent'] == agent_name
    assert results_log['operation'] == "results"
    assert results_log['session_id'] == session_id
    assert results_log['result_count'] == 2
    assert results_log['duration'] == 0.125
    assert "Paris" in results_log['sample_content']

def test_knowledge_logger_error_logging():
    """Test that KnowledgeLogger.log_error correctly logs errors"""
    # Create a test logger
    agent_name = "TestAgent"
    session_id = str(uuid.uuid4())
    logger = KnowledgeLogger(agent_name=agent_name, session_id=session_id)
    
    # Log a test query and error
    query_text = "What is the capital of France?"
    query_id = logger.log_query(query_text)
    
    test_error = ValueError("Test error message")
    logger.log_error(query_id, test_error)
    
    # Get the logs and verify the error was logged correctly
    logs = get_knowledge_logs(operation_type="error")
    
    # Find our log entry
    error_log = next((log for log in logs if log.get('query_id') == query_id), None)
    assert error_log is not None
    assert error_log['agent'] == agent_name
    assert error_log['operation'] == "error"
    assert error_log['session_id'] == session_id
    assert error_log['error_type'] == "ValueError"
    assert error_log['error_message'] == "Test error message"

def test_wrap_knowledge_base():
    """Test that wrap_knowledge_base correctly wraps a knowledge base with logging"""
    # Create a mock knowledge base
    mock_kb = MagicMock()
    mock_kb.query = MagicMock(return_value=[{"content": "Test result"}])
    
    # Wrap the knowledge base with logging
    agent_name = "TestAgent"
    session_id = str(uuid.uuid4())
    wrapped_kb = wrap_knowledge_base(mock_kb, agent_name=agent_name, session_id=session_id)
    
    # Use the wrapped knowledge base
    query_text = "Test query"
    results = wrapped_kb.query(query_text)
    
    # Verify the original query method was called
    mock_kb.query.assert_called_once_with(query_text)
    
    # Verify the results are returned correctly
    assert results == [{"content": "Test result"}]
    
    # Get the logs and verify logging occurred
    query_logs = get_knowledge_logs(operation_type="query")
    result_logs = get_knowledge_logs(operation_type="results")
    
    # Find the most recent query and result logs
    query_log = next((log for log in query_logs if log.get('agent') == agent_name), None)
    assert query_log is not None
    assert query_log['query_text'] == query_text
    
    result_log = next((log for log in result_logs if log.get('agent') == agent_name), None)
    assert result_log is not None
    assert result_log['result_count'] == 1

@trace_kb_usage
def test_decorated_function(arg1, arg2=None):
    """Test function decorated with trace_kb_usage"""
    return f"{arg1}-{arg2}"

def test_trace_kb_usage_decorator():
    """Test that trace_kb_usage decorator correctly logs function calls"""
    # Call the decorated function
    result = test_decorated_function("test", arg2="value")
    assert result == "test-value"
    
    # Verify trace logs were created
    logs = get_knowledge_logs()
    
    # Find trace operation logs
    trace_logs = [log for log in logs if log.get('operation') == 'trace']
    assert len(trace_logs) > 0
    
    # Find our specific trace log
    func_logs = [log for log in trace_logs if 'test_decorated_function' in log.get('id', '')]
    assert len(func_logs) > 0

def test_knowledge_logger_integration_with_api():
    """Test integration of knowledge logging with API endpoints"""
    with patch('src.api.main.wrap_knowledge_base') as mock_wrap_kb:
        from src.api.main import run_task, TaskRequest
        
        # Set up a mock knowledge base and wrapped knowledge base
        mock_kb = MagicMock()
        mock_wrapped_kb = MagicMock()
        mock_wrap_kb.return_value = mock_wrapped_kb
        
        with patch('src.knowledge.factory.initialize_knowledge_base', return_value=mock_kb):
            # Create a task request with knowledge base parameters
            task_request = TaskRequest(
                message="Test message",
                model_id="gpt-4o",
                model_provider="openai",
                task="Create a financial model for a rental property investment",
                provider_api_key="sk-test",
                knowledge_urls=["https://example.com/test.pdf"],
                vector_db_type="lancedb",
                embedder_provider="openai",
                embedder_model="text-embedding-3-small"
            )
            
            # Mock other dependencies to avoid actual API calls
            with patch('src.agents.searcher.SearchingAgent'):
                with patch('src.agents.assumption_generator.AssumptionGeneratorAgent'):
                    with patch('src.agents.metrics_deriver.MetricsDerivingAgent'):
                        with patch('src.agents.financial_modeler.FinancialModelingAgent'):
                            with patch('agno.team.team.Team'):
                                with patch('src.api.main.create_model'):
                                    # Call run_task
                                    run_task(task_request)
            
            # Verify wrap_knowledge_base was called with the right parameters
            mock_wrap_kb.assert_called_once()
            # First argument should be the knowledge base
            assert mock_wrap_kb.call_args[0][0] == mock_kb
            # Agent name should be "APIEndpoint"
            assert mock_wrap_kb.call_args[1]['agent_name'] == "APIEndpoint"
            # Session ID should be a valid UUID
            assert 'session_id' in mock_wrap_kb.call_args[1] 