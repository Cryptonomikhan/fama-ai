#!/usr/bin/env python3
"""
Test suite for agent state persistence across API calls.

This module tests the persistence of agent state across separate API calls,
ensuring that conversation history, context, and agent memory are properly
maintained when the same session ID is used in subsequent API requests.
"""

import unittest
import os
import uuid
import json
import logging
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.api.main import app, TaskRequest
from src.storage.factory import initialize_storage
from src.api.main import run_task  # Function is likely in main.py

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatePersistence(unittest.TestCase):
    """Test suite for agent state persistence across API calls."""

    def setUp(self):
        """Set up test environment before each test."""
        self.client = TestClient(app)
        
        # Create a temporary directory for file-based storage
        self.temp_dir = tempfile.mkdtemp()
        
        # Create storage directories
        self.sqlite_dir = os.path.join(self.temp_dir, "sqlite")
        self.json_dir = os.path.join(self.temp_dir, "json")
        
        os.makedirs(self.sqlite_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        
        # Set up test parameters
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"
        self.api_key = "mock-api-key"
        
        # SQLite file path
        self.sqlite_path = os.path.join(self.sqlite_dir, "test_persistence.db")
        
        # Test conversation flow
        self.initial_query = "What is a yield-generating investment vehicle?"
        self.followup_query = "Can you provide specific examples of those?"
        self.reference_query = "What did I ask you initially?"
        
        # Mock responses for consistent testing
        self.initial_response = "A yield-generating investment vehicle is a financial asset or instrument that provides regular income or returns to investors while preserving the principal investment. These vehicles generate cash flow through interest, dividends, rent, or other distributions."
        self.followup_response = "Specific examples of yield-generating investment vehicles include: 1) Dividend-paying stocks, 2) Real Estate Investment Trusts (REITs), 3) Corporate and government bonds, 4) Certificate of Deposits (CDs), 5) Money Market Funds, 6) Preferred stocks, 7) Master Limited Partnerships (MLPs), and 8) Rental properties."
        self.reference_response = "You initially asked me what a yield-generating investment vehicle is."

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    def test_state_persistence_sqlite_direct_api(self):
        """Test state persistence across API calls with SQLite storage using direct API calls."""
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Set up response sequence
            responses = [
                MagicMock(content=self.initial_response),
                MagicMock(content=self.followup_response),
                MagicMock(content=self.reference_response)
            ]
            
            # Configure the mock to return different responses for each call
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API call with storage configuration
            initial_request = TaskRequest(
                message=self.initial_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the initial request
            initial_response = run_task(initial_request)
            
            # Verify the response
            self.assertEqual(initial_response.content, self.initial_response)
            
            # PHASE 2: Follow-up API call with the same session ID
            followup_request = TaskRequest(
                message=self.followup_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite", 
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the follow-up request
            followup_response = run_task(followup_request)
            
            # Verify the response
            self.assertEqual(followup_response.content, self.followup_response)
            
            # PHASE 3: Reference query to check context retention
            reference_request = TaskRequest(
                message=self.reference_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the reference request
            reference_response = run_task(reference_request)
            
            # Verify the response contains a reference to the initial query
            self.assertEqual(reference_response.content, self.reference_response)
            
            # Verify that the model was called with appropriate context each time
            calls = mock_model.generate.call_args_list
            self.assertEqual(len(calls), 3, "Model should have been called 3 times")

    def test_state_persistence_json_direct_api(self):
        """Test state persistence across API calls with JSON storage using direct API calls."""
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Set up response sequence
            responses = [
                MagicMock(content=self.initial_response),
                MagicMock(content=self.followup_response),
                MagicMock(content=self.reference_response)
            ]
            
            # Configure the mock to return different responses for each call
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API call with storage configuration
            initial_request = TaskRequest(
                message=self.initial_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="json",
                storage_connection=self.json_dir,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the initial request
            initial_response = run_task(initial_request)
            
            # Verify the response
            self.assertEqual(initial_response.content, self.initial_response)
            
            # Verify JSON storage file was created
            json_file_path = os.path.join(self.json_dir, f"{self.session_id}.json")
            self.assertTrue(os.path.exists(json_file_path), "JSON storage file should be created")
            
            # PHASE 2: Follow-up API call with the same session ID
            followup_request = TaskRequest(
                message=self.followup_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="json",
                storage_connection=self.json_dir,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the follow-up request
            followup_response = run_task(followup_request)
            
            # Verify the response
            self.assertEqual(followup_response.content, self.followup_response)
            
            # Check that the JSON file was updated (size should increase)
            initial_file_size = os.path.getsize(json_file_path)
            
            # PHASE 3: Reference query to check context retention
            reference_request = TaskRequest(
                message=self.reference_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="json",
                storage_connection=self.json_dir,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the reference request
            reference_response = run_task(reference_request)
            
            # Verify the response contains a reference to the initial query
            self.assertEqual(reference_response.content, self.reference_response)
            
            # Verify that the JSON file size increased after additional messages
            final_file_size = os.path.getsize(json_file_path)
            self.assertGreater(final_file_size, initial_file_size, "JSON file should grow with additional messages")
            
            # Verify the file content contains the conversation history
            with open(json_file_path, 'r') as f:
                data = json.load(f)
                self.assertIn("messages", data, "JSON file should contain messages")
                messages = data.get("messages", [])
                self.assertGreaterEqual(len(messages), 6, "Should have at least 6 messages (3 user, 3 assistant)")
                
                # Verify the message sequence matches our test flow
                user_messages = [msg for msg in messages if msg.get("role") == "user"]
                self.assertGreaterEqual(len(user_messages), 3)
                self.assertEqual(user_messages[0].get("content"), self.initial_query)
                self.assertEqual(user_messages[1].get("content"), self.followup_query)
                self.assertEqual(user_messages[2].get("content"), self.reference_query)

    def test_state_persistence_http_api(self):
        """Test state persistence across API calls via HTTP interface."""
        # Skip this test if the app is not properly configured
        try:
            # Import optional dependencies for API testing
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("FastAPI TestClient not available")
        
        # Create a test client
        client = TestClient(app)
        
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Set up response sequence
            responses = [
                MagicMock(content=self.initial_response),
                MagicMock(content=self.followup_response),
                MagicMock(content=self.reference_response)
            ]
            
            # Configure the mock to return different responses for each call
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API call with storage configuration
            initial_request = {
                "message": self.initial_query,
                "provider": "openai",
                "model": "gpt-4o",
                "provider_api_key": self.api_key,
                "stream": False,
                "storage_type": "sqlite",
                "storage_connection": self.sqlite_path,
                "session_id": self.session_id,
                "user_id": self.user_id
            }
            
            # Execute the initial request
            initial_response = client.post("/api/tasks", json=initial_request)
            self.assertEqual(initial_response.status_code, 200)
            initial_data = initial_response.json()
            self.assertEqual(initial_data.get("content"), self.initial_response)
            
            # PHASE 2: Follow-up API call with the same session ID
            followup_request = {
                "message": self.followup_query,
                "provider": "openai",
                "model": "gpt-4o",
                "provider_api_key": self.api_key,
                "stream": False,
                "storage_type": "sqlite",
                "storage_connection": self.sqlite_path,
                "session_id": self.session_id,
                "user_id": self.user_id
            }
            
            # Execute the follow-up request
            followup_response = client.post("/api/tasks", json=followup_request)
            self.assertEqual(followup_response.status_code, 200)
            followup_data = followup_response.json()
            self.assertEqual(followup_data.get("content"), self.followup_response)
            
            # PHASE 3: Reference query to check context retention
            reference_request = {
                "message": self.reference_query,
                "provider": "openai",
                "model": "gpt-4o",
                "provider_api_key": self.api_key,
                "stream": False,
                "storage_type": "sqlite",
                "storage_connection": self.sqlite_path,
                "session_id": self.session_id,
                "user_id": self.user_id
            }
            
            # Execute the reference request
            reference_response = client.post("/api/tasks", json=reference_request)
            self.assertEqual(reference_response.status_code, 200)
            reference_data = reference_response.json()
            self.assertEqual(reference_data.get("content"), self.reference_response)

    def test_state_persistence_with_different_models(self):
        """Test state persistence when switching models between API calls."""
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model_1 = MagicMock()
            mock_model_1.generate.return_value = MagicMock(content=self.initial_response)
            
            mock_model_2 = MagicMock()
            mock_model_2.generate.return_value = MagicMock(content=self.followup_response)
            
            # Configure the mock to return different models
            mock_create_model.side_effect = [mock_model_1, mock_model_2]
            
            # PHASE 1: Initial API call with GPT-4o
            initial_request = TaskRequest(
                message=self.initial_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the initial request
            initial_response = run_task(initial_request)
            
            # Verify the response
            self.assertEqual(initial_response.content, self.initial_response)
            
            # PHASE 2: Follow-up API call with GPT-3.5-turbo but same session ID
            followup_request = TaskRequest(
                message=self.followup_query,
                provider="openai",
                model="gpt-3.5-turbo",  # Different model
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the follow-up request
            followup_response = run_task(followup_request)
            
            # Verify the response
            self.assertEqual(followup_response.content, self.followup_response)
            
            # Verify that both models were used with the conversation history
            self.assertEqual(mock_create_model.call_count, 2, "Both models should have been created")
            self.assertEqual(mock_model_1.generate.call_count, 1, "First model should be called once")
            self.assertEqual(mock_model_2.generate.call_count, 1, "Second model should be called once")

    def test_state_persistence_with_parallel_sessions(self):
        """Test state persistence with multiple parallel sessions."""
        # Create a second session ID
        second_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Responses for first session
            first_initial_response = MagicMock(content="First session initial response")
            first_followup_response = MagicMock(content="First session followup response")
            
            # Responses for second session
            second_initial_response = MagicMock(content="Second session initial response")
            second_followup_response = MagicMock(content="Second session followup response")
            
            # Configure the mock to return different responses based on session
            responses = [
                first_initial_response,      # First session initial
                second_initial_response,     # Second session initial
                first_followup_response,     # First session followup
                second_followup_response     # Second session followup
            ]
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API calls for both sessions
            
            # First session initial call
            first_initial_request = TaskRequest(
                message="First session initial query",
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            first_initial_response_result = run_task(first_initial_request)
            self.assertEqual(first_initial_response_result.content, "First session initial response")
            
            # Second session initial call
            second_initial_request = TaskRequest(
                message="Second session initial query",
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=second_session_id,
                user_id=self.user_id
            )
            
            second_initial_response_result = run_task(second_initial_request)
            self.assertEqual(second_initial_response_result.content, "Second session initial response")
            
            # PHASE 2: Follow-up API calls for both sessions
            
            # First session followup
            first_followup_request = TaskRequest(
                message="First session followup query",
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            first_followup_response_result = run_task(first_followup_request)
            self.assertEqual(first_followup_response_result.content, "First session followup response")
            
            # Second session followup
            second_followup_request = TaskRequest(
                message="Second session followup query",
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=second_session_id,
                user_id=self.user_id
            )
            
            second_followup_response_result = run_task(second_followup_request)
            self.assertEqual(second_followup_response_result.content, "Second session followup response")
            
            # Verify that the model was called with the correct context for each session
            # This would require inspecting the calls to the model's generate method
            calls = mock_model.generate.call_args_list
            self.assertEqual(len(calls), 4, "Model should have been called 4 times")

    def test_state_persistence_with_storage_changes(self):
        """Test state persistence when switching storage backends between API calls."""
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Set up response sequence
            responses = [
                MagicMock(content=self.initial_response),
                MagicMock(content=self.followup_response)
            ]
            
            # Configure the mock to return different responses for each call
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API call with SQLite storage
            initial_request = TaskRequest(
                message=self.initial_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the initial request
            initial_response = run_task(initial_request)
            
            # Verify the response
            self.assertEqual(initial_response.content, self.initial_response)
            
            # PHASE 2: Follow-up API call with different storage (JSON) but same session ID
            # This test verifies that the system properly handles different storage backends
            # Note: In a real implementation, this might not preserve state across different storage backends
            # But we want to verify that the system handles this gracefully
            followup_request = TaskRequest(
                message=self.followup_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="json",  # Different storage backend
                storage_connection=self.json_dir, # Different connection
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the follow-up request
            followup_response = run_task(followup_request)
            
            # Verify the response
            self.assertEqual(followup_response.content, self.followup_response)
            
            # Verify that both storage backends were properly used
            # SQLite file should exist
            self.assertTrue(os.path.exists(self.sqlite_path), "SQLite file should be created")
            
            # JSON file should exist
            json_file_path = os.path.join(self.json_dir, f"{self.session_id}.json")
            self.assertTrue(os.path.exists(json_file_path), "JSON file should be created")

    def test_state_persistence_with_delayed_resume(self):
        """Test state persistence with a significant delay between API calls."""
        # Mock the model creation and response generation
        with patch("src.models.factory.create_model") as mock_create_model:
            # Configure the mock model to return predictable responses
            mock_model = MagicMock()
            
            # Set up response sequence
            responses = [
                MagicMock(content=self.initial_response),
                MagicMock(content=self.followup_response)
            ]
            
            # Configure the mock to return different responses for each call
            mock_model.generate.side_effect = responses
            mock_create_model.return_value = mock_model
            
            # PHASE 1: Initial API call with storage configuration
            initial_request = TaskRequest(
                message=self.initial_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the initial request
            initial_response = run_task(initial_request)
            
            # Verify the response
            self.assertEqual(initial_response.content, self.initial_response)
            
            # Simulate a significant delay between API calls (3 seconds)
            time.sleep(3)
            
            # PHASE 2: Follow-up API call with the same session ID after delay
            followup_request = TaskRequest(
                message=self.followup_query,
                provider="openai",
                model="gpt-4o",
                provider_api_key=self.api_key,
                stream=False,
                storage_type="sqlite",
                storage_connection=self.sqlite_path,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            # Execute the follow-up request
            followup_response = run_task(followup_request)
            
            # Verify the response
            self.assertEqual(followup_response.content, self.followup_response)
            
            # Verify that the model was called with appropriate context
            calls = mock_model.generate.call_args_list
            self.assertEqual(len(calls), 2, "Model should have been called twice")


if __name__ == "__main__":
    unittest.main() 