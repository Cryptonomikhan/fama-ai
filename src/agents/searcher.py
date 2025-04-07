from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.thinking import ThinkingTools
from agno.tools.firecrawl import FirecrawlTools
from src.models.factory import create_model
from src.tools.website_scraper import WebsiteScraperTools
import logging
from textwrap import dedent
from typing import Any, Optional, List
import os
from dotenv import load_dotenv
from src.knowledge.logging import wrap_knowledge_base

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class SearchingAgent:
    """
    Agent specialized in searching for information both online and in knowledge bases.
    
    This agent uses web search tools, web scraping, and knowledge base searching to gather 
    comprehensive information on a topic. It can balance between using a provided knowledge 
    base for domain-specific information and searching the web for up-to-date information.
    
    The agent's output is structured to be easily used by other agents in the financial 
    modeling process.
    """
    def __init__(
        self,
        provider: str = "formation",
        model_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        firecrawl: bool = False,
        firecrawl_api_key: Optional[str] = None,
        additional_tools: List = None,
        knowledge_base: Optional[Any] = None,
        search_knowledge: bool = True,
        session_id: Optional[str] = None,
        storage: Optional[Any] = None,
        **kwargs: Any
    ):
        """
        Initialize a SearchingAgent with the specified parameters.
        
        Args:
            provider: Model provider (e.g., "openai", "formation", "anthropic")
            model_id: ID of the model to use
            temperature: Temperature for model generation (higher = more creative, lower = more deterministic)
            max_tokens: Maximum tokens to generate in responses
            firecrawl: Whether to use Firecrawl for web crawling
            firecrawl_api_key: API key for Firecrawl (if None, tries to get from environment)
            additional_tools: Additional tools to give the agent
            knowledge_base: Knowledge base instance to use for semantic search
            search_knowledge: Whether to search the knowledge base for relevant information
            session_id: Session ID for knowledge tracking across agents
            storage: Optional storage backend for maintaining agent state across sessions
            **kwargs: Additional keyword arguments for the model
        """
        
        logger.info("Initializing SearchingAgent")
        model = create_model(
            provider=provider,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Build tools list based on availability
        tools = [ThinkingTools(), DuckDuckGoTools()]
        
        # Always add our custom WebsiteScraperTools
        tools.append(WebsiteScraperTools())
        
        # Conditionally add FirecrawlTools if requested
        if firecrawl:
            firecrawl_api_key = firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY")
            if firecrawl_api_key:
                logger.info("Adding FirecrawlTools to SearchingAgent")
                tools.append(FirecrawlTools(api_key=firecrawl_api_key))
            else:
                logger.warning("Firecrawl was requested but no API key was provided. Will not add FirecrawlTools.")
        
        # Add any additional tools provided
        if additional_tools:
            for tool in additional_tools:
                tools.append(tool)
                logger.info(f"Added additional tool to SearchingAgent: {tool.name}")
        
        # Instructions for the agent
        instructions = dedent("""
        # Instructions on Conducting Comprehensive Research
        
        ## General Research Approach
        - Research the investment opportunity thoroughly using all available tools
        - First search for general information about the type of investment
        - Then research specific performance characteristics of the asset class
        - Gather current market data including:
          * Current prices or rates
          * Historical performance
          * Expert projections
          * Comparable investments
          * Market trends
        - Focus on quantitative data that can be used in financial modeling
        - Always cite your sources and include URLs when possible
        
        ## Financial Data to Prioritize
        - Acquisition costs
        - Expected revenue generation mechanisms
        - Operating expense ratios
        - Maintenance costs
        - Historical appreciation/depreciation rates
        - Vacancy or utilization rates (depending on asset class)
        - Seasonality factors
        - Regulatory or tax considerations
        - Liquidity and market depth
        - Recent comparable transactions
        
        ## Using the Knowledge Base
        - When a knowledge base is available, search it for:
          * Asset-specific performance data
          * Proprietary market intelligence
          * Historical transaction records
          * Industry benchmarks
        - Cross-reference knowledge base findings with current web data
        - Always prefer more recent information 
        - Combine multiple sources to build a comprehensive view
        
        ## Effective Web Searching
        - Use precise search queries that include specific terms related to:
          * The exact investment vehicle type
          * Current year + "data" or "performance"
          * Industry-specific metrics and benchmarks
          * Geographic specificity when relevant
        - Evaluate source credibility before including information
        - Prefer primary sources and industry publications over general news
        - Use the web scraper tool when you need detailed information from specific pages
        - Gather numerical data, not just qualitative assessments
        
        ## Organizing Your Findings
        - Structure your research in clear categories
        - Present information in order of relevance and reliability
        - Clearly separate facts from projections or estimates
        - Format numerical data consistently
        - Specify data sources for each major finding
        - Highlight any significant data gaps or contradictions
        
        ## Handling Data Inconsistency
        - When you encounter conflicting data:
          * Note the discrepancy
          * Compare source credibility
          * Consider recency of information
          * Look for additional sources to validate
          * Present the range of findings
        - Be transparent about uncertainty
        
        ## Numerical Data Presentation
        - Always include units with numerical data (%, $, years, etc.)
        - Present ranges when appropriate rather than single point estimates
        - Note the timeframe for any performance data
        - Convert all monetary values to consistent currency
        - Use consistent decimal precision
        
        ## Scope and Limitations
        - Focus on directly relevant information for financial modeling
        - Avoid digressing into tangential topics
        - Maintain objectivity; don't showcase only positive information
        - Acknowledge limitations in available data
        - Suggest where additional research might be valuable
        
        Remember: Your research will directly inform the assumptions used in the financial model, so accuracy, comprehensiveness, and proper citing of sources are critical.
        """)
        
        if knowledge_base and search_knowledge:
            # Wrap knowledge base with logging if it hasn't been wrapped already
            if session_id and not hasattr(knowledge_base, '_kb_logging_wrapped'):
                knowledge_base = wrap_knowledge_base(
                    knowledge_base, 
                    agent_name="SearchingAgent",
                    session_id=session_id
                )
                knowledge_base._kb_logging_wrapped = True
                logger.info("Knowledge base wrapped with logging for SearchingAgent")

        self.agent = Agent(
            name="Web Search Agent",
            model=model,
            tools=tools,
            role=dedent("""\
                Your role is to gather information related to the investment
                opportunity that is relevant to building a sophisticated
                and high quality financial model for the opportunity.\
            """),
            description=dedent("""\
                You are Fama Datagatherer, a distinguished research assisstant
                that is well known for searching to the end of the earth to
                find relevant inforamtion for a given subject. Today you are
                aiding in building a sophisticated financial model for an
                investment opportunity. You search the web to find information
                that can be used to derive assumptions, determine key metrics,
                risk factors, and other key components to a financial model.
                Once you've gathered the necessary information you structure it
                in a way that makes it usable by your teammates and others.

                You always organize data and provide sources for it, including
                links to webpages where you found the data.
            """),
            instructions=instructions,
            knowledge_base=knowledge_base,
            search_knowledge=search_knowledge,
            show_tool_calls=True,
            markdown=True,
            storage=storage
        )


if __name__ == "__main__":

    searcher = SearchingAgent(
        provider="openai",
        model_id="gpt-4o"
    )

    searcher.agent.print_response("Gather the information necessary to build a financial model for a 3 year timeframe for a small real estate fund that invests in AI server farms", stream=True)
