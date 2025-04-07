import pytest
from unittest.mock import patch, MagicMock, ANY, mock
import os
import sys
from fastapi.testclient import TestClient
import unittest.mock

# Add the src directory to the path so we can import the API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app, run_task, TaskRequest

client = TestClient(app)

# Helper function for string matching in assert calls
def contains_string(expected_substr):
    class StringContains(unittest.mock.Mock):
        def __eq__(self, other):
            return isinstance(other, str) and expected_substr in other
    return StringContains()

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
@patch('logging.Logger.info')
@patch('logging.Logger.debug')
def test_knowledge_base_usage_logging(
    mock_logger_debug,
    mock_logger_info,
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that knowledge base usage is properly logged"""
    
    # Create a mock knowledge base with a query method
    mock_kb = MagicMock()
    mock_query_results = [
        {"content": "Sample result 1", "similarity": 0.95},
        {"content": "Sample result 2", "similarity": 0.85},
        {"content": "Sample result 3", "similarity": 0.75},
    ]
    mock_kb.query = MagicMock(return_value=mock_query_results)
    mock_initialize_kb.return_value = mock_kb
    
    # Create a mock team that will use the knowledge base
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    
    # Configure the team's arun method to trigger a knowledge base query
    async def mock_arun_with_kb_query(*args, **kwargs):
        # Simulate a knowledge base query during execution
        mock_kb.query("What is the capital of France?")
        return MagicMock(content="Test response")
    
    mock_team_instance.arun = mock_arun_with_kb_query
    
    # Mock agent instances
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request with knowledge base parameters and verbose logging
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        verbose_logging=True,
        stream=False
    )
    
    # Call run_task - this will use our mocked versions
    response = run_task(task_request)
    
    # Verify that knowledge base initialization is logged
    mock_logger_info.assert_any_call("Initializing knowledge base")
    
    # Verify that knowledge base query is logged
    # Find logs containing "Knowledge base query"
    query_logs = [call for call in mock_logger_info.call_args_list if 
                 isinstance(call[0][0], str) and 
                 "Knowledge base query" in call[0][0] and
                 "What is the capital of France?" in call[0][0]]
    
    assert len(query_logs) > 0, "Expected knowledge base query to be logged"
    
    # Verify that query results are logged when verbose logging is enabled
    result_logs = [call for call in mock_logger_debug.call_args_list if 
                  isinstance(call[0][0], str) and 
                  "Knowledge base query" in call[0][0] and
                  "result" in call[0][0]]
    
    # Should have logs for the first three results
    assert len(result_logs) >= 3, "Expected at least 3 result logs due to verbose logging"

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
def test_run_task_with_knowledge_base(
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that run_task initializes and passes the knowledge base to agents"""
    
    # Set up mocks
    mock_kb = MagicMock()
    mock_initialize_kb.return_value = mock_kb
    
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    # Mock the agent instances
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request with knowledge base parameters
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        knowledge_text="Test knowledge text",
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        chunking_strategy="fixed",
        chunk_size=5000,
        chunk_overlap=0,
        similarity_threshold=0.5,
        stream=False
    )
    
    # Call run_task
    response = run_task(task_request)
    
    # Verify knowledge base was initialized
    mock_initialize_kb.assert_called_once_with(
        knowledge_urls=task_request.knowledge_urls,
        knowledge_text=task_request.knowledge_text,
        vector_db_type=task_request.vector_db_type,
        embedder_provider=task_request.embedder_provider,
        embedder_model=task_request.embedder_model,
        provider_api_key=task_request.provider_api_key,
        chunking_strategy=task_request.chunking_strategy,
        chunk_size=task_request.chunk_size,
        chunk_overlap=task_request.chunk_overlap,
        similarity_threshold=task_request.similarity_threshold
    )
    
    # Verify knowledge base was passed to all agents
    mock_searcher.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=mock_kb,
        search_knowledge=True,
        api_key=task_request.provider_api_key
    )
    
    mock_assumption_generator.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=mock_kb,
        search_knowledge=True,
        api_key=task_request.provider_api_key
    )
    
    mock_metrics_deriver.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=mock_kb,
        search_knowledge=True,
        api_key=task_request.provider_api_key
    )
    
    mock_financial_modeler.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=mock_kb,
        search_knowledge=True,
        api_key=task_request.provider_api_key
    )
    
    # Verify team was created with all agents
    mock_team.assert_called_once()
    team_kwargs = mock_team.call_args.kwargs
    assert team_kwargs["name"] == "Financial Modeling Team"
    assert len(team_kwargs["members"]) == 4
    assert mock_searcher_instance.agent in team_kwargs["members"]
    assert mock_assumption_generator_instance.agent in team_kwargs["members"]
    assert mock_metrics_deriver_instance.agent in team_kwargs["members"]
    assert mock_financial_modeler_instance.agent in team_kwargs["members"]
    
    # Verify team.arun was called with the message
    mock_team_instance.arun.assert_called_once_with(task_request.message, stream=False)
    
    # Check response
    assert response == "Test response"

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
def test_run_task_without_knowledge_base(
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that run_task works without knowledge base parameters"""
    
    # Set up mocks
    mock_initialize_kb.return_value = None
    
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    # Mock the agent instances
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request without knowledge base parameters
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        stream=False
    )
    
    # Call run_task
    response = run_task(task_request)
    
    # Verify knowledge base was not initialized
    mock_initialize_kb.assert_not_called()
    
    # Verify knowledge base was not passed to agents
    mock_searcher.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=None,
        search_knowledge=False,
        api_key=task_request.provider_api_key
    )
    
    # Verify team.arun was called with the message
    mock_team_instance.arun.assert_called_once_with(task_request.message, stream=False)
    
    # Check response
    assert response == "Test response"

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
def test_knowledge_base_init_before_agent_creation(
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that knowledge base initialization happens before agent creation"""
    
    # Create a mock manager to track the order of calls
    mock_manager = MagicMock()
    
    # Setup the mocks to record their call order through the manager
    def initialize_kb_side_effect(**kwargs):
        mock_manager.initialize_knowledge_base()
        return MagicMock()
    
    def searcher_side_effect(**kwargs):
        mock_manager.create_searcher_agent()
        instance = MagicMock()
        instance.agent = MagicMock()
        return instance
    
    def assumption_side_effect(**kwargs):
        mock_manager.create_assumption_agent()
        instance = MagicMock()
        instance.agent = MagicMock()
        return instance
    
    def metrics_side_effect(**kwargs):
        mock_manager.create_metrics_agent()
        instance = MagicMock()
        instance.agent = MagicMock()
        return instance
    
    def modeler_side_effect(**kwargs):
        mock_manager.create_modeler_agent()
        instance = MagicMock()
        instance.agent = MagicMock()
        return instance
    
    # Set up the side effects
    mock_initialize_kb.side_effect = initialize_kb_side_effect
    mock_searcher.side_effect = searcher_side_effect
    mock_assumption_generator.side_effect = assumption_side_effect
    mock_metrics_deriver.side_effect = metrics_side_effect
    mock_financial_modeler.side_effect = modeler_side_effect
    
    # Create a mock team instance
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    # Create task request
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        stream=False
    )
    
    # Call run_task
    run_task(task_request)
    
    # Get the call order from the mock manager
    mock_manager.assert_has_calls([
        mock.call.initialize_knowledge_base(),
        mock.call.create_searcher_agent(),
        mock.call.create_assumption_agent(),
        mock.call.create_metrics_agent(),
        mock.call.create_modeler_agent()
    ], any_order=False)  # any_order=False ensures the calls happened in this exact order
    
    # Verify that the knowledge base initialization was called before any agent creation
    mock_manager.method_calls.index(mock.call.initialize_knowledge_base()) < \
    mock_manager.method_calls.index(mock.call.create_searcher_agent()) 

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
@patch('logging.Logger.error')
@patch('logging.Logger.warning')
def test_knowledge_base_error_handling(
    mock_logger_warning,
    mock_logger_error,
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that knowledge base integration errors are properly handled"""
    
    # Set up initialize_knowledge_base to raise an exception
    mock_initialize_kb.side_effect = Exception("Simulated knowledge base error")
    
    # Create mock team and agent instances
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request with knowledge base parameters
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        stream=False
    )
    
    # Call run_task - this should handle the exception thrown by initialize_knowledge_base
    response = run_task(task_request)
    
    # Verify that the error is logged
    mock_logger_error.assert_any_call("Unexpected error initializing knowledge base: Simulated knowledge base error")
    
    # Verify that we log a warning about proceeding without knowledge base
    mock_logger_warning.assert_any_call("Proceeding with agents without knowledge base support due to unexpected error")
    
    # Verify that agents are initialized without knowledge base
    mock_searcher.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=None,
        search_knowledge=False,
        api_key=task_request.provider_api_key
    )
    
    # Verify that team.arun is still called (the overall process continues)
    mock_team_instance.arun.assert_called_once_with(task_request.message, stream=False)
    
    # Check that we get a valid response despite the knowledge base error
    assert response == "Test response"

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
@patch('logging.Logger.error')
@patch('logging.Logger.warning')
def test_knowledge_base_specific_error_handling(
    mock_logger_warning,
    mock_logger_error,
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that specific knowledge base errors are properly handled"""
    
    # Import necessary classes to create specific error types for testing
    from src.knowledge.factory import KnowledgeBaseError
    
    # Set up initialize_knowledge_base to raise a specific KnowledgeBaseError
    error_details = {"vector_db_type": "unknown_db", "embedder_provider": "invalid"}
    mock_initialize_kb.side_effect = KnowledgeBaseError("Invalid vector database configuration", error_details)
    
    # Create mock team and agent instances
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request with knowledge base parameters
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="unknown_db",  # Intentionally using an invalid DB type
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        stream=False
    )
    
    # Call run_task - this should handle the KnowledgeBaseError
    response = run_task(task_request)
    
    # Verify that the KnowledgeBaseError is logged with its message
    mock_logger_error.assert_any_call("Knowledge base initialization error: Invalid vector database configuration")
    
    # Verify that the error details are also logged
    mock_logger_error.assert_any_call(f"Knowledge base error details: {error_details}")
    
    # Verify that we log a warning about proceeding without knowledge base
    mock_logger_warning.assert_any_call("Proceeding with agents without knowledge base support due to initialization failure")
    
    # Verify that agents are initialized without knowledge base
    mock_searcher.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=None,
        search_knowledge=False,
        api_key=task_request.provider_api_key
    )
    
    # Verify that team.arun is still called (the overall process continues)
    mock_team_instance.arun.assert_called_once_with(task_request.message, stream=False)
    
    # Check that we get a valid response despite the knowledge base error
    assert response == "Test response"

