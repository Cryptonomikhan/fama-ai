"""
Investment Context Analyzer.

This module provides tools for analyzing investment contexts and determining
the appropriate financial modeling approach based on the type of investment opportunity.
"""

import logging
import json
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

class ContextAnalyzerTools:
    """
    Tools for analyzing investment contexts and structuring financial models.
    
    Uses AI reasoning to determine the appropriate financial modeling approach,
    metrics, and structures based on the specific type of investment opportunity.
    """
    
    def __init__(self):
        self.name = "ContextAnalyzerTools"
        self.description = "Tools for analyzing investment contexts and determining financial modeling approaches"
    
    async def analyze_investment_type(self, query: str) -> str:
        """
        Analyze the investment opportunity and determine its type and appropriate modeling approach.
        
        Args:
            query: Description of the investment opportunity
            
        Returns:
            Analysis of the investment type and recommended modeling approach
        """
        logger.info("Analyzing investment type")
        
        # Instead of using predefined logic, we'll have the LLM reason about this
        # The method itself just needs to return the prompt to be analyzed by the LLM
        
        prompt = f"""
# Investment Opportunity Analysis

## Context
{query}

Please analyze this investment opportunity and determine:

1. **Investment Type Classification**: What type of investment is this? (e.g., Startup, Established Business, REIT, Tokenized Asset, SPV, Private Credit, etc.)
2. **Key Characteristics**: What are the defining characteristics of this investment?
3. **Recommended Financial Modeling Approach**: What financial modeling approaches are most appropriate?
4. **Critical Metrics**: What specific financial metrics and KPIs should be prioritized?
5. **Data Requirements**: What data would be needed to properly analyze this opportunity?
6. **Risk Factors**: What specific risks should be modeled and analyzed?

Provide a comprehensive analysis with specific recommendations for how to approach the financial modeling.
"""
        return prompt
    
    async def determine_revenue_model(self, query: str) -> str:
        """
        Analyze a business or investment and determine the most appropriate revenue model(s).
        
        Args:
            query: Description of the business or investment
            
        Returns:
            Analysis of appropriate revenue models with recommendations
        """
        logger.info("Determining appropriate revenue model")
        
        # Instead of predefined revenue models, we'll have the LLM reason about this
        prompt = f"""
# Revenue Model Analysis

## Context
{query}

Please analyze this business or investment opportunity and determine:

1. **Appropriate Revenue Model(s)**: What revenue model(s) would be most appropriate? Consider:
   - Subscription
   - Pay-As-You-Go/Usage-Based
   - One-Time Purchase
   - Freemium
   - Marketplace/Transaction Fee
   - Advertising
   - Licensing/Royalties
   - Rental/Leasing Income
   - Interest Income
   - Dividend Income
   - Capital Appreciation
   - Carried Interest
   - Distribution Models
   - Any other appropriate models

2. **Revenue Model Justification**: Why are these models most appropriate for this specific opportunity?
3. **Revenue Streams**: What specific revenue streams would this model generate?
4. **Implementation Considerations**: What would be required to successfully implement this revenue model?
5. **Hybrid Approach**: Would a hybrid approach combining multiple revenue models be appropriate?

Provide a comprehensive analysis with specific recommendations.
"""
        return prompt
    
    async def identify_investment_metrics(self, query: str) -> str:
        """
        Identify the most relevant financial metrics for a specific investment type.
        
        Args:
            query: Description of the investment type and context
            
        Returns:
            List of relevant financial metrics with definitions and importance
        """
        logger.info("Identifying investment metrics")
        
        # Use the LLM to determine the appropriate metrics for this specific investment type
        prompt = f"""
# Investment Metrics Analysis

## Context
{query}

Please identify the most appropriate financial metrics for analyzing this specific investment opportunity:

1. **Primary Metrics**: What are the 5-7 most critical financial metrics for this type of investment?
2. **Definitions**: Provide clear definitions for each metric.
3. **Calculation Methods**: How is each metric calculated?
4. **Benchmarks**: What are typical benchmark values or ranges for these metrics in this investment category?
5. **Importance**: Why are these metrics particularly important for this investment type?
6. **Leading Indicators**: Which metrics serve as early indicators of performance?
7. **Lagging Indicators**: Which metrics confirm long-term performance?
8. **Risk Metrics**: What specific risk-related metrics should be analyzed?

Organize the metrics by category (e.g., profitability, liquidity, risk, etc.) and provide a comprehensive analysis.
"""
        return prompt
    
    async def design_scenario_analysis(self, query: str) -> str:
        """
        Design scenario analysis parameters for a specific investment opportunity.
        
        Args:
            query: Description of the investment opportunity
            
        Returns:
            Scenario analysis design with parameters for base, optimistic, and pessimistic cases
        """
        logger.info("Designing scenario analysis")
        
        # Use the LLM to design an appropriate scenario analysis for this investment type
        prompt = f"""
# Scenario Analysis Design

## Context
{query}

Please design a comprehensive scenario analysis framework for this investment opportunity:

1. **Key Variables**: What are the most important variables that should be adjusted in the scenario analysis?
2. **Base Case Parameters**: What values should be used for the base case scenario?
3. **Optimistic Case Parameters**: What values should be used for the optimistic scenario?
4. **Pessimistic Case Parameters**: What values should be used for the pessimistic scenario?
5. **Variable Sensitivity**: Which variables have the greatest impact on outcomes?
6. **Correlation Factors**: How do various factors correlate with each other?
7. **Time Horizons**: What are appropriate time horizons for the analysis?
8. **Black Swan Events**: What low-probability, high-impact events should be considered?

Provide a detailed framework that can be used to properly stress-test this investment opportunity.
"""
        return prompt
    
    async def suggest_data_sources(self, query: str) -> str:
        """
        Suggest relevant data sources for a specific investment analysis.
        
        Args:
            query: Description of the investment type and data needs
            
        Returns:
            List of recommended data sources with descriptions
        """
        logger.info("Suggesting data sources")
        
        # Use the LLM to recommend data sources based on the investment type
        prompt = f"""
# Data Source Recommendations

## Context
{query}

Please recommend appropriate data sources for analyzing this investment opportunity:

1. **Primary Data Sources**: What are the most essential data sources for this investment type?
2. **Industry-Specific Sources**: What industry-specific data sources would be valuable?
3. **Financial Data Sources**: What sources of financial data would be most relevant?
4. **Market Research Sources**: What market research sources would provide valuable context?
5. **Regulatory Sources**: What regulatory filings or reports should be consulted?
6. **Alternative Data Sources**: What non-traditional data sources might provide insights?
7. **Data Collection Methods**: What methods should be used to collect necessary data?

For each source, provide a brief description of the data available, how it can be accessed, and its specific value for this analysis.
"""
        return prompt 