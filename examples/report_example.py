#!/usr/bin/env python3
"""
Report Generation Example for Fama AI.

This example demonstrates how to use the report generation tools with
the Agno agent framework.
"""
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agno.agent import Agent
from agno.models.base import Model

from models.model_factory import create_model
from tools.report_tools import ReportGeneratorTool, PDFReportTool
from reports.report_generator import generate_report

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to run the report example.
    """
    # Create a sample financial modeling result
    sample_results = create_sample_results()
    
    # Generate a report using the direct function call
    direct_report_path = generate_direct_report(sample_results)
    logger.info(f"Direct report generated at: {direct_report_path}")
    
    # Generate a report using the Agno agent with the report tools
    agent_report_path = generate_agent_report(sample_results)
    logger.info(f"Agent report generated at: {agent_report_path}")

def create_sample_results():
    """
    Create a sample financial modeling result for demonstration.
    
    Returns:
        Dict with sample financial modeling results
    """
    return {
        "request_id": "sample-1234",
        "description": "Tokenized Real Estate Fund - Office Buildings",
        "time_horizon": 5,
        "risk_factors": "moderate",
        "research_results": {
            "market_overview": "The commercial real estate market is experiencing moderate growth with increasing demand for office spaces in urban centers.",
            "competitive_landscape": [
                "REITs specializing in office properties",
                "Traditional real estate investment funds",
                "Digital tokenized real estate platforms"
            ],
            "regulatory_considerations": [
                "SEC regulations for tokenized securities",
                "Local real estate regulations",
                "International investment regulations"
            ]
        },
        "market_conditions": {
            "interest_rates": "3.5% with projected increase to 4.0% over the next 2 years",
            "inflation": "2.1% annual rate",
            "commercial_real_estate_trends": "Post-pandemic return to office with hybrid models"
        },
        "yield_data": {
            "similar_investments": [
                {"type": "REIT - Office", "yield": "5.2%"},
                {"type": "Tokenized Commercial Real Estate", "yield": "7.1%"},
                {"type": "Traditional Real Estate Fund", "yield": "4.8%"}
            ],
            "average_yield": "5.7%"
        },
        "assumptions": {
            "revenue": [
                "Occupancy rate starting at 85% in Year 1, increasing to 95% by Year 3",
                "Average lease rate of $35 per square foot with 3% annual increases",
                "Additional revenue from amenities and services of 10% of base rent"
            ],
            "expenses": [
                "Property management fees of 4% of gross revenue",
                "Maintenance costs of $2.50 per square foot",
                "Insurance costs of $1.20 per square foot with 2% annual increases"
            ],
            "capital": [
                "Initial acquisition cost of $200 per square foot",
                "Capital expenditures of 2% of property value annually",
                "Terminal cap rate of 6.5%"
            ]
        },
        "financial_model": {
            "income_statement": {
                "description": "Annual income statement for the tokenized real estate fund",
                "data": [
                    ["", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
                    ["Rental Income", 2975000, 3160250, 3486976, 3626455, 3771513],
                    ["Other Income", 297500, 316025, 348698, 362646, 377151],
                    ["Gross Revenue", 3272500, 3476275, 3835673, 3989101, 4148664],
                    ["Property Management", 130900, 139051, 153427, 159564, 165947],
                    ["Maintenance", 250000, 255000, 260100, 265302, 270608],
                    ["Insurance", 120000, 122400, 124848, 127345, 129892],
                    ["Property Taxes", 175000, 178500, 182070, 185711, 189426],
                    ["Total Operating Expenses", 675900, 694951, 720445, 737922, 755873],
                    ["Net Operating Income", 2596600, 2781324, 3115228, 3251179, 3392792],
                    ["Capital Expenditures", 400000, 408000, 416160, 424483, 432973],
                    ["Debt Service", 1200000, 1200000, 1200000, 1200000, 1200000],
                    ["Net Cash Flow", 996600, 1173324, 1499068, 1626696, 1759819]
                ]
            },
            "cash_flow": {
                "description": "Annual cash flow projections",
                "data": [
                    ["", "Year 0", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
                    ["Initial Investment", -20000000, 0, 0, 0, 0, 0],
                    ["Net Cash Flow", 0, 996600, 1173324, 1499068, 1626696, 1759819],
                    ["Terminal Value", 0, 0, 0, 0, 0, 52196785],
                    ["Total Cash Flow", -20000000, 996600, 1173324, 1499068, 1626696, 53956604]
                ]
            }
        },
        "metrics": {
            "irr": 0.156,
            "npv": 15248761,
            "roi": 1.76,
            "payback_period": 3.8,
            "cash_on_cash": 0.0498
        },
        "scenarios": {
            "baseline": {
                "description": "Expected case with moderate growth in occupancy and rental rates",
                "metrics": {
                    "irr": 0.156,
                    "npv": 15248761,
                    "roi": 1.76
                }
            },
            "bull": {
                "description": "Optimistic case with higher occupancy rates and faster rental rate growth",
                "metrics": {
                    "irr": 0.189,
                    "npv": 19873429,
                    "roi": 2.12
                }
            },
            "bear": {
                "description": "Conservative case with lower occupancy and slower rental rate growth",
                "metrics": {
                    "irr": 0.098,
                    "npv": 8125473,
                    "roi": 1.32
                }
            }
        },
        "validation": {
            "model_validation": {
                "score": 0.92,
                "critical_issues": [],
                "recommendations": [
                    "Consider adding sensitivity analysis for interest rate fluctuations",
                    "Include more detailed breakdown of operating expenses"
                ]
            },
            "metric_validation": {
                "accuracy": 0.95,
                "issues": []
            },
            "scenario_validation": {
                "coverage": 0.90,
                "issues": [
                    "The bear case may not fully capture extreme downside risks"
                ]
            }
        }
    }

def generate_direct_report(results):
    """
    Generate a report using the direct function call.
    
    Args:
        results: Financial modeling results
        
    Returns:
        Path to the generated report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"direct_report_{timestamp}"
    
    # Generate a JSON report
    json_report_path = generate_report(
        results=results,
        format="json",
        filename=filename,
        output_dir="reports"
    )
    
    # Generate a PDF report
    pdf_report_path = generate_report(
        results=results,
        format="pdf",
        filename=filename,
        output_dir="reports"
    )
    
    return {
        "json": json_report_path,
        "pdf": pdf_report_path
    }

