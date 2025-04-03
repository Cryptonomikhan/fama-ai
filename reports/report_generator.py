#!/usr/bin/env python3
"""
Report Generator for Fama AI.

This module provides functionality to generate formatted reports from the
financial modeling results in various formats (JSON, CSV, PDF).
"""
import os
import json
import csv
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

# Setup logging
logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Report generator for Fama AI.
    
    This class provides methods to generate reports in various formats
    from the financial modeling results.
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the report generator.
        
        Args:
            output_dir: Directory to store the generated reports
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        logger.info(f"Report generator initialized with output directory: {output_dir}")
    
    def generate_report(
        self,
        results: Dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> str:
        """
        Generate a report in the specified format.
        
        Args:
            results: Results from the financial modeling process
            format: Format for the report (json, csv, pdf)
            filename: Optional filename for the report
            request_id: Optional request ID to include in the filename
            
        Returns:
            Path to the generated report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if request_id:
                filename = f"report_{request_id[:8]}_{timestamp}"
            else:
                filename = f"report_{timestamp}"
        
        if format.lower() == "json":
            return self.generate_json_report(results, filename)
        elif format.lower() == "csv":
            return self.generate_csv_report(results, filename)
        elif format.lower() == "pdf":
            return self.generate_pdf_report(results, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_json_report(self, results: Dict[str, Any], filename: str) -> str:
        """
        Generate a JSON report from the results.
        
        Args:
            results: Results from the financial modeling process
            filename: Filename for the report
            
        Returns:
            Path to the generated JSON file
        """
        if not filename.endswith(".json"):
            filename += ".json"
            
        file_path = os.path.join(self.output_dir, filename)
        
        # Ensure the result is serializable
        # Some model outputs might contain non-serializable objects
        serializable_results = self._make_serializable(results)
        
        with open(file_path, "w") as f:
            json.dump(serializable_results, f, indent=2)
            
        logger.info(f"JSON report generated: {file_path}")
        return file_path
    
    def generate_csv_report(self, results: Dict[str, Any], filename: str) -> str:
        """
        Generate CSV files from the results.
        
        This method generates multiple CSV files for different components
        of the financial model (income statement, cash flow, metrics, etc.)
        
        Args:
            results: Results from the financial modeling process
            filename: Base filename for the reports
            
        Returns:
            Path to the generated CSV files directory
        """
        csv_dir = os.path.join(self.output_dir, f"{filename}_csv")
        
        # Create directory for the CSV files
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        
        # Generate CSV for financial model components
        if "financial_model" in results:
            model = results["financial_model"]
            
            # Income statement
            if "income_statement" in model and "data" in model["income_statement"]:
                self._write_csv(
                    model["income_statement"]["data"],
                    os.path.join(csv_dir, "income_statement.csv")
                )
            
            # Cash flow
            if "cash_flow" in model and "data" in model["cash_flow"]:
                self._write_csv(
                    model["cash_flow"]["data"],
                    os.path.join(csv_dir, "cash_flow.csv")
                )
                
            # Balance sheet
            if "balance_sheet" in model and "data" in model["balance_sheet"]:
                self._write_csv(
                    model["balance_sheet"]["data"],
                    os.path.join(csv_dir, "balance_sheet.csv")
                )
        
        # Generate CSV for financial metrics
        if "financial_metrics" in results:
            metrics = results["financial_metrics"]
            metrics_data = [[k, v] for k, v in metrics.items() if k != "details"]
            self._write_csv(
                metrics_data,
                os.path.join(csv_dir, "financial_metrics.csv"),
                headers=["Metric", "Value"]
            )
            
        # Generate CSV for scenarios
        if "scenarios" in results:
            scenarios = results["scenarios"]
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict) and "data" in scenario_data:
                    self._write_csv(
                        scenario_data["data"],
                        os.path.join(csv_dir, f"scenario_{scenario_name}.csv")
                    )
        
        logger.info(f"CSV reports generated in directory: {csv_dir}")
        return csv_dir
    
    def generate_pdf_report(self, results: Dict[str, Any], filename: str) -> str:
        """
        Generate a comprehensive PDF report from the results.
        
        Args:
            results: Results from the financial modeling process
            filename: Filename for the report
            
        Returns:
            Path to the generated PDF file
        """
        if not filename.endswith(".pdf"):
            filename += ".pdf"
            
        file_path = os.path.join(self.output_dir, filename)
        
        # Create a PDF document
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=6
        ))
        
        # Build the document content
        elements = []
        
        # Title
        title = "Financial Analysis Report"
        if "description" in results:
            title = f"Financial Analysis: {results['description'][:50]}"
            if len(results["description"]) > 50:
                title += "..."
                
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Metadata
        metadata = []
        if "time_horizon" in results:
            metadata.append(f"Time Horizon: {results['time_horizon']} years")
        if "risk_factors" in results:
            metadata.append(f"Risk Profile: {results['risk_factors']}")
        
        for item in metadata:
            elements.append(Paragraph(item, styles['Normal']))
            
        elements.append(Spacer(1, 12))
        
        # Executive Summary
        if "executive_summary" in results:
            elements.append(Paragraph("Executive Summary", styles['Subtitle']))
            elements.append(Paragraph(results["executive_summary"], styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Research Results
        if "research_results" in results:
            elements.append(Paragraph("Research Findings", styles['Subtitle']))
            research = results["research_results"]
            
            if isinstance(research, dict):
                for key, value in research.items():
                    if key not in ["raw_research"]:
                        elements.append(Paragraph(f"{key.replace('_', ' ').title()}", styles['TableHeader']))
                        if isinstance(value, list):
                            for item in value:
                                elements.append(Paragraph(f"• {item}", styles['Normal']))
                        else:
                            elements.append(Paragraph(str(value), styles['Normal']))
                        elements.append(Spacer(1, 6))
            
            elements.append(Spacer(1, 12))
        
        # Financial Model
        if "financial_model" in results:
            elements.append(Paragraph("Financial Model", styles['Subtitle']))
            model = results["financial_model"]
            
            # Income Statement
            if "income_statement" in model:
                elements.append(Paragraph("Income Statement", styles['TableHeader']))
                if "data" in model["income_statement"]:
                    table_data = self._format_table_data(model["income_statement"]["data"])
                    if table_data:
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
            
            # Cash Flow
            if "cash_flow" in model:
                elements.append(Paragraph("Cash Flow", styles['TableHeader']))
                if "data" in model["cash_flow"]:
                    table_data = self._format_table_data(model["cash_flow"]["data"])
                    if table_data:
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
        
        # Financial Metrics
        if "financial_metrics" in results:
            elements.append(Paragraph("Financial Metrics", styles['Subtitle']))
            metrics = results["financial_metrics"]
            
            # Create a table for the metrics
            metrics_data = [["Metric", "Value"]]
            for key, value in metrics.items():
                if key != "details" and value is not None:
                    metrics_data.append([key.replace("_", " ").title(), str(value)])
            
            if len(metrics_data) > 1:
                table = Table(metrics_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))
        
        # Validation Results
        if "validation" in results:
            elements.append(Paragraph("Validation Results", styles['Subtitle']))
            validation = results["validation"]
            
            if "model_validation" in validation:
                elements.append(Paragraph("Model Validation", styles['TableHeader']))
                model_validation = validation["model_validation"]
                
                if "score" in model_validation:
                    elements.append(Paragraph(f"Overall Score: {model_validation['score']}", styles['Normal']))
                
                if "critical_issues" in model_validation and model_validation["critical_issues"]:
                    elements.append(Paragraph("Critical Issues:", styles['Normal']))
                    for issue in model_validation["critical_issues"]:
                        elements.append(Paragraph(f"• {issue}", styles['Normal']))
                
                if "recommendations" in model_validation and model_validation["recommendations"]:
                    elements.append(Paragraph("Recommendations:", styles['Normal']))
                    for rec in model_validation["recommendations"]:
                        elements.append(Paragraph(f"• {rec}", styles['Normal']))
                
                elements.append(Spacer(1, 12))
        
        # Scenarios
        if "scenarios" in results:
            elements.append(Paragraph("Scenario Analysis", styles['Subtitle']))
            scenarios = results["scenarios"]
            
            for scenario_name, scenario_data in scenarios.items():
                elements.append(Paragraph(f"{scenario_name.title()} Scenario", styles['TableHeader']))
                
                if isinstance(scenario_data, dict):
                    if "description" in scenario_data:
                        elements.append(Paragraph(scenario_data["description"], styles['Normal']))
                    
                    if "metrics" in scenario_data:
                        metrics_data = [["Metric", "Value"]]
                        for key, value in scenario_data["metrics"].items():
                            if value is not None:
                                metrics_data.append([key.replace("_", " ").title(), str(value)])
                        
                        if len(metrics_data) > 1:
                            table = Table(metrics_data)
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                            ]))
                            elements.append(table)
                
                elements.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(elements)
        
        logger.info(f"PDF report generated: {file_path}")
        return file_path
    
    def _write_csv(
        self,
        data: List[List[Any]],
        file_path: str,
        headers: Optional[List[str]] = None
    ) -> None:
        """
        Write data to a CSV file.
        
        Args:
            data: Data to write to the CSV file
            file_path: Path to the CSV file
            headers: Optional headers for the CSV file
        """
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            
            if headers:
                writer.writerow(headers)
                
            for row in data:
                writer.writerow(row)
    
    def _format_table_data(self, data: List[List[Any]]) -> List[List[str]]:
        """
        Format data for a PDF table.
        
        Args:
            data: Raw data for the table
            
        Returns:
            Formatted data for the table
        """
        if not data:
            return []
            
        # Convert all values to strings
        formatted_data = []
        for row in data:
            formatted_row = []
            for cell in row:
                if isinstance(cell, (int, float)):
                    # Format numbers
                    if isinstance(cell, int):
                        formatted_row.append(f"{cell:,}")
                    else:
                        formatted_row.append(f"{cell:,.2f}")
                else:
                    formatted_row.append(str(cell))
            formatted_data.append(formatted_row)
            
        return formatted_data
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Make an object JSON serializable.
        
        Args:
            obj: Object to make serializable
            
        Returns:
            Serializable version of the object
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Convert to string if not a basic type
            return str(obj)


def generate_report(
    results: Dict[str, Any],
    format: str = "json",
    filename: Optional[str] = None,
    request_id: Optional[str] = None,
    output_dir: str = "reports"
) -> str:
    """
    Generate a report from the financial modeling results.
    
    Args:
        results: Results from the financial modeling process
        format: Format for the report (json, csv, pdf)
        filename: Optional filename for the report
        request_id: Optional request ID to include in the filename
        output_dir: Directory to store the generated reports
        
    Returns:
        Path to the generated report file
    """
    generator = ReportGenerator(output_dir=output_dir)
    return generator.generate_report(
        results=results,
        format=format,
        filename=filename,
        request_id=request_id
    ) 