@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('src.knowledge.factory.initialize_knowledge_base')
@patch('agno.team.team.Team')
@patch('logging.Logger.error')
@patch('logging.Logger.warning')
@patch('logging.Logger.info')
def test_knowledge_base_query_failure_handling(
    mock_logger_info,
    mock_logger_warning,
    mock_logger_error,
    mock_team, 
    mock_initialize_kb, 
    mock_financial_modeler, 
    mock_metrics_deriver, 
    mock_assumption_generator, 
    mock_searcher
):
    """Test that knowledge base query failures are properly handled"""
    
    # Create a mock knowledge base with a query method that will fail
    mock_kb = MagicMock()
    mock_kb.query = MagicMock(side_effect=Exception("Simulated query failure"))
    mock_initialize_kb.return_value = mock_kb
    
    # Create mock team and agent instances
    mock_team_instance = MagicMock()
    mock_team.return_value = mock_team_instance
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    
    mock_searcher_instance = MagicMock()
    mock_searcher.return_value = mock_searcher_instance
    mock_searcher_instance.agent = MagicMock()
    
    mock_assumption_generator_instance = MagicMock()
    mock_assumption_generator.return_value = mock_assumption_generator_instance
    mock_assumption_generator_instance.agent = MagicMock()
    
    mock_metrics_deriver_instance = MagicMock()
    mock_metrics_deriver.return_value = mock_metrics_deriver_instance
    mock_metrics_deriver_instance.agent = MagicMock()
    
    mock_financial_modeler_instance = MagicMock()
    mock_financial_modeler.return_value = mock_financial_modeler_instance
    mock_financial_modeler_instance.agent = MagicMock()
    
    # Create task request with knowledge base parameters
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        provider_api_key="sk-test-key",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="lancedb",
        embedder_provider="openai",
        embedder_model="text-embedding-3-small",
        stream=False
    )
    
    # Call run_task - this should handle the query failure
    response = run_task(task_request)
    
    # Verify that the query error is logged
    mock_logger_error.assert_any_call("Knowledge base test query failed: Simulated query failure")
    
    # Verify that we log a warning about disabling knowledge base
    mock_logger_warning.assert_any_call("Disabling knowledge base due to test query failure")
    
    # Verify that agents are initialized without knowledge base
    mock_searcher.assert_called_once_with(
        provider=task_request.provider,
        model_id=task_request.model,
        temperature=0.025,
        knowledge_base=None,
        search_knowledge=False,
        api_key=task_request.provider_api_key
    )
    
    # Verify that team.arun is still called (the overall process continues)
    mock_team_instance.arun.assert_called_once_with(task_request.message, stream=False)
    
    # Check that we get a valid response despite the knowledge base error
    assert response == "Test response"

