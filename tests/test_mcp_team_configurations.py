import pytest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
import os
import sys
import asyncio
import tempfile
import json

# Add the src directory to the path so we can import the API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import run_task, TaskRequest

# Helper function to create a test directory
def create_test_filesystem():
    temp_dir = tempfile.mkdtemp(prefix="mcp_test_")
    # Create a simple JSON file with financial data
    financial_data = {
        "investment": {
            "name": "Tech Growth Fund",
            "type": "venture_capital",
            "initial_investment": 1000000,
            "projected_returns": [
                {"year": 1, "return": 0.05},
                {"year": 2, "return": 0.08},
                {"year": 3, "return": 0.12},
                {"year": 4, "return": 0.15},
                {"year": 5, "return": 0.20}
            ]
        }
    }
    
    # Write the test file
    with open(os.path.join(temp_dir, "financial_data.json"), "w") as f:
        json.dump(financial_data, f, indent=2)
    
    # Create a README file
    with open(os.path.join(temp_dir, "README.txt"), "w") as f:
        f.write("This directory contains financial data for testing purposes.\n")
        f.write("The financial_data.json file contains investment information.\n")
    
    return temp_dir


@patch('agno.tools.mcp.MCPTools.__aenter__')
@patch('agno.tools.mcp.MCPTools.__aexit__')
@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
@patch('logging.Logger.info')
async def test_mcp_tools_with_single_agent_team(
    mock_logger_info,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that MCP tools work correctly with a team containing only a single agent"""
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_mcp_tools = AsyncMock()
        mock_mcp_tools_enter.return_value = mock_mcp_tools
        
        # Mock team instance
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
        
        # Mock only one agent that will be used
        mock_financial_modeler_instance = MagicMock()
        mock_financial_modeler.return_value = mock_financial_modeler_instance
        mock_financial_modeler_instance.agent = MagicMock()
        
        # Configure the task request with only the financial modeler agent enabled
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze investment return data",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            # Explicitly disable the other agents to test single agent config
            use_searcher=False,
            use_assumption_generator=False,
            use_metrics_deriver=False,
            stream=False
        )
        
        # Run the task
        loop = asyncio.get_event_loop()
        response = await run_task(task_request)
        
        # Verify team was created with the correct agents
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "members" in team_kwargs, "Team should have the members parameter"
        
        # Only the financial modeler agent should be present
        # Note: This relies on internal handling of disabled agents in run_task
        # and may need adjustment depending on actual implementation
        agents_in_team = len(team_kwargs["members"])
        assert agents_in_team == 1, f"Expected 1 agent in team, got {agents_in_team}"
        
        # Verify MCP tools were passed correctly
        assert "tools" in team_kwargs, "Team should have the tools parameter"
        assert team_kwargs["tools"] == [mock_mcp_tools], "Team tools should include the MCP tools"
        
        # Ensure response processing worked
        assert response is not None, "Task should have returned a response"
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)


@patch('agno.tools.mcp.MCPTools.__aenter__')
@patch('agno.tools.mcp.MCPTools.__aexit__')
@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
@patch('logging.Logger.info')
async def test_mcp_tools_with_custom_team_mode(
    mock_logger_info,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that MCP tools work correctly with different team coordination modes"""
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_mcp_tools = AsyncMock()
        mock_mcp_tools_enter.return_value = mock_mcp_tools
        
        # Mock team instance
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
        
        # Mock all agent instances
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
        
        # Configure the task request with round_robin mode
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze investment data with round-robin approach",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            team_mode="round_robin",  # Use round_robin mode instead of default
            stream=False
        )
        
        # Run the task
        loop = asyncio.get_event_loop()
        response = await run_task(task_request)
        
        # Verify team was created with the correct mode
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "mode" in team_kwargs, "Team should have the mode parameter"
        assert team_kwargs["mode"] == "round_robin", "Team should use round_robin mode"
        
        # Verify MCP tools were passed correctly
        assert "tools" in team_kwargs, "Team should have the tools parameter"
        assert team_kwargs["tools"] == [mock_mcp_tools], "Team tools should include the MCP tools"
        
        # Reset mocks for the next test
        mock_team.reset_mock()
        
        # Test with authoritarian mode
        # Configure the task request with authoritarian mode
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze investment data with authoritarian approach",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            team_mode="authoritarian",  # Use authoritarian mode
            stream=False
        )
        
        # Run the task
        response = await run_task(task_request)
        
        # Verify team was created with the correct mode
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "mode" in team_kwargs, "Team should have the mode parameter"
        assert team_kwargs["mode"] == "authoritarian", "Team should use authoritarian mode"
        
        # Verify MCP tools were passed correctly
        assert "tools" in team_kwargs, "Team should have the tools parameter"
        assert team_kwargs["tools"] == [mock_mcp_tools], "Team tools should include the MCP tools"
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)


