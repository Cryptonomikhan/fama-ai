#!/usr/bin/env python3
"""
Test suite for tool configuration functionality.

This module tests the tool configuration functionality, ensuring that tools
are correctly created and configured based on TaskRequest parameters.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import logging

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.models.model_request import ToolConfig
from src.tools.factory import create_tools, register_custom_tool
from src.tools.website_scraper import WebSearchTool
from src.tools.math_tools import CalculatorTool, DataAnalysisTool
from src.tools.financial_calculations import FinancialDataTool


class TestToolConfiguration(unittest.TestCase):
    """Test cases for tool configuration and creation."""

    def setUp(self):
        """Set up test environment."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Prepare test tools
        self.test_tools = {
            "web_search": WebSearchTool,
            "calculator": CalculatorTool,
            "data_analysis": DataAnalysisTool,
            "financial_data": FinancialDataTool,
        }

    def test_create_tools_with_strings(self):
        """Test creating tools using string identifiers."""
        tools = create_tools(tools=["calculator", "web_search"])
        
        self.assertEqual(len(tools), 2)
        self.assertTrue(any(isinstance(tool, CalculatorTool) for tool in tools))
        self.assertTrue(any(isinstance(tool, WebSearchTool) for tool in tools))

    def test_create_tools_with_config(self):
        """Test creating tools using ToolConfig objects."""
        tool_configs = [
            ToolConfig(tool_name="calculator", tool_args={"precision": 4}, enabled=True),
            ToolConfig(tool_name="web_search", tool_args={"max_results": 5}, enabled=True)
        ]
        
        tools = create_tools(tools=tool_configs)
        
        self.assertEqual(len(tools), 2)
        self.assertTrue(any(isinstance(tool, CalculatorTool) for tool in tools))
        self.assertTrue(any(isinstance(tool, WebSearchTool) for tool in tools))

    def test_disabled_tools(self):
        """Test that disabled tools are not created."""
        tool_configs = [
            ToolConfig(tool_name="calculator", tool_args={}, enabled=True),
            ToolConfig(tool_name="web_search", tool_args={}, enabled=False)
        ]
        
        tools = create_tools(tools=tool_configs)
        
        self.assertEqual(len(tools), 1)
        self.assertTrue(isinstance(tools[0], CalculatorTool))
        self.assertFalse(any(isinstance(tool, WebSearchTool) for tool in tools))

    def test_boolean_flags(self):
        """Test that boolean flags correctly control tool creation."""
        tools = create_tools(
            web_search_enabled=True,
            data_analysis_enabled=True,
            calculator_enabled=False
        )
        
        self.assertTrue(any(isinstance(tool, WebSearchTool) for tool in tools))
        self.assertTrue(any(isinstance(tool, DataAnalysisTool) for tool in tools))
        self.assertFalse(any(isinstance(tool, CalculatorTool) for tool in tools))

    def test_custom_tool_registration(self):
        """Test registration of custom tools."""
        # Create a mock tool class
        MockTool = MagicMock()
        MockTool.__name__ = "MockTool"
        
        # Register the custom tool
        register_custom_tool("mock_tool", MockTool)
        
        # Try to create the tool
        tools = create_tools(tools=["mock_tool"])
        
        # Verify the tool was created
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].__class__.__name__, "MockTool")

    @patch('src.tools.factory.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling during tool creation."""
        # Create a tool class that raises an exception
        def failing_constructor():
            raise ValueError("Test exception")
        
        MockFailingTool = MagicMock()
        MockFailingTool.side_effect = failing_constructor
        MockFailingTool.__name__ = "MockFailingTool"
        
        # Register the failing tool
        register_custom_tool("failing_tool", MockFailingTool)
        
        # Try to create the tool
        tools = create_tools(tools=["failing_tool", "calculator"])
        
        # Verify only the valid tool was created
        self.assertEqual(len(tools), 1)
        self.assertTrue(isinstance(tools[0], CalculatorTool))
        
        # Verify the error was logged
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main() 