@patch("src.api.main.SearchingAgent")
@patch("src.api.main.AssumptionGeneratorAgent")
@patch("src.api.main.MetricsDerivingAgent")
@patch("src.api.main.FinancialModelingAgent")
@patch("src.api.main.Team")
@patch("src.api.main.logger")
@patch("src.api.main.initialize_knowledge_base")
def test_knowledge_base_missing_dependency_fallback(
    mock_init_kb, mock_logger, mock_team, mock_modeler, mock_metrics, mock_assumptions, mock_searcher
):
    """Test that the API continues to work when knowledge base has a missing dependency."""
    # Setup mock to raise ImportError (missing dependency)
    mock_init_kb.side_effect = ImportError("Missing required dependency: some_package")
    
    # Setup mock team and agent instances
    mock_team_instance = MagicMock()
    mock_team_instance.arun.return_value = MagicMock(content="Test response")
    mock_team.return_value = mock_team_instance
    
    # Setup mock agent instances
    for mock_agent in [mock_searcher, mock_assumptions, mock_metrics, mock_modeler]:
        mock_agent_instance = MagicMock()
        mock_agent_instance.agent = MagicMock()
        mock_agent.return_value = mock_agent_instance
    
    # Create task request with knowledge URLs that would normally use the missing dependency
    task_request = TaskRequest(
        message="Test message",
        provider="openai",
        model="gpt-4o",
        knowledge_urls=["https://example.com/test.pdf"],
        vector_db_type="lancedb",
        provider_api_key="test-api-key"
    )
    
    # Call the function
    response = run_task(task_request)
    
    # Verify that the import error was logged
    mock_logger.error.assert_any_call(contains_string("Missing required dependency"))
    
    # Verify the warning about proceeding without knowledge base was logged
    mock_logger.warning.assert_any_call(contains_string("Proceeding with agents without knowledge base"))
    
    # Verify that agents were still initialized (without knowledge base)
    assert mock_searcher.called
    assert mock_assumptions.called
    assert mock_metrics.called
    assert mock_modeler.called
    
    # Verify that the knowledge_base parameter was None for all agents
    for mock_agent in [mock_searcher, mock_assumptions, mock_metrics, mock_modeler]:
        assert mock_agent.call_args.kwargs.get('knowledge_base') is None
        assert mock_agent.call_args.kwargs.get('search_knowledge') is False
    
    # Verify that the team was created and the task was processed
    assert mock_team.called
    assert mock_team_instance.arun.called
    
    # Verify that a valid response was returned (even without knowledge base)
    assert response is not None 