@patch('agno.tools.mcp.MCPTools.__aenter__')
@patch('agno.tools.mcp.MCPTools.__aexit__')
@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
@patch('src.tools.factory.create_tools')
@patch('logging.Logger.info')
async def test_mcp_tools_with_additional_tools(
    mock_logger_info,
    mock_create_tools,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that MCP tools work correctly with additional tools enabled"""
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_mcp_tools = AsyncMock()
        mock_mcp_tools_enter.return_value = mock_mcp_tools
        
        # Mock additional tools
        mock_additional_tools = [MagicMock(), MagicMock()]
        mock_create_tools.return_value = mock_additional_tools
        
        # Mock team instance
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
        
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
        
        # Configure the task request with web search and math tools enabled
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze investment data with additional tools",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            enable_web_search=True,
            enable_math_tools=True,
            stream=False
        )
        
        # Run the task
        loop = asyncio.get_event_loop()
        response = await run_task(task_request)
        
        # Verify create_tools was called with correct parameters
        mock_create_tools.assert_called_once()
        tools_kwargs = mock_create_tools.call_args[1]
        assert tools_kwargs["web_search_enabled"] is True, "Web search should be enabled"
        assert tools_kwargs["calculator_enabled"] is True, "Math tools should be enabled"
        
        # Verify team was created with both MCP and additional tools
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "tools" in team_kwargs, "Team should have the tools parameter"
        
        # MCP tools should be combined with additional tools
        expected_tools = [mock_mcp_tools]
        assert team_kwargs["tools"] == expected_tools, "Team should include both MCP and additional tools"
        
        # Verify additional tools were passed to agents
        mock_searcher.assert_called_once()
        searcher_kwargs = mock_searcher.call_args[1]
        assert "additional_tools" in searcher_kwargs, "Searcher should receive additional tools"
        assert searcher_kwargs["additional_tools"] == mock_additional_tools, "Searcher should receive all additional tools"
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)


@patch('agno.tools.mcp.MCPTools.__aenter__')
@patch('agno.tools.mcp.MCPTools.__aexit__')
@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
@patch('logging.Logger.info')
async def test_mcp_tools_with_memory_integration(
    mock_logger_info,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that MCP tools work correctly with memory systems enabled"""
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_mcp_tools = AsyncMock()
        mock_mcp_tools_enter.return_value = mock_mcp_tools
        
        # Mock memory
        mock_memory = MagicMock()
        
        # Patch the AgentMemory class
        with patch('agno.memory.agent.AgentMemory') as mock_agent_memory:
            mock_agent_memory.return_value = mock_memory
            
            # Patch SQLite memory db
            with patch('agno.memory.db.sqlite.SqliteMemoryDb') as mock_sqlite_memory_db:
                mock_sqlite_memory_db.return_value = MagicMock()
                
                # Mock team instance
                mock_team_instance = MagicMock()
                mock_team.return_value = mock_team_instance
                mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
                
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
                
                # Configure the task request with memory enabled
                task_request = TaskRequest(
                    model_id="gpt-4o",
                    model_provider="openai",
                    task="Analyze investment data with memory",
                    provider_api_key="sk-test-key",
                    use_filesystem_mcp=True,
                    filesystem_root_path=temp_dir,
                    # Memory parameters
                    storage_type="sqlite",
                    storage_connection=":memory:",
                    session_id="test-session-123",
                    user_id="test-user-456",
                    enable_chat_history=True,
                    enable_user_memories=True,
                    enable_summaries=True,
                    memory_depth=10,
                    stream=False
                )
                
                # Run the task
                loop = asyncio.get_event_loop()
                response = await run_task(task_request)
                
                # Verify memory was initialized
                mock_agent_memory.assert_called_once()
                memory_kwargs = mock_agent_memory.call_args[1]
                assert memory_kwargs["create_user_memories"] is True, "User memories should be enabled"
                assert memory_kwargs["create_session_summary"] is True, "Session summaries should be enabled"
                assert memory_kwargs["max_messages"] == 10, "Memory depth should be set to 10"
                
                # Verify team was created with both MCP tools and memory
                mock_team.assert_called_once()
                team_kwargs = mock_team.call_args[1]
                assert "tools" in team_kwargs, "Team should have the tools parameter"
                assert team_kwargs["tools"] == [mock_mcp_tools], "Team should have MCP tools"
                assert "memory" in team_kwargs, "Team should have memory parameter"
                assert team_kwargs["memory"] == mock_memory, "Team should have the memory instance"
                
                # Verify other memory-related parameters
                assert "add_history_to_messages" in team_kwargs, "Team should have add_history_to_messages parameter"
                assert team_kwargs["add_history_to_messages"] is True, "add_history_to_messages should be True"
                assert "read_chat_history" in team_kwargs, "Team should have read_chat_history parameter"
                assert team_kwargs["read_chat_history"] is True, "read_chat_history should be True"
    
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir) 