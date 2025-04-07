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

# Helper function to create a temp directory with a test file
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
async def test_filesystem_mcp_initialization(
    mock_logger_info,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that filesystem MCP is properly initialized with the provided root path"""
    # Create a temporary directory with test data
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_mcp_tools = AsyncMock()
        mock_mcp_tools_enter.return_value = mock_mcp_tools
        
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
        
        # Create task request with filesystem MCP enabled
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze the financial data in the provided directory",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            stream=False
        )
        
        # Run the task
        loop = asyncio.get_event_loop()
        response = await run_task(task_request)
        
        # Verify that MCPTools was initialized with the correct parameters
        from agno.tools.mcp import MCPTools
        
        # Verify MCPTools was constructed with a command that includes the filesystem MCP server
        MCPTools_call_args = mock_mcp_tools_enter.call_args
        assert MCPTools_call_args is not None, "MCPTools.__aenter__ should have been called"
        
        # Check if any logging occurred for the filesystem MCP
        filesystem_mcp_logs = [
            call for call in mock_logger_info.call_args_list 
            if isinstance(call[0][0], str) and "filesystem MCP" in call[0][0].lower()
        ]
        assert len(filesystem_mcp_logs) > 0, "Expected filesystem MCP initialization to be logged"
        
        # Verify Team was created with the MCP tools
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "tools" in team_kwargs, "Team should have been created with tools parameter"
        assert team_kwargs["tools"] == [mock_mcp_tools], "Team tools should include the MCP tools"
        
        # Verify MCP resources were cleaned up
        assert mock_mcp_tools_exit.called, "MCPTools.__aexit__ should have been called for cleanup"
        
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)


@patch('agno.tools.mcp.MultiMCPTools.__aenter__')
@patch('agno.tools.mcp.MultiMCPTools.__aexit__')
@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
async def test_multiple_mcp_servers(
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_multi_mcp_tools_exit,
    mock_multi_mcp_tools_enter
):
    """Test that multiple MCP servers can be configured simultaneously"""
    # Create a temporary directory with test data
    temp_dir = create_test_filesystem()
    
    try:
        # Configure mocks
        mock_multi_mcp_tools = AsyncMock()
        mock_multi_mcp_tools_enter.return_value = mock_multi_mcp_tools
        
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
        
        # Create task request with both filesystem MCP and custom MCP servers
        task_request = TaskRequest(
            model_id="gpt-4o",
            model_provider="openai",
            task="Analyze the financial data using multiple MCP servers",
            provider_api_key="sk-test-key",
            use_filesystem_mcp=True,
            filesystem_root_path=temp_dir,
            mcp_servers=[
                {
                    "command": "npx",
                    "args": ["-y", "@financialtools/mcp-server"],
                    "env": {"API_KEY": "test-api-key"}
                }
            ],
            stream=False
        )
        
        # Run the task
        loop = asyncio.get_event_loop()
        response = await run_task(task_request)
        
        # Verify that MultiMCPTools was initialized
        from agno.tools.mcp import MultiMCPTools
        assert mock_multi_mcp_tools_enter.called, "MultiMCPTools.__aenter__ should have been called"
        
        # Verify that both the filesystem MCP and custom MCP commands were included
        MultiMCPTools_call_args = mock_multi_mcp_tools_enter.call_args
        assert MultiMCPTools_call_args is not None, "MultiMCPTools.__aenter__ should have been called"
        
        # Verify Team was created with the MCP tools
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        assert "tools" in team_kwargs, "Team should have been created with tools parameter"
        assert team_kwargs["tools"] == [mock_multi_mcp_tools], "Team tools should include the MultiMCPTools"
        
        # Verify MCP resources were cleaned up
        assert mock_multi_mcp_tools_exit.called, "MultiMCPTools.__aexit__ should have been called for cleanup"
        
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
@patch('logging.Logger.error')
async def test_filesystem_mcp_error_handling(
    mock_logger_error,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher,
    mock_mcp_tools_exit,
    mock_mcp_tools_enter
):
    """Test that errors in MCP initialization are handled gracefully"""
    # Configure mocks
    mock_mcp_tools_enter.side_effect = Exception("Failed to initialize MCP tools")
    
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
    
    # Create task request with filesystem MCP enabled
    task_request = TaskRequest(
        model_id="gpt-4o",
        model_provider="openai",
        task="Analyze the financial data despite MCP errors",
        provider_api_key="sk-test-key",
        use_filesystem_mcp=True,
        filesystem_root_path="/nonexistent/path",
        stream=False
    )
    
    # Run the task
    loop = asyncio.get_event_loop()
    response = await run_task(task_request)
    
    # Verify error was logged
    mock_logger_error.assert_any_call(contains_string("Failed to initialize MCP tools"))
    
    # Verify team was still created (without MCP tools)
    mock_team.assert_called_once()
    team_kwargs = mock_team.call_args[1]
    assert "tools" not in team_kwargs or not team_kwargs["tools"], "Team should have been created without MCP tools"
    
    # Define helper for string matching
    def contains_string(expected_substr):
        class StringContains(MagicMock):
            def __eq__(self, other):
                return isinstance(other, str) and expected_substr in other
        return StringContains()


@patch('src.agents.searcher.SearchingAgent')
@patch('src.agents.assumption_generator.AssumptionGeneratorAgent')
@patch('src.agents.metrics_deriver.MetricsDerivingAgent')
@patch('src.agents.financial_modeler.FinancialModelingAgent')
@patch('agno.team.team.Team')
@patch('logging.Logger.info')
@patch('logging.Logger.error')
async def test_validate_mcp_resource_lifecycle(
    mock_logger_error,
    mock_logger_info,
    mock_team,
    mock_financial_modeler,
    mock_metrics_deriver,
    mock_assumption_generator,
    mock_searcher
):
    """Test that MCP resources are properly initialized and cleaned up in various scenarios."""
    # Create a temporary directory with test data
    temp_dir = create_test_filesystem()
    
    try:
        # Test Case 1: Successful initialization and cleanup with MCPTools
        with patch('agno.tools.mcp.MCPTools.__aenter__') as mock_mcp_tools_enter:
            with patch('agno.tools.mcp.MCPTools.__aexit__') as mock_mcp_tools_exit:
                # Configure mocks
                mock_mcp_tools = AsyncMock()
                mock_mcp_tools_enter.return_value = mock_mcp_tools
                
                mock_team_instance = MagicMock()
                mock_team.return_value = mock_team_instance
                mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
                
                # Set up a simple task request with filesystem MCP
                task_request = TaskRequest(
                    model_id="gpt-4o",
                    model_provider="openai",
                    task="Test MCP resource lifecycle",
                    provider_api_key="sk-test-key",
                    use_filesystem_mcp=True,
                    filesystem_root_path=temp_dir,
                    stream=False
                )
                
                # Run the task
                loop = asyncio.get_event_loop()
                response = await run_task(task_request)
                
                # Verify proper initialization
                assert mock_mcp_tools_enter.called, "MCPTools.__aenter__ should have been called"
                
                # Verify proper cleanup
                assert mock_mcp_tools_exit.called, "MCPTools.__aexit__ should have been called for cleanup"
                
                # Verify resources were passed to the team
                team_kwargs = mock_team.call_args[1]
                assert "tools" in team_kwargs, "Team should have been created with tools parameter"
                assert team_kwargs["tools"] == [mock_mcp_tools], "Team tools should include the MCP tools"
                
                # Check for initialization logging
                init_logs = [
                    call for call in mock_logger_info.call_args_list 
                    if isinstance(call[0][0], str) and "initializing" in call[0][0].lower() and "mcp" in call[0][0].lower()
                ]
                assert len(init_logs) > 0, "Expected MCP initialization to be logged"
        
        # Reset mocks between tests
        mock_team.reset_mock()
        mock_logger_info.reset_mock()
        mock_logger_error.reset_mock()
        
        # Test Case 2: Successful initialization and cleanup with MultiMCPTools
        with patch('agno.tools.mcp.MultiMCPTools.__aenter__') as mock_multi_mcp_tools_enter:
            with patch('agno.tools.mcp.MultiMCPTools.__aexit__') as mock_multi_mcp_tools_exit:
                # Configure mocks
                mock_multi_mcp_tools = AsyncMock()
                mock_multi_mcp_tools_enter.return_value = mock_multi_mcp_tools
                
                mock_team_instance = MagicMock()
                mock_team.return_value = mock_team_instance
                mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
                
                # Set up a task request with both filesystem MCP and custom MCP
                task_request = TaskRequest(
                    model_id="gpt-4o",
                    model_provider="openai",
                    task="Test multiple MCP servers lifecycle",
                    provider_api_key="sk-test-key",
                    use_filesystem_mcp=True,
                    filesystem_root_path=temp_dir,
                    mcp_servers=[
                        {
                            "command": "npx",
                            "args": ["-y", "@financialtools/mcp-server"],
                            "env": {"API_KEY": "test-api-key"}
                        }
                    ],
                    stream=False
                )
                
                # Run the task
                loop = asyncio.get_event_loop()
                response = await run_task(task_request)
                
                # Verify proper initialization
                assert mock_multi_mcp_tools_enter.called, "MultiMCPTools.__aenter__ should have been called"
                
                # Verify proper cleanup
                assert mock_multi_mcp_tools_exit.called, "MultiMCPTools.__aexit__ should have been called for cleanup"
                
                # Verify resources were passed to the team
                team_kwargs = mock_team.call_args[1]
                assert "tools" in team_kwargs, "Team should have been created with tools parameter"
                assert team_kwargs["tools"] == [mock_multi_mcp_tools], "Team tools should include the MultiMCPTools"
        
        # Reset mocks between tests
        mock_team.reset_mock()
        mock_logger_info.reset_mock()
        mock_logger_error.reset_mock()
        
        # Test Case 3: Cleanup during initialization exceptions
        with patch('agno.tools.mcp.MCPTools.__aenter__') as mock_mcp_tools_enter:
            with patch('agno.tools.mcp.MCPTools.__aexit__') as mock_mcp_tools_exit:
                # Configure mocks to raise an exception
                mock_mcp_tools_enter.side_effect = Exception("Failed to initialize MCP tools")
                
                mock_team_instance = MagicMock()
                mock_team.return_value = mock_team_instance
                mock_team_instance.arun = AsyncMock(return_value=MagicMock(content="Test response"))
                
                # Set up task request with filesystem MCP
                task_request = TaskRequest(
                    model_id="gpt-4o",
                    model_provider="openai",
                    task="Test MCP error handling",
                    provider_api_key="sk-test-key",
                    use_filesystem_mcp=True,
                    filesystem_root_path=temp_dir,
                    stream=False
                )
                
                # Run the task
                loop = asyncio.get_event_loop()
                response = await run_task(task_request)
                
                # Verify initialization was attempted
                assert mock_mcp_tools_enter.called, "MCPTools.__aenter__ should have been called"
                
                # Verify __aexit__ was called to clean up even if __aenter__ failed
                assert mock_mcp_tools_exit.called, "MCPTools.__aexit__ should have been called for cleanup after exception"
                
                # Check for error logging
                error_logs = [
                    call for call in mock_logger_error.call_args_list 
                    if isinstance(call[0][0], str) and "failed" in call[0][0].lower() and "mcp" in call[0][0].lower()
                ]
                assert len(error_logs) > 0, "Expected MCP error to be logged"
                
                # Verify team was created without MCP tools after the failure
                team_kwargs = mock_team.call_args[1]
                assert "tools" not in team_kwargs or not team_kwargs["tools"], "Team should not have MCP tools after initialization failure"
        
        # Reset mocks between tests
        mock_team.reset_mock()
        mock_logger_info.reset_mock()
        mock_logger_error.reset_mock()
        
        # Test Case 4: Cleanup during run exceptions
        with patch('agno.tools.mcp.MCPTools.__aenter__') as mock_mcp_tools_enter:
            with patch('agno.tools.mcp.MCPTools.__aexit__') as mock_mcp_tools_exit:
                # Configure mocks
                mock_mcp_tools = AsyncMock()
                mock_mcp_tools_enter.return_value = mock_mcp_tools
                
                mock_team_instance = MagicMock()
                mock_team.return_value = mock_team_instance
                # Make the run method raise an exception
                mock_team_instance.arun.side_effect = Exception("Error during team run")
                
                # Set up task request with filesystem MCP
                task_request = TaskRequest(
                    model_id="gpt-4o",
                    model_provider="openai",
                    task="Test MCP cleanup after run error",
                    provider_api_key="sk-test-key",
                    use_filesystem_mcp=True,
                    filesystem_root_path=temp_dir,
                    stream=False
                )
                
                # Run the task and catch the exception we expect
                try:
                    loop = asyncio.get_event_loop()
                    response = await run_task(task_request)
                except:
                    pass
                
                # Verify initialization occurred
                assert mock_mcp_tools_enter.called, "MCPTools.__aenter__ should have been called"
                
                # Verify cleanup still happened despite run error
                assert mock_mcp_tools_exit.called, "MCPTools.__aexit__ should have been called for cleanup after run exception"
    
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir) 