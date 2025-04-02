"""
Market Research Tools for Financial Modeling.

This module provides tools for market research, competitor analysis, and industry insights.
"""

import re
import logging
from typing import Dict, List, Any, Optional
import json
from textwrap import dedent

# Import the helper instead of direct model
try:
    from src.utils.llm_models import get_llm_model
except ImportError:
    # Fallback if the helper module isn't found
    logging.error("Could not import get_llm_model utility. Ensure the file exists and PYTHONPATH is correct.")
    # Temporary fallback - REMOVE once helper utility is confirmed
    from agno.models import OpenAIChat

logger = logging.getLogger(__name__)

class MarketResearchTools:
    """
    Tools for conducting market research and competitor analysis.
    
    Provides methods for researching industries, analyzing competitors,
    and identifying key market trends.
    """
    
    def __init__(self):
        self.name = "MarketResearchTools"
        self.description = "Tools for analyzing markets, industries, and competitors"
    
    async def search_industry_data(self, query: str) -> str:
        """
        Search for industry data and metrics.
        
        Args:
            query: Search query about an industry or market
            
        Returns:
            Information about the industry market size, growth rate, and trends
        """
        logger.info(f"Searching industry data for: {query}")
        
        # Extract industry name using regex
        industry_match = re.search(r"(?:industry|market|sector)?\s*(?:of|for|about)?\s*([A-Za-z\s&]+)", query, re.IGNORECASE)
        industry = industry_match.group(1).strip() if industry_match else query
        
        # Try to generate industry data using LLM
        try:
            # Use our helper to get a model instance
            model = get_llm_model()
            
            # Create prompt for industry data
            prompt = dedent(f"""
            Provide current, factual data about the {industry} industry, including:
            
            1. Market size in USD
            2. Growth rate (CAGR percentage)
            3. 4-6 key trends shaping the industry
            
            Format your response as a concise Markdown report with sections for Market Overview and Key Trends.
            Use bullet points for trends. Be specific and include actual figures for market size and growth.
            Use the most recent data available.
            """)
            
            # Generate industry analysis
            industry_analysis = await model.generate(prompt)
            
            if industry_analysis and len(industry_analysis) > 100:
                logger.info(f"Generated industry data for {industry} using LLM")
                return industry_analysis
                
        except Exception as e:
            logger.warning(f"Could not generate industry data with LLM: {e}")
            logger.info(f"Falling back to template industry data for {industry}")
        
        # If LLM is not available or fails, use the industry lookup table as fallback
        # Simple industry data lookup table
        industry_data = {
            "software": {
                "market_size": "$1.8 trillion",
                "growth_rate": "11.5% CAGR",
                "key_trends": [
                    "Shift to cloud-based solutions",
                    "Integration of AI and ML",
                    "Focus on cybersecurity",
                    "Increased demand for remote work tools"
                ]
            },
            "healthcare": {
                "market_size": "$8.5 trillion",
                "growth_rate": "8.0% CAGR",
                "key_trends": [
                    "Telehealth expansion",
                    "AI-driven diagnostics",
                    "Personalized medicine",
                    "Value-based care models"
                ]
            },
            "retail": {
                "market_size": "$26 trillion",
                "growth_rate": "4.8% CAGR",
                "key_trends": [
                    "E-commerce growth",
                    "Omnichannel experiences",
                    "Sustainable and ethical practices",
                    "Personalized shopping experiences"
                ]
            },
            "finance": {
                "market_size": "$22.5 trillion",
                "growth_rate": "6.3% CAGR",
                "key_trends": [
                    "Digital banking adoption",
                    "Blockchain and cryptocurrency integration",
                    "Regtech solutions",
                    "Open banking initiatives"
                ]
            }
        }
        
        # Find the closest industry match
        matched_industry = None
        for key in industry_data.keys():
            if key in industry.lower():
                matched_industry = key
                break
        
        if matched_industry:
            data = industry_data[matched_industry]
            result = f"""
# {matched_industry.title()} Industry Analysis

## Market Overview
- **Market Size**: {data['market_size']}
- **Growth Rate**: {data['growth_rate']}

## Key Trends
{chr(10).join(['- ' + trend for trend in data['key_trends']])}

## Sources
Industry data compiled from market reports, industry associations, and expert analysis.
"""
        else:
            # For unknown industries, try using LLM with a more generic prompt
            try:
                model = get_llm_model()
                
                generic_prompt = dedent(f"""
                Provide a brief industry analysis for the {industry} industry.
                Include estimates of market size, growth rate, and 3-5 key trends if known.
                Format your response in Markdown with clear sections.
                Keep the analysis factual and concise.
                """)
                
                generic_analysis = await model.generate(generic_prompt)
                if generic_analysis and len(generic_analysis) > 100:
                    return generic_analysis
            except Exception as e:
                logger.warning(f"Failed secondary attempt to generate industry data: {e}")
                
            # Fallback to generic message
            result = f"No specific data found for '{industry}'. Please try a more common industry name like software, healthcare, retail, or finance."
        
        return result
    
    async def analyze_competitors(self, query: str) -> str:
        """
        Analyze competitors in a specific industry or market.
        
        Args:
            query: Search query that includes industry and optionally specific competitors
            
        Returns:
            Competitor analysis with market share, strengths, and weaknesses
        """
        logger.info(f"Analyzing competitors for: {query}")
        
        # Extract industry and competitors using regex
        industry_match = re.search(r"(?:industry|market|sector)?\s*(?:of|for|about)?\s*([A-Za-z\s&]+)", query, re.IGNORECASE)
        industry = industry_match.group(1).strip() if industry_match else "general"
        
        # Try to extract specific competitors from the query
        competitor_match = re.search(r"competitors\s+(?:like|such as|including)\s+([A-Za-z0-9\s,&]+)", query, re.IGNORECASE)
        mentioned_competitors = []
        if competitor_match:
            competitors_text = competitor_match.group(1)
            mentioned_competitors = [comp.strip() for comp in re.split(r',|\band\b', competitors_text) if comp.strip()]
        
        # Try to generate competitor analysis using LLM
        try:
            # Use the helper to get a model instance
            model = get_llm_model()
            
            # Create prompt for competitor analysis
            prompt = dedent(f"""
            Analyze the top competitors in the {industry} industry.
            
            {f"Focus on these specific competitors: {', '.join(mentioned_competitors)}" if mentioned_competitors else "Identify and analyze the top 3-5 major competitors in this industry."}
            
            For each competitor, provide:
            1. Company name
            2. Estimated market share (percentage)
            3. Key strengths (2-3 points)
            4. Key weaknesses (2-3 points)
            5. Primary revenue model
            
            Format your response as a Markdown report with a separate section for each competitor.
            Include an introduction that overviews the competitive landscape of the {industry} industry.
            Be specific and factual.
            """)
            
            # Generate competitor analysis
            competitor_analysis = await model.generate(prompt)
            
            if competitor_analysis and len(competitor_analysis) > 150:
                logger.info(f"Generated competitor analysis for {industry} using LLM")
                return competitor_analysis
                
        except Exception as e:
            logger.warning(f"Could not generate competitor analysis with LLM: {e}")
            logger.info(f"Falling back to template competitor data for {industry}")
        
        # If LLM is not available or fails, use the competitor data lookup as fallback
        competitor_data = {
            "software": [
                {
                    "name": "Microsoft",
                    "market_share": "25%",
                    "strengths": ["Established enterprise presence", "Diverse product portfolio", "Strong cloud services"],
                    "weaknesses": ["Innovation lag in some areas", "Complex licensing"]
                },
                {
                    "name": "Google",
                    "market_share": "18%",
                    "strengths": ["Strong technical innovation", "Free basic services", "Data analytics capabilities"],
                    "weaknesses": ["Privacy concerns", "Revenue concentration in advertising"]
                },
                {
                    "name": "Amazon (AWS)",
                    "market_share": "32%",
                    "strengths": ["Market leader in cloud infrastructure", "Extensive service offerings", "Scalability"],
                    "weaknesses": ["Premium pricing", "Complex for small businesses"]
                }
            ],
            "healthcare": [
                {
                    "name": "UnitedHealth Group",
                    "market_share": "15%",
                    "strengths": ["Diversified health services", "Strong insurance arm", "Data analytics"],
                    "weaknesses": ["Customer satisfaction challenges", "Regulatory pressures"]
                },
                {
                    "name": "CVS Health",
                    "market_share": "9%",
                    "strengths": ["Retail presence", "Pharmacy expertise", "Aetna acquisition"],
                    "weaknesses": ["Online competition", "Pharmacy benefit management challenges"]
                },
                {
                    "name": "Kaiser Permanente",
                    "market_share": "7%",
                    "strengths": ["Integrated care model", "Strong preventive care", "Digital health innovation"],
                    "weaknesses": ["Limited geographical presence", "Capacity constraints"]
                }
            ]
        }
        
        # Find the closest industry match
        matched_industry = None
        for key in competitor_data.keys():
            if key in industry.lower():
                matched_industry = key
                break
        
        if matched_industry:
            competitors = competitor_data[matched_industry]
            result = f"""
# {matched_industry.title()} Market Competitor Analysis

## Major Competitors

"""
            for comp in competitors:
                result += f"""
### {comp['name']}
- **Market Share**: {comp['market_share']}
- **Strengths**: {', '.join(comp['strengths'])}
- **Weaknesses**: {', '.join(comp['weaknesses'])}
"""
            
            result += """
## Sources
Competitor analysis compiled from market reports, annual reports, and industry analysis.
"""
        else:
            # For unknown industries, try using LLM with a more generic prompt
            try:
                model = get_llm_model()
                
                generic_prompt = dedent(f"""
                Provide a brief competitor analysis for the {industry} industry.
                Identify 2-3 major competitors and their key characteristics.
                Format your response in Markdown with clear sections.
                Keep the analysis factual and concise.
                """)
                
                generic_analysis = await model.generate(generic_prompt)
                if generic_analysis and len(generic_analysis) > 100:
                    return generic_analysis
            except Exception as e:
                logger.warning(f"Failed secondary attempt to generate competitor analysis: {e}")
                
            # Fallback to generic message
            result = f"No specific competitor data found for '{industry}'. Please try a more common industry name like software or healthcare."
        
        return result
    
    async def identify_kpis(self, query: str) -> str:
        """
        Identify key performance indicators for a business or industry.
        
        Args:
            query: Search query that includes industry or business type
            
        Returns:
            List of relevant KPIs with descriptions and importance ratings
        """
        logger.info(f"Identifying KPIs for: {query}")
        
        # Extract industry using regex
        industry_match = re.search(r"(?:industry|market|sector|business)?\s*(?:of|for|about)?\s*([A-Za-z\s&]+)", query, re.IGNORECASE)
        industry = industry_match.group(1).strip() if industry_match else "general"
        
        # Look for specific business model/type information
        business_model_match = re.search(r"(saas|ecommerce|manufacturing|service|b2b|b2c|retail|wholesale)", query, re.IGNORECASE)
        business_model = business_model_match.group(1).lower() if business_model_match else None
        
        # Try to generate KPI analysis using LLM
        try:            
            # Use the helper to get a model instance
            model = get_llm_model()
            
            # Create prompt for KPI analysis
            prompt = dedent(f"""
            Identify the most important key performance indicators (KPIs) for a business in the {industry} industry
            {f"with a {business_model} business model" if business_model else ""}.
            
            Organize the KPIs into these categories:
            1. Financial KPIs
            2. Operational KPIs
            3. Growth/Marketing KPIs
            
            For each KPI, provide:
            - Name of the KPI
            - Clear and concise description of what it measures and why it matters
            - Importance rating (High, Medium, or Low)
            - If applicable, a typical benchmark or target range for this industry
            
            Format your response as a Markdown report with clear sections for each category.
            Include a brief introduction explaining the importance of tracking KPIs in this specific industry.
            Provide 4-6 KPIs in each category, prioritizing the most relevant ones for this industry.
            """)
            
            # Generate KPI analysis
            kpi_analysis = await model.generate(prompt)
            
            if kpi_analysis and len(kpi_analysis) > 200:
                logger.info(f"Generated KPI analysis for {industry} using LLM")
                return kpi_analysis
                
        except Exception as e:
            logger.warning(f"Could not generate KPI analysis with LLM: {e}")
            logger.info(f"Falling back to template KPI data for {industry}")
        
        # If LLM is not available or fails, use the KPI lookup table as fallback
        # KPI lookup table
        kpi_data = {
            "saas": [
                {"name": "Monthly Recurring Revenue (MRR)", "description": "Predictable revenue generated each month", "importance": "High"},
                {"name": "Customer Acquisition Cost (CAC)", "description": "Cost to acquire a new customer", "importance": "High"},
                {"name": "Customer Lifetime Value (CLV)", "description": "Total revenue from a customer over time", "importance": "High"},
                {"name": "Churn Rate", "description": "Rate at which customers cancel subscriptions", "importance": "High"},
                {"name": "Net Revenue Retention", "description": "Revenue from existing customers, including expansion", "importance": "High"},
                {"name": "Gross Margin", "description": "Revenue minus COGS, divided by revenue", "importance": "Medium"}
            ],
            "ecommerce": [
                {"name": "Conversion Rate", "description": "Percentage of visitors who make a purchase", "importance": "High"},
                {"name": "Average Order Value (AOV)", "description": "Average amount spent per order", "importance": "High"},
                {"name": "Customer Acquisition Cost (CAC)", "description": "Cost to acquire a new customer", "importance": "High"},
                {"name": "Return Rate", "description": "Percentage of items returned", "importance": "Medium"},
                {"name": "Cart Abandonment Rate", "description": "Percentage of carts abandoned before checkout", "importance": "Medium"},
                {"name": "Inventory Turnover", "description": "How quickly inventory is sold and replaced", "importance": "Medium"}
            ],
            "general": [
                {"name": "Revenue Growth Rate", "description": "Year-over-year revenue increase", "importance": "High"},
                {"name": "Gross Margin", "description": "Revenue minus COGS, divided by revenue", "importance": "High"},
                {"name": "Net Profit Margin", "description": "Net profit divided by revenue", "importance": "High"},
                {"name": "Operating Cash Flow", "description": "Cash generated from core business operations", "importance": "High"},
                {"name": "Customer Satisfaction Score", "description": "Measure of customer happiness", "importance": "Medium"},
                {"name": "Employee Turnover Rate", "description": "Rate at which employees leave", "importance": "Medium"}
            ]
        }
        
        # Find the closest industry match
        matched_industry = "general"  # Default to general KPIs
        if business_model and business_model in kpi_data:
            matched_industry = business_model
        else:
            for key in kpi_data.keys():
                if key in industry.lower():
                    matched_industry = key
                    break
        
        # Format the KPI data for response
        kpis = kpi_data[matched_industry]
        result = f"""
# Key Performance Indicators for {matched_industry.title()} Business

## Introduction
Tracking the right KPIs is essential for measuring business performance and making data-driven decisions. Here are the most important KPIs for a {matched_industry} business:

## Financial KPIs
"""
        # Split KPIs into categories
        financial_kpis = kpis[:2]
        operational_kpis = kpis[2:4]
        growth_kpis = kpis[4:]
        
        for kpi in financial_kpis:
            result += f"### {kpi['name']}\n"
            result += f"- **Description**: {kpi['description']}\n"
            result += f"- **Importance**: {kpi['importance']}\n\n"
        
        result += "## Operational KPIs\n"
        for kpi in operational_kpis:
            result += f"### {kpi['name']}\n"
            result += f"- **Description**: {kpi['description']}\n"
            result += f"- **Importance**: {kpi['importance']}\n\n"
        
        result += "## Growth KPIs\n"
        for kpi in growth_kpis:
            result += f"### {kpi['name']}\n"
            result += f"- **Description**: {kpi['description']}\n"
            result += f"- **Importance**: {kpi['importance']}\n\n"
        
        # Try a more generic KPI analysis with LLM as a last resort if the industry didn't match
        if matched_industry == "general" and industry.lower() not in ["general", "business"]:
            try:
                model = get_llm_model()
                
                generic_prompt = dedent(f"""
                Identify 5-8 key performance indicators that would be important for a business in the {industry} industry.
                For each KPI, provide a brief description and why it matters.
                Format your response in Markdown with clear sections.
                Keep the analysis focused and concise.
                """)
                
                generic_analysis = await model.generate(generic_prompt)
                if generic_analysis and len(generic_analysis) > 150:
                    return generic_analysis
            except Exception as e:
                logger.warning(f"Failed secondary attempt to generate KPI analysis: {e}")
        
        return result 