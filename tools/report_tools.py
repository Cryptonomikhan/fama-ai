#!/usr/bin/env python3
"""
Report Tools for Fama AI.

This module provides tools for generating reports in various formats
that can be used by agents in the Fama AI platform.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from reports.report_generator import ReportGenerator, generate_report

# Setup logging
logger = logging.getLogger(__name__)

# Base tool class
class Tool:
    """Base class for all tools."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    def run(self, *args, **kwargs):
        raise NotImplementedError("Tool must implement run method")

class ReportGeneratorTool(Tool):
    """
    Tool for generating financial reports in various formats.
    
    This tool can be used by agents to generate reports from financial
    modeling results in JSON, CSV, or PDF formats.
    """
    
    name = "report_generator"
    description = "Generate financial reports from modeling results in various formats"
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize the report generator tool.
        
        Args:
            output_dir: Directory to store generated reports
        """
        super().__init__(name=self.name, description=self.description)
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        logger.info(f"Report generator tool initialized with output directory: {output_dir}")
    
    def run(self, query: str, **kwargs: Any) -> str:
        """
        Generate a report based on the query parameters.
        
        Args:
            query: A JSON string or natural language query containing parameters for report generation
            **kwargs: Additional keyword arguments
            
        Returns:
            A string with the path to the generated report and a status message
        """
        try:
            # Parse the query
            params = self._parse_query(query)
            
            # Check if results are provided
            if "results" not in params:
                return "Error: No results provided for report generation. Please include the financial modeling results."
            
            # Get report parameters
            results = params["results"]
            format = params.get("format", "json")
            filename = params.get("filename", None)
            request_id = params.get("request_id", None)
            
            # Generate the report
            report_path = generate_report(
                results=results,
                format=format,
                filename=filename,
                request_id=request_id,
                output_dir=self.output_dir
            )
            
            return f"Report generated successfully at {report_path}"
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse the query into parameters for report generation.
        
        Args:
            query: A JSON string or natural language query
            
        Returns:
            Dictionary with parameters for report generation
        """
        # Try to parse as JSON
        try:
            return json.loads(query)
        except json.JSONDecodeError:
            # If not JSON, try to parse natural language
            return self._parse_natural_language(query)
    
    def _parse_natural_language(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into report parameters.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with parameters for report generation
        """
        # This is a simplified implementation
        # In a real-world scenario, this would use NLP to extract parameters
        params = {}
        
        # Extract format
        formats = ["json", "csv", "pdf"]
        for fmt in formats:
            if f"format {fmt}" in query.lower() or f"{fmt} format" in query.lower():
                params["format"] = fmt
                break
        
        # Extract filename if specified
        if "filename" in query.lower():
            parts = query.split("filename")
            if len(parts) > 1:
                filename_part = parts[1].strip()
                if " " in filename_part:
                    filename = filename_part.split(" ")[0].strip()
                    if filename.endswith("."):
                        filename = filename[:-1]
                    params["filename"] = filename
        
        # Extract request_id if specified
        if "request_id" in query.lower():
            parts = query.split("request_id")
            if len(parts) > 1:
                request_id_part = parts[1].strip()
                if " " in request_id_part:
                    request_id = request_id_part.split(" ")[0].strip()
                    if request_id.endswith("."):
                        request_id = request_id[:-1]
                    params["request_id"] = request_id
        
        return params

class PDFReportTool(Tool):
    """
    Tool specifically for generating PDF reports.
    
    This tool is a specialized version of the ReportGeneratorTool
    that only generates PDF reports.
    """
    
    name = "pdf_report_generator"
    description = "Generate professional PDF reports from financial modeling results"
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the PDF report generator tool.
        
        Args:
            output_dir: Directory to store generated reports
        """
        super().__init__(self.name, self.description)
        self.output_dir = output_dir
        self.generator = ReportGenerator(output_dir=output_dir)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        logger.info(f"PDF report generator tool initialized with output directory: {output_dir}")
    
    def run(self, query: str, **kwargs: Any) -> str:
        """
        Generate a PDF report based on the query parameters.
        
        Args:
            query: A JSON string or natural language query containing parameters for report generation
            **kwargs: Additional keyword arguments
            
        Returns:
            A string with the path to the generated PDF report and a status message
        """
        try:
            # Parse the query
            params = self._parse_query(query)
            
            # Check if results are provided
            if "results" not in params:
                return "Error: No results provided for PDF report generation. Please include the financial modeling results."
            
            # Get report parameters
            results = params["results"]
            filename = params.get("filename", None)
            request_id = params.get("request_id", None)
            
            # Generate the PDF report
            report_path = self.generator.generate_pdf_report(
                results=results,
                filename=filename or f"report_{request_id[:8] if request_id else ''}"
            )
            
            return f"PDF report generated successfully at {report_path}"
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return f"Error generating PDF report: {str(e)}"
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse the query into parameters for PDF report generation.
        
        Args:
            query: A JSON string or natural language query
            
        Returns:
            Dictionary with parameters for report generation
        """
        # Try to parse as JSON
        try:
            return json.loads(query)
        except json.JSONDecodeError:
            # If not JSON, try to parse natural language
            return self._parse_natural_language(query)
    
    def _parse_natural_language(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into report parameters.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with parameters for report generation
        """
        # This is a simplified implementation
        # In a real-world scenario, this would use NLP to extract parameters
        params = {}
        
        # Extract filename if specified
        if "filename" in query.lower():
            parts = query.split("filename")
            if len(parts) > 1:
                filename_part = parts[1].strip()
                if " " in filename_part:
                    filename = filename_part.split(" ")[0].strip()
                    if filename.endswith("."):
                        filename = filename[:-1]
                    params["filename"] = filename
        
        # Extract request_id if specified
        if "request_id" in query.lower():
            parts = query.split("request_id")
            if len(parts) > 1:
                request_id_part = parts[1].strip()
                if " " in request_id_part:
                    request_id = request_id_part.split(" ")[0].strip()
                    if request_id.endswith("."):
                        request_id = request_id[:-1]
                    params["request_id"] = request_id
        
        return params 