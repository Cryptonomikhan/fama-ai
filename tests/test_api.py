#!/usr/bin/env python3
"""
Test script for the API endpoints.

This script tests the API endpoints for the Fama AI application.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary components
from api.main import app, route_request

def test_submit_endpoint():
    """Test the /api/submit endpoint."""
    print("Testing /api/submit endpoint...")
    
    # Set up a valid API key
    os.environ["API_KEY"] = "test-api-key"
    
    # Set up the request headers
    headers = {
        "X-API-Key": "test-api-key",
        "Content-Type": "application/json"
    }
    
    # Set up the request body
    body = {
        "description": "A tokenized GPU compute resource leasing model with revenue from hourly usage fees.",
        "time_horizon": 5,
        "risk_factors": "moderate",
        "output_format": "json",
        "research_context": "Focus on AI compute demand and GPU markets."
    }
    
    # Route the request
    request = {
        "headers": headers,
        "body": json.dumps(body),
        "method": "POST",
        "path": "/api/submit"
    }
    
    response = route_request(request)
    
    # Verify the response
    assert response.get("statusCode") == 200, f"Expected status code 200, got {response.get('statusCode')}"
    
    response_body = json.loads(response.get("body", "{}"))
    assert "request_id" in response_body, "Response does not contain request_id"
    assert "log_stream_url" in response_body, "Response does not contain log_stream_url"
    
    print("✓ /api/submit endpoint test passed")
    
    # Return the request_id for use in other tests
    return response_body.get("request_id")

def test_logs_endpoint(request_id):
    """Test the /api/logs/{request_id} endpoint."""
    if not request_id:
        print("Skipping /api/logs endpoint test due to missing request_id")
        return
    
    print(f"Testing /api/logs/{request_id} endpoint...")
    
    # Set up the request headers
    headers = {
        "X-API-Key": "test-api-key",
        "Content-Type": "application/json"
    }
    
    # Route the request
    request = {
        "headers": headers,
        "method": "GET",
        "path": f"/api/logs/{request_id}"
    }
    
    response = route_request(request)
    
    # Verify the response
    assert response.get("statusCode") == 200, f"Expected status code 200, got {response.get('statusCode')}"
    
    response_body = json.loads(response.get("body", "{}"))
    assert "logs" in response_body, "Response does not contain logs"
    
    # Check for results data in the response
    if "results" in response_body:
        results = response_body["results"]
        
        # Verify research, financial model, and scenario planning data
        assert "research_results" in results, "Results missing research_results"
        assert "market_conditions" in results, "Results missing market_conditions"
        assert "yield_data" in results, "Results missing yield_data"
        assert "financial_model" in results, "Results missing financial_model"
        assert "metrics" in results, "Results missing metrics"
        assert "scenarios" in results, "Results missing scenarios"
        assert "scenario_impact" in results, "Results missing scenario_impact"
        
        # Verify assumption data
        assert "assumptions" in results, "Results missing assumptions"
        assert "assumption_validation" in results, "Results missing assumption_validation"
        
        # Verify validation data
        assert "validation" in results, "Results missing validation"
        validation = results["validation"]
        assert "model_validation" in validation, "Validation missing model_validation"
        assert "metric_validation" in validation, "Validation missing metric_validation"
        assert "scenario_validation" in validation, "Validation missing scenario_validation"
        
        print("✓ Verified research and financial model data")
        print("✓ Verified scenario planning data")
        print("✓ Verified assumption data")
        print("✓ Verified validation data")
    
    print("✓ /api/logs endpoint test passed")

def main():
    """Run the API tests."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Test the /api/submit endpoint
    request_id = test_submit_endpoint()
    
    # Test the /api/logs endpoint
    test_logs_endpoint(request_id)
    
    print("All API tests passed!")

if __name__ == "__main__":
    main() 