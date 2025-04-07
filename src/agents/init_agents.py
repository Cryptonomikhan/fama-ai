#!/usr/bin/env python3
"""
Agent initialization for Fama AI.

This module provides functions for initializing agent teams with various
configurations, including optional storage for persistent sessions.
"""

import logging
from typing import Dict, Any, Optional, List, Union

# Import agent classes
from src.agents.searcher import SearchingAgent
from src.agents.assumption_generator import AssumptionGeneratorAgent
from src.agents.metrics_deriver import MetricsDerivingAgent
from src.agents.financial_modeler import FinancialModelingAgent

# Import for team creation
from agno.team.team import Team

# Import for model creation
from src.models.factory import create_model

# Import storage utilities
from src.storage.factory import initialize_storage, AgentStorage

# Set up logging
logger = logging.getLogger(__name__)

def initialize_financial_modeling_team(
    api_key: str,
    provider: str = "openai",
    model_id: str = "gpt-4o",
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    knowledge_files: Optional[List[str]] = None,
    knowledge_urls: Optional[List[str]] = None,
    memory_id: Optional[str] = None,
    history_id: Optional[str] = None,
    storage_type: Optional[str] = None,
    storage_connection: Optional[str] = None, 
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    table_name: str = "agent_sessions",
    mcp_server_url: Optional[str] = None,
    search_tool: str = "duckduckgo",
    firecrawl: bool = False,
    firecrawl_api_key: Optional[str] = None,
    knowledge_base: Any = None,
    search_knowledge: bool = True,
    team_name: str = "Financial Modeling Team",
    team_mode: str = "coordinate",
    **kwargs: Any
) -> Union[Team, Dict[str, Any]]:
    """
    Initialize a team of financial modeling agents with optional storage.
    
    This function creates a team of specialized agents for financial modeling tasks,
    including research, assumption generation, metrics derivation, and financial modeling.
    If storage parameters are provided, each agent will use persistent storage for
    maintaining state across sessions.
    
    Args:
        api_key: API key for the model provider
        provider: Model provider (e.g., "openai", "anthropic", "formation")
        model_id: ID of the model to use
        temperature: Temperature for model generation (higher = more creative)
        max_tokens: Maximum tokens to generate in responses
        knowledge_files: List of paths to knowledge files
        knowledge_urls: List of URLs to use as knowledge sources
        memory_id: ID for the memory to use
        history_id: ID for the history to use
        storage_type: Type of storage backend to use (sqlite, postgres, etc.)
        storage_connection: Connection string for the storage backend
        session_id: Session ID for resuming conversations
        user_id: User ID for personalization
        table_name: Name of the table/collection to use for storage
        mcp_server_url: URL for MCP server
        search_tool: Search tool to use (duckduckgo, google, etc.)
        firecrawl: Whether to use Firecrawl for web crawling
        firecrawl_api_key: API key for Firecrawl
        knowledge_base: Knowledge base instance to use
        search_knowledge: Whether to search the knowledge base
        team_name: Name for the team
        team_mode: Team coordination mode ("coordinate" or "relay")
        **kwargs: Additional keyword arguments for the agents
        
    Returns:
        An Agno Team instance with integrated storage capabilities
    """
    logger.info(f"Initializing financial modeling team with provider={provider}, model={model_id}")
    
    # Model configuration
    model_kwargs = {
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # Initialize storage if requested
    storage = None
    if storage_type and storage_connection:
        try:
            logger.info(f"Initializing {storage_type} storage with connection: {storage_connection[:20]}...")
            storage = initialize_storage(
                storage_type=storage_type,
                storage_connection=storage_connection,
                session_id=session_id,
                user_id=user_id,
                table_name=table_name,
                **kwargs
            )
            logger.info(f"Storage initialized successfully: {type(storage).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            logger.warning("Continuing without storage")
            storage = None
    
    # Initialize agents
    # Create searcher agent
    searcher = SearchingAgent(
        provider=provider,
        model_id=model_id,
        temperature=temperature,
        firecrawl=firecrawl,
        firecrawl_api_key=firecrawl_api_key,
        knowledge_base=knowledge_base,
        search_knowledge=search_knowledge,
        session_id=session_id,
        storage=storage,  # Pass storage object if available
        **model_kwargs
    )
    
    # Create assumption generator agent
    assumption_generator = AssumptionGeneratorAgent(
        provider=provider,
        model_id=model_id,
        temperature=temperature,
        firecrawl=firecrawl,
        firecrawl_api_key=firecrawl_api_key,
        knowledge_base=knowledge_base,
        search_knowledge=search_knowledge,
        session_id=session_id,
        storage=storage,  # Pass storage object if available
        **model_kwargs
    )
    
    # Create metrics deriver agent
    metrics_deriver = MetricsDerivingAgent(
        provider=provider,
        model_id=model_id,
        temperature=temperature,
        knowledge_base=knowledge_base,
        search_knowledge=search_knowledge,
        session_id=session_id,
        storage=storage,  # Pass storage object if available
        **model_kwargs
    )
    
    # Create financial modeler agent
    financial_modeler = FinancialModelingAgent(
        provider=provider,
        model_id=model_id,
        temperature=temperature,
        knowledge_base=knowledge_base,
        search_knowledge=search_knowledge,
        session_id=session_id,
        storage=storage,  # Pass storage object if available
        **model_kwargs
    )
    
    # Create a model for the team
    team_model = create_model(
        provider=provider,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Create team instructions
    team_instructions = [
        "You are a financial modeling team that works together to create comprehensive financial models.",
        "Use each team member's specialized expertise to build the best possible financial model.",
        "Searcher Agent: Researches relevant market data and industry benchmarks.",
        "Assumption Generator Agent: Creates realistic assumptions based on market research.",
        "Metrics Deriver Agent: Identifies the key metrics to include in the model.",
        "Financial Modeler Agent: Builds the actual financial model with calculations.",
        "Ensure all team members have the information they need to perform their tasks.",
        "Always provide clear, well-formatted responses with specific numerical values."
    ]

    # Create the Agno Team
    try:
        team = Team(
            name=team_name,
            members=[
                searcher.agent, 
                assumption_generator.agent, 
                metrics_deriver.agent, 
                financial_modeler.agent
            ],
            model=team_model,
            mode=team_mode,
            instructions=team_instructions,
            storage=storage,  # Pass storage to the team
            session_id=session_id,  # Ensure session continuity
            show_tool_calls=True,
            markdown=True
        )
        logger.info(f"Financial modeling team created successfully with {len(team.members)} agents")
        
        # Create a mapping from agent name to agent for backward compatibility
        # This ensures existing code that depends on the dictionary return still works
        agent_dict = {
            "searcher": searcher.agent,
            "assumption_generator": assumption_generator.agent,
            "metrics_deriver": metrics_deriver.agent,
            "financial_modeler": financial_modeler.agent
        }
        
        # Attach the dictionary to the team for backward compatibility
        team.agent_dict = agent_dict
        
        return team
        
    except Exception as e:
        logger.error(f"Failed to create team: {str(e)}")
        logger.warning("Falling back to returning agent dictionary")
        
        # For backward compatibility, return the dict of agents if team creation fails
        agent_team = {
            "searcher": searcher.agent,
            "assumption_generator": assumption_generator.agent,
            "metrics_deriver": metrics_deriver.agent,
            "financial_modeler": financial_modeler.agent
        }
        
        logger.info(f"Financial modeling team initialized with {len(agent_team)} agents")
        
        return agent_team 