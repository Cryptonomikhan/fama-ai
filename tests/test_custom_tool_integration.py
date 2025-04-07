#!/usr/bin/env python3
"""
Test suite for custom tool integration with the API.

This module tests the integration of custom tools with the API endpoint,
ensuring that custom tools defined in TaskRequest are properly passed
to agents and used in the system.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.models.model_request import ToolConfig
from src.api.main import run_task, TaskRequest
from src.tools.factory import register_custom_tool
from agno.agent import Agent
from agno.team.team import Team


class TestCustomToolIntegration(unittest.TestCase):
    """Test cases for custom tool integration with the API."""

    @patch('src.api.main.create_model')
    @patch('src.api.main.knowledge_base')
    @patch('src.api.main.Team')
    @patch('src.api.main.SearchingAgent')
    @patch('src.api.main.AssumptionGeneratorAgent')
    @patch('src.api.main.MetricsDerivingAgent')
    @patch('src.api.main.FinancialModelingAgent')
    @patch('src.tools.factory.create_tools')
    async def test_custom_tool_in_task_request(
        self, 
        mock_create_tools, 
        mock_financial_modeler, 
        mock_metrics_deriver, 
        mock_assumption_generator, 
        mock_searcher,
        mock_team,
        mock_knowledge_base,
        mock_create_model
    ):
        """Test that custom tools in TaskRequest are properly passed to agents."""
        # Create mock tools
        mock_custom_tool = MagicMock()
        mock_custom_tool.__name__ = "CustomTool"
        
        # Mock the create_tools function to return our mock tool
        mock_create_tools.return_value = [mock_custom_tool]
        
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
        
        # Mock the team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with custom tools
        custom_tool_config = {
            "tool_name": "custom_data_source",
            "tool_args": {
                "api_key": "test-key",
                "base_url": "https://api.example.com"
            },
            "enabled": True
        }
        
        task_request = TaskRequest(
            message="Test message with custom tools",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            custom_tools=[custom_tool_config],
            enable_web_search=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify create_tools was called with the custom tool config
        mock_create_tools.assert_called_once()
        tools_arg = mock_create_tools.call_args[1]['tools']
        self.assertEqual(len(tools_arg), 1)
        self.assertEqual(tools_arg[0].tool_name, "custom_data_source")
        self.assertEqual(tools_arg[0].tool_args["api_key"], "test-key")
        self.assertEqual(tools_arg[0].enabled, True)
        
        # Verify agents were created with the tools
        mock_searcher.assert_called_once()
        self.assertIn('additional_tools', mock_searcher.call_args[1])
        self.assertEqual(mock_searcher.call_args[1]['additional_tools'], [mock_custom_tool])
        
        mock_assumption_generator.assert_called_once()
        self.assertIn('additional_tools', mock_assumption_generator.call_args[1])
        self.assertEqual(mock_assumption_generator.call_args[1]['additional_tools'], [mock_custom_tool])
        
        mock_metrics_deriver.assert_called_once()
        self.assertIn('additional_tools', mock_metrics_deriver.call_args[1])
        self.assertEqual(mock_metrics_deriver.call_args[1]['additional_tools'], [mock_custom_tool])
        
        mock_financial_modeler.assert_called_once()
        self.assertIn('additional_tools', mock_financial_modeler.call_args[1])
        self.assertEqual(mock_financial_modeler.call_args[1]['additional_tools'], [mock_custom_tool])


    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.tools.factory.logger')
    async def test_invalid_custom_tool_handling(
        self, 
        mock_logger, 
        mock_team,
        mock_create_model
    ):
        """Test that invalid custom tools are properly handled."""
        # Create a TaskRequest with an invalid custom tool
        invalid_tool_config = {
            "tool_name": "invalid_tool",
            # Missing required fields
        }
        
        task_request = TaskRequest(
            message="Test message with invalid custom tool",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            custom_tools=[invalid_tool_config]
        )
        
        # Create a mock for Stream Response
        mock_response = MagicMock()
        mock_team.return_value.arun = mock_response
        
        # Call run_task - this should not raise an exception
        await run_task(task_request)
        
        # Verify warning was logged
        mock_logger.warning.assert_called()


if __name__ == "__main__":
    unittest.main() 