def generate_agent_report(results):
    """
    Generate a report using the Agno agent with the report tools.
    
    Args:
        results: Financial modeling results
        
    Returns:
        Path to the generated report
    """
    # Create a model for the agent
    model = create_model(
        provider="formation",  # You can use "openai", "anthropic", etc.
        temperature=0.2
    )
    
    # Initialize the agent with the report generation tools
    agent = Agent(
        model=model,
        name="Report Generator Agent",
        role="Financial report generator for investment vehicles",
        description="Generates comprehensive financial reports in various formats",
        instructions=[
            "Generate well-formatted financial reports based on the provided financial modeling results",
            "Use the report_generator tool for creating reports in various formats",
            "Use the pdf_report_generator tool specifically for PDF reports",
            "Always communicate clearly about the status of report generation"
        ],
        tools=[ReportGeneratorTool(), PDFReportTool()],
        markdown=True,
        show_tool_calls=True
    )
    
    # Prepare the request
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query = {
        "results": results,
        "format": "pdf",
        "filename": f"agent_report_{timestamp}"
    }
    
    # Generate report using the agent
    response = agent.run(f"Generate a comprehensive PDF report using this data: {json.dumps(query)}")
    
    # Parse the response to extract the report path
    # This is a simple implementation; in practice, you would extract the path more robustly
    result = str(response.content)
    if "Report generated successfully at" in result:
        return result.split("Report generated successfully at")[1].strip()
    else:
        logger.error(f"Failed to generate report: {result}")
        return None

if __name__ == "__main__":
    main() 