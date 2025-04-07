from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator


class Provider(str, Enum):
    """Model provider options"""
    formation = "formation"
    openai = "openai"
    anthropic = "anthropic"
    openrouter = "openrouter"


class StorageType(str, Enum):
    """Storage type options for agent state persistence"""
    sqlite = "sqlite"
    postgres = "postgres"
    mongodb = "mongodb"
    dynamodb = "dynamodb"
    json = "json"
    yaml = "yaml"


class MemoryType(str, Enum):
    """Memory type options for agents"""
    default = "default"
    buffer = "buffer"
    summary = "summary"
    window = "window"
    none = "none"


class ToolConfig(BaseModel):
    """Configuration for a tool to be used by the agent"""
    tool_name: str = Field(..., description="Name of the tool to use")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    enabled: bool = Field(True, description="Whether the tool is enabled")
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        """Validate the tool name to ensure it's a supported tool."""
        supported_tools = [
            "web_search", "calculator", "data_analysis", "financial_data", 
            "code_interpreter", "json_explorer", "file_browser", "url_fetcher"
        ]
        if v not in supported_tools:
            raise ValueError(f"Tool '{v}' is not supported. Supported tools: {', '.join(supported_tools)}")
        return v


class ModelRequest(BaseModel):
    """Request model for financial modeling"""
    description: str = Field(..., description="Description of the investment opportunity")
    provider: Provider = Field(Provider.formation, description="Model provider")
    api_key: Optional[str] = Field(None, description="API key for the selected provider")
    model_id: Optional[str] = Field(None, description="Model ID to use (provider-specific)")
    stream: bool = Field(True, description="Whether to stream the response")
    temperature: float = Field(0.1, description="Temperature for generation")
    timeout: int = Field(300, description="Timeout for the request in seconds")
    
    # Knowledge
    knowledge_urls: Optional[List[str]] = Field(None, description="List of URLs to use as knowledge sources")
    
    # Memory & History
    memory_id: Optional[str] = Field(None, description="Memory ID for persistent memory")
    history_id: Optional[str] = Field(None, description="History ID for conversation tracking")
    
    # Storage
    storage_type: Optional[StorageType] = Field(None, description="Storage type for agent state persistence")
    storage_connection: Optional[str] = Field(None, description="Connection string or path for the storage")
    session_id: Optional[str] = Field(None, description="Session ID for persistent sessions")
    user_id: Optional[str] = Field(None, description="User ID for multi-user systems")
    
    # Tools integration
    tools: Optional[List[Union[str, ToolConfig]]] = Field(None, description="List of tools to use")
    web_search_enabled: bool = Field(False, description="Whether web search capability is enabled")
    data_analysis_enabled: bool = Field(False, description="Whether data analysis capability is enabled")
    calculator_enabled: bool = Field(True, description="Whether calculator capability is enabled")
    
    # Memory configuration
    memory_window_size: Optional[int] = Field(None, description="Number of messages to keep in memory window")
    summarize_memory: bool = Field(False, description="Whether to summarize long conversations")
    memory_type: Optional[MemoryType] = Field(MemoryType.default, description="Type of memory to use")
    
    # MCP Server
    mcp_server_url: Optional[str] = Field(None, description="URL for MCP server")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature is within allowed range."""
        if v < 0 or v > 2.0:
            raise ValueError("Temperature must be between 0 and 2.0")
        return v
    
    @validator('memory_window_size')
    def validate_memory_window_size(cls, v):
        """Validate memory window size is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Memory window size must be a positive integer")
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("Timeout must be a positive integer")
        return v
    
    @root_validator
    def validate_storage_config(cls, values):
        """Validate storage configuration."""
        storage_type = values.get('storage_type')
        storage_connection = values.get('storage_connection')
        session_id = values.get('session_id')
        
        # If any storage parameter is provided, ensure all required ones are present
        if any([storage_type, storage_connection, session_id]):
            if not storage_type:
                raise ValueError("storage_type is required when using storage functionality")
            if not storage_connection:
                raise ValueError("storage_connection is required when using storage functionality")
            if not session_id:
                raise ValueError("session_id is required when using storage functionality")
        
        return values
    
    @validator('tools')
    def validate_tools(cls, v):
        """Validate tool configurations."""
        if v is None:
            return v
            
        normalized_tools = []
        for tool in v:
            # If tool is a string, convert it to a ToolConfig
            if isinstance(tool, str):
                supported_tools = [
                    "web_search", "calculator", "data_analysis", "financial_data", 
                    "code_interpreter", "json_explorer", "file_browser", "url_fetcher"
                ]
                if tool not in supported_tools:
                    raise ValueError(f"Tool '{tool}' is not supported. Supported tools: {', '.join(supported_tools)}")
                normalized_tools.append(ToolConfig(tool_name=tool))
            else:
                normalized_tools.append(tool)
                
        return normalized_tools


class ModelResponse(BaseModel):
    """Response model for financial modeling"""
    request_id: str
    search_results: Optional[str] = None
    assumptions: Optional[Dict[str, Any]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    financial_model: Dict[str, Any] 