#!/usr/bin/env python3
"""
Tool Factory for creating and configuring tools.

This module provides functionality to create and configure tools based on the
tool configuration provided in the API request. It follows Agno's patterns
for tool initialization and configuration.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from src.api.models.model_request import ToolConfig

# Import all available tools
from src.tools.website_scraper import WebScraperTool, WebSearchTool
from src.tools.math_tools import CalculatorTool, DataAnalysisTool
from src.tools.financial_calculations import FinancialDataTool

logger = logging.getLogger(__name__)


# Dictionary mapping tool names to their respective classes
TOOL_CLASSES = {
    "web_search": WebSearchTool,
    "calculator": CalculatorTool,
    "data_analysis": DataAnalysisTool,
    "financial_data": FinancialDataTool,
}


def create_tools(
    tools: Optional[List[Union[str, ToolConfig]]] = None,
    web_search_enabled: bool = False,
    data_analysis_enabled: bool = False,
    calculator_enabled: bool = True,
    **kwargs,
) -> List[Any]:
    """
    Create and configure tools based on the provided configuration.
    
    Args:
        tools: List of tools to enable, which can be strings or ToolConfig objects
        web_search_enabled: Whether to enable web search capabilities
        data_analysis_enabled: Whether to enable data analysis capabilities
        calculator_enabled: Whether to enable calculator capabilities
        **kwargs: Additional arguments to pass to tool constructors
        
    Returns:
        List of configured tool instances
    """
    configured_tools = []
    
    # Handle explicit tool configurations
    if tools:
        for tool in tools:
            if isinstance(tool, str):
                # Simple string-based configuration
                if tool in TOOL_CLASSES:
                    try:
                        logger.info(f"Initializing tool: {tool}")
                        tool_instance = TOOL_CLASSES[tool]()
                        configured_tools.append(tool_instance)
                    except Exception as e:
                        logger.error(f"Failed to initialize tool {tool}: {str(e)}")
            else:
                # Detailed ToolConfig configuration
                tool_name = tool.tool_name
                tool_args = tool.tool_args
                enabled = tool.enabled
                
                if not enabled:
                    logger.info(f"Tool {tool_name} is explicitly disabled")
                    continue
                    
                if tool_name in TOOL_CLASSES:
                    try:
                        logger.info(f"Initializing tool: {tool_name} with args: {tool_args}")
                        tool_instance = TOOL_CLASSES[tool_name](**tool_args)
                        configured_tools.append(tool_instance)
                    except Exception as e:
                        logger.error(f"Failed to initialize tool {tool_name}: {str(e)}")
    
    # Handle boolean flags for common tools
    if web_search_enabled and "web_search" not in [t.__class__.__name__ for t in configured_tools]:
        try:
            logger.info("Enabling web search tool via flag")
            configured_tools.append(WebSearchTool())
        except Exception as e:
            logger.error(f"Failed to initialize web search tool: {str(e)}")
            
    if data_analysis_enabled and "data_analysis" not in [t.__class__.__name__ for t in configured_tools]:
        try:
            logger.info("Enabling data analysis tool via flag")
            configured_tools.append(DataAnalysisTool())
        except Exception as e:
            logger.error(f"Failed to initialize data analysis tool: {str(e)}")
            
    if calculator_enabled and "calculator" not in [t.__class__.__name__ for t in configured_tools]:
        try:
            logger.info("Enabling calculator tool via flag")
            configured_tools.append(CalculatorTool())
        except Exception as e:
            logger.error(f"Failed to initialize calculator tool: {str(e)}")
    
    logger.info(f"Created {len(configured_tools)} tools: {[t.__class__.__name__ for t in configured_tools]}")
    return configured_tools


def register_custom_tool(tool_name: str, tool_class: Any) -> None:
    """
    Register a custom tool class to make it available for configuration.
    
    Args:
        tool_name: Name of the tool to register
        tool_class: Tool class to register
    """
    if tool_name in TOOL_CLASSES:
        logger.warning(f"Overriding existing tool: {tool_name}")
    
    TOOL_CLASSES[tool_name] = tool_class
    logger.info(f"Registered custom tool: {tool_name}")
    

def validate_tools(tools_list: List[Any]) -> bool:
    """
    Validate that all tools in the list are properly initialized.
    
    Args:
        tools_list: List of tool instances to validate
        
    Returns:
        True if all tools are valid, False otherwise
    """
    for tool in tools_list:
        # Check for required attributes and methods
        if not hasattr(tool, "name") or not hasattr(tool, "description"):
            logger.error(f"Tool {tool.__class__.__name__} is missing required attributes")
            return False
            
        # Check for required methods (if following Agno's patterns)
        if not hasattr(tool, "run") or not callable(getattr(tool, "run")):
            logger.error(f"Tool {tool.__class__.__name__} is missing required run method")
            return False
    
    return True 