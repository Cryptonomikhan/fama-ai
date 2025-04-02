"""
Research Agent for Financial Modeling.
This agent is responsible for analyzing business context, market research,
and competitor analysis to understand the business opportunity.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import asyncio
from datetime import datetime
import json
import re
from textwrap import dedent

# Plan to integrate with Agno's model system for advanced reasoning
# from agno.models import OpenAIModel, AnthropicModel, GeminiModel, DeepseekModel
# This would be imported when using actual Agno Framework

from agno.agent import Agent
from agno.tools import ToolSpec, tool, CodeExecutionTool

# Assuming the helper is in src/utils/llm_models.py relative to project root
# Adjust import path if necessary
try:
    from src.utils.llm_models import get_llm_model
except ImportError:
    # Fallback or error handling if the util module isn't found
    logging.error("Could not import get_llm_model from src.utils.llm_models. Ensure the file exists and PYTHONPATH is correct.")
    # As a temporary fallback, you might import OpenAIChat directly, but it defeats the purpose
    from agno.models.openai import OpenAIChat as get_llm_model # Temporary fallback - REMOVE once util is confirmed

logger = logging.getLogger(__name__)

class ResearchAgent(Agent):
    """
    Agent specializing in deep research and market analysis.
    
    This agent gathers business context, performs competitor analysis,
    and identifies key KPIs and financial metrics for the business.
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        tools: Optional[List[Union[ToolSpec, callable]]] = None,
        **kwargs: Any,
    ):
        _model = model or get_llm_model()
        _tools = tools or [
            # Example: Add relevant tools here if needed, or they can be passed during run
        ]

        super().__init__(
            model=_model,
            tools=_tools,
            name="MarketResearchAnalyst",
            description="Expert AI agent specialized in deep market research, competitor analysis, and identifying key business metrics.",
            instructions=dedent("""\
                You are an expert Market Research Analyst. Your goal is to provide comprehensive, data-driven insights.
                1.  Thoroughly analyze the provided industry, region, and competitors.
                2.  Use available tools to gather real-time data if necessary.
                3.  Structure your analysis clearly with sections for Market Overview, Competitor Landscape, Key KPIs, and Revenue Models.
                4.  Provide actionable recommendations and highlight key opportunities and risks.
                5.  Format outputs as requested, typically JSON.
                6.  If data is unavailable or ambiguous, state it clearly and provide reasoned estimates or qualitative assessments.
            """),
            add_datetime_to_instructions=True,
            show_tool_calls=kwargs.pop('show_tool_calls', True), # Default to True, allow override
            markdown=kwargs.pop('markdown', True), # Default to True, allow override
            **kwargs, # Pass remaining kwargs to parent Agent class
        )
        self.code_execution_tool = CodeExecutionTool()

    async def _call_llm_for_json(self, prompt: str, retries: int = 2) -> Dict[str, Any]:
        """Helper function to call the LLM and parse JSON output with retries."""
        for attempt in range(retries + 1):
            try:
                # Use the agent's configured model
                response = await self.run_async(prompt)

                # Extract JSON part - improved regex to handle variations
                json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Fallback: assume the entire response might be JSON if no markdown fences
                    json_str = response.strip()
                    if not (json_str.startswith('{') and json_str.endswith('}')):
                         # If it doesn't look like JSON, raise error for retry
                         raise json.JSONDecodeError("No valid JSON block found in response", json_str, 0)

                parsed_json = json.loads(json_str)
                logger.info("Successfully parsed JSON response from LLM.")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON from LLM response: {e}. Response:\n{response}")
                if attempt == retries:
                    logger.error("Max retries reached for JSON parsing.")
                    # Fallback: return error structure or raise specific exception
                    return {"error": "Failed to generate valid JSON analysis after multiple attempts."}
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: An unexpected error occurred during LLM call: {e}")
                if attempt == retries:
                     return {"error": f"An unexpected error occurred: {e}"}
        # Should not be reached if retries >= 0
        return {"error": "LLM call failed after retries."}

    async def analyze(
        self,
        business_name: str,
        business_description: str,
        industry: str,
        competitors: Optional[List[str]] = None,
        region: Optional[str] = None,
        existing_revenue_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform deep research on a business opportunity.
        
        Args:
            business_name: Name of the business
            business_description: Description of the business
            industry: Industry or sector the business operates in
            competitors: List of key competitors
            region: Geographic region of operation
            existing_revenue_model: Current revenue model if available
            
        Returns:
            Dictionary containing research findings and analysis
        """
        logger.info(f"Starting deep research for: {business_name}")
        
        # In a real implementation, these functions would use AI models for analysis
        market_analysis = await self._analyze_market(industry, region)
        competitor_analysis = await self._analyze_competitors(competitors, industry)
        kpi_analysis = await self._identify_key_kpis(business_description, industry, market_analysis)
        
        # Determine recommended revenue models based on research
        revenue_models = await self._recommend_revenue_models(
            business_description,
            industry,
            market_analysis,
            competitor_analysis,
            existing_revenue_model
        )
        
        # Combine all research elements into a comprehensive report
        research_results = {
            "business_profile": {
                "name": business_name,
                "description": business_description,
                "industry": industry,
                "region": region or "Global"
            },
            "market_analysis": market_analysis,
            "competitor_analysis": competitor_analysis,
            "key_performance_indicators": kpi_analysis,
            "recommended_revenue_models": revenue_models,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Completed research analysis for: {business_name}")
        return research_results
    
    async def _analyze_market(self, industry: str, region: Optional[str]) -> Dict[str, Any]:
        """Analyze the market for the given industry and region using LLM."""
        logger.info(f"Analyzing market for industry: {industry}, region: {region or 'Global'}")

        prompt = dedent(f"""\
            Perform a detailed market analysis for the {industry} industry in {region or 'the global'} market.

            Provide the following information:
            1. Market size (in USD, specify year)
            2. Annual growth rate (CAGR percentage, specify period)
            3. 3-5 key market trends
            4. 3-5 market challenges
            5. 3-5 market opportunities

            Format your response as a JSON object enclosed in triple backticks (```json ... ```) with the following structure:
            {{
                "market_size": {{ "value": <number>, "unit": "USD", "year": <number> }},
                "growth_rate": {{ "value": <number>, "unit": "CAGR %", "period": "<start_year>-<end_year>" }},
                "trends": ["<trend1>", "<trend2>", ...],
                "challenges": ["<challenge1>", "<challenge2>", ...],
                "opportunities": ["<opportunity1>", "<opportunity2>", ...]
            }}
            Ensure all numeric values are represented as numbers, not strings.
        """)

        analysis = await self._call_llm_for_json(prompt)
        # Basic validation or default values
        if "error" in analysis:
             logger.warning(f"LLM failed to generate market analysis. Using defaults. Error: {analysis['error']}")
             # Provide more specific defaults based on context if possible
             return {
                 "market_size": {"value": 0, "unit": "USD", "year": None}, "growth_rate": {"value": 0, "unit": "CAGR %", "period": None},
                 "trends": ["Data unavailable"], "challenges": ["Data unavailable"], "opportunities": ["Data unavailable"]
            }

        logger.info(f"Market analysis generated for {industry}")
        return analysis
    
    async def _analyze_competitors(
        self,
        competitors: Optional[List[str]],
        industry: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze competitors and their market positioning using LLM."""
        logger.info("Performing competitor analysis")

        identified_competitors = competitors or []
        competitor_query_part = ""
        if identified_competitors:
             competitor_query_part = f"Focus specifically on these known competitors if possible: {', '.join(identified_competitors)}."
        else:
            competitor_query_part = "Identify the top 3-5 key competitors in this industry."


        prompt = dedent(f"""\
            Analyze the competitive landscape for the {industry} industry.
            {competitor_query_part}

            For each key competitor (up to 5), provide the following:
            1. Company Name
            2. Estimated Market Share (%) - Provide a range if exact number is unknown.
            3. Key Strengths (2-3 points)
            4. Key Weaknesses (2-3 points)
            5. Recent notable activities or strategic moves (1-2 points)

            Format your response as a JSON object enclosed in triple backticks (```json ... ```) with the following structure:
            {{
                "competitors": [
                    {{
                        "name": "<competitor_name>",
                        "market_share_percent": "<estimated_percentage_or_range>",
                        "strengths": ["<strength1>", "<strength2>", ...],
                        "weaknesses": ["<weakness1>", "<weakness2>", ...],
                        "recent_activity": ["<activity1>", "<activity2>", ...]
                    }},
                    ...
                ]
            }}
            If specific data like market share is unavailable, indicate "Unavailable" or provide a qualitative assessment.
        """)

        analysis = await self._call_llm_for_json(prompt)

        if "error" in analysis or not analysis.get("competitors"):
             logger.warning(f"LLM failed to generate competitor analysis. Using defaults. Error: {analysis.get('error', 'No competitors found')}")
             return {"competitors": [{"name": "Unknown", "market_share_percent": "Unavailable", "strengths": [], "weaknesses": [], "recent_activity": []}]}

        logger.info(f"Competitor analysis generated for {industry}")
        return analysis
    
    async def _identify_key_kpis(
        self,
        business_description: str,
        industry: str,
        market_analysis: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identify key performance indicators relevant to the business using LLM."""
        logger.info("Identifying key performance indicators")

        # Extract market context safely
        market_size = market_analysis.get('market_size', {}).get('value', 'Unknown')
        growth_rate = market_analysis.get('growth_rate', {}).get('value', 'Unknown')

        prompt = dedent(f"""\
            Identify the most critical Key Performance Indicators (KPIs) for a business with the following characteristics:

            Industry: {industry}
            Business Description: {business_description}
            Market Size: {market_size}
            Market Growth: {growth_rate}

            Provide KPIs relevant to these categories:
            1. Financial Performance (e.g., MRR, CAC, LTV, Burn Rate, Gross Margin)
            2. Customer/User Engagement (e.g., Active Users, Churn Rate, Conversion Rate)
            3. Operational Efficiency (e.g., Customer Support Tickets, Uptime)

            For each KPI, provide:
            - Name: The name of the KPI
            - Description: A brief explanation of what it measures and why it's important for this business.
            - Category: (Financial, Customer, Operational)
            - Typical Benchmark/Goal (Optional): A typical industry benchmark or goal, if available (e.g., "Aim for <3% Churn"). State if highly variable.

            Format your response as a JSON object enclosed in triple backticks (```json ... ```) with the structure:
            {{
                "kpis": [
                    {{
                        "name": "<kpi_name>",
                        "description": "<explanation>",
                        "category": "<Financial|Customer|Operational>",
                        "benchmark_goal": "<optional_benchmark_info>"
                    }},
                    ...
                ]
            }}
            Select the top 2-4 most relevant KPIs per category for this specific business profile.
        """)

        analysis = await self._call_llm_for_json(prompt)

        if "error" in analysis or not analysis.get("kpis"):
            logger.warning(f"LLM failed to generate KPI analysis. Using defaults. Error: {analysis.get('error', 'No KPIs identified')}")
            return {"kpis": [{"name": "Data Unavailable", "description": "", "category": "Unknown", "benchmark_goal": ""}]}

        logger.info(f"KPI identification completed for: {business_description}")
        return analysis
    
    async def _recommend_revenue_models(
        self,
        business_description: str,
        industry: str,
        market_analysis: Dict[str, Any],
        competitor_analysis: Dict[str, List[Dict[str, Any]]],
        existing_revenue_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Recommend suitable revenue models based on research using LLM."""
        logger.info("Analyzing and recommending optimal revenue models")

        # Prepare context safely
        market_size = market_analysis.get('market_size', {}).get('value', 'Unknown')
        growth_rate = market_analysis.get('growth_rate', {}).get('value', 'Unknown')
        trends = market_analysis.get('trends', [])
        competitors_summary = [f"{c.get('name', 'Unknown')} (Share: {c.get('market_share_percent', 'N/A')})"
                               for c in competitor_analysis.get('competitors', [])]

        prompt = dedent(f"""\
            Recommend and evaluate potential revenue models for a business with the following profile:

            Industry: {industry}
            Business Description: {business_description}
            Market Size: {market_size}
            Market Growth: {growth_rate}
            Key Market Trends: {', '.join(trends) if trends else 'N/A'}
            Key Competitors: {', '.join(competitors_summary) if competitors_summary else 'N/A'}
            Existing Revenue Model (if any): {existing_revenue_model or 'None specified'}

            Consider standard models like Subscription (Tiered/Usage-based), Transaction Fees, Advertising, Licensing, Freemium, Direct Sales, Affiliate Marketing, etc.

            Provide the following:
            1. Recommended Models: List the top 2-3 most suitable revenue models.
            2. Rationale: For each recommended model, explain why it fits the business context (industry, description, market).
            3. Potential Challenges: Briefly list 1-2 potential challenges for each recommended model.
            4. Hybrid Opportunities: Suggest if combining models could be beneficial.

            Format your response as a JSON object enclosed in triple backticks (```json ... ```) with the structure:
            {{
                "recommended_models": [
                    {{
                        "model_name": "<e.g., Subscription>",
                        "rationale": "<explanation>",
                        "challenges": ["<challenge1>", ...]
                    }},
                    ...
                ],
                "hybrid_opportunities": "<suggestion_if_applicable>"
            }}
        """)

        analysis = await self._call_llm_for_json(prompt)

        if "error" in analysis or not analysis.get("recommended_models"):
            logger.warning(f"LLM failed to recommend revenue models. Using defaults. Error: {analysis.get('error', 'No models recommended')}")
            return {
                "recommended_models": [{"model_name": "Data Unavailable", "rationale": "", "challenges": []}],
                "hybrid_opportunities": "Data Unavailable"
            }

        logger.info(f"Revenue model recommendations generated for: {business_description}")
        return analysis

    async def run(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        # ... (Rest of the run method, potentially orchestrating the above _ methods) ...
        # This method might need adjustment based on how the agent is triggered (e.g., via API endpoint)
        # For now, assume it's called with specific parameters or a general query that needs parsing.
        logger.info(f"ResearchAgent received query: {query}")
        # Example: Parse query or expect specific inputs via kwargs
        industry = kwargs.get("industry", "general technology") # Example default
        business_desc = kwargs.get("business_description", "a sample tech startup") # Example default
        region = kwargs.get("region", None)
        competitors = kwargs.get("competitors", None)

        market_analysis = await self._analyze_market(industry, region)
        competitor_analysis = await self._analyze_competitors(competitors, industry)
        key_kpis = await self._identify_key_kpis(business_desc, industry, market_analysis)
        revenue_models = await self._recommend_revenue_models(business_desc, industry, market_analysis, competitor_analysis)

        return {
            "market_analysis": market_analysis,
            "competitor_analysis": competitor_analysis,
            "key_kpis": key_kpis,
            "revenue_models": revenue_models,
        }


# Example of how to potentially use the agent (e.g., in an API route)
async def example_usage():
    agent = ResearchAgent()
    results = await agent.run(
        query="Analyze the SaaS market for a CRM startup targeting SMBs in North America",
        industry="SaaS CRM",
        business_description="A new CRM startup focused on ease-of-use for small-to-medium businesses.",
        region="North America",
        competitors=["Salesforce", "HubSpot", "Zoho CRM"] # Optional
    )
    import pprint
    pprint.pprint(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 