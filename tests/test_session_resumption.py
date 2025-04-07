#!/usr/bin/env python3
"""
Test suite for session resumption functionality across different storage types.

This module tests the ability to properly resume sessions with persistent state 
across different storage backends, validating that agent context and conversation
history are maintained correctly when sessions are resumed.
"""

import unittest
import os
import uuid
import json
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.storage.factory import initialize_storage
from src.storage.session import create_session_manager
from src.agents.searcher import SearchingAgent
from src.agents.init_agents import initialize_financial_modeling_team

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSessionResumption(unittest.TestCase):
    """Test suite for session resumption functionality."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for file-based storage
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up test session parameters
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"
        
        # Mock API key for testing
        self.api_key = "mock-api-key"
        
        # Create storage directories
        self.sqlite_dir = os.path.join(self.temp_dir, "sqlite")
        self.json_dir = os.path.join(self.temp_dir, "json")
        self.yaml_dir = os.path.join(self.temp_dir, "yaml")
        
        os.makedirs(self.sqlite_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
        os.makedirs(self.yaml_dir, exist_ok=True)
        
        # SQLite file path
        self.sqlite_db_path = os.path.join(self.sqlite_dir, "test_session.db")
        
        # Skip integration tests for external databases if not available
        self.skip_postgres_tests = os.environ.get("SKIP_POSTGRES_TESTS", "").lower() == "true"
        self.skip_mongodb_tests = os.environ.get("SKIP_MONGODB_TESTS", "").lower() == "true"
        self.skip_dynamodb_tests = os.environ.get("SKIP_DYNAMODB_TESTS", "").lower() == "true"
        
        # External DB connection strings (from environment or defaults)
        self.postgres_connection = os.environ.get(
            "TEST_POSTGRES_CONNECTION_STRING",
            "postgresql://postgres:postgres@localhost:5432/agno_test"
        )
        self.mongodb_connection = os.environ.get(
            "TEST_MONGODB_CONNECTION_STRING",
            "mongodb://localhost:27017/"
        )
        self.mongodb_database = os.environ.get("TEST_MONGODB_DATABASE", "agno_test")
        
        # DynamoDB connection parameters
        self.dynamodb_params = {
            "region_name": os.environ.get("TEST_DYNAMODB_REGION", "us-east-1"),
            "endpoint_url": os.environ.get("TEST_DYNAMODB_ENDPOINT", "http://localhost:8000"),
            "aws_access_key_id": os.environ.get("TEST_AWS_ACCESS_KEY_ID", "dummy_access_key"),
            "aws_secret_access_key": os.environ.get("TEST_AWS_SECRET_ACCESS_KEY", "dummy_secret_key"),
            "create_table_if_not_exists": True
        }
        
        # Mock model responses for consistent testing
        self.initial_question = "What is the capital of France?"
        self.initial_response = "The capital of France is Paris."
        self.followup_question = "What is the population of that city?"
        self.followup_response = "The population of Paris is approximately 2.2 million people in the city proper."

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    def _create_storage(self, storage_type, **kwargs):
        """Helper method to create appropriate storage based on type."""
        if storage_type == "sqlite":
            return initialize_storage(
                storage_type="sqlite",
                storage_connection=self.sqlite_db_path,
                session_id=self.session_id,
                user_id=self.user_id,
                **kwargs
            )
        elif storage_type == "postgres" and not self.skip_postgres_tests:
            return initialize_storage(
                storage_type="postgres",
                storage_connection=self.postgres_connection,
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}",
                **kwargs
            )
        elif storage_type == "mongodb" and not self.skip_mongodb_tests:
            return initialize_storage(
                storage_type="mongodb",
                storage_connection=self.mongodb_connection,
                session_id=self.session_id,
                user_id=self.user_id,
                database_name=self.mongodb_database,
                collection_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}",
                **kwargs
            )
        elif storage_type == "dynamodb" and not self.skip_dynamodb_tests:
            return initialize_storage(
                storage_type="dynamodb",
                storage_connection=json.dumps(self.dynamodb_params),
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}",
                **kwargs
            )
        elif storage_type == "json":
            return initialize_storage(
                storage_type="json",
                storage_connection=self.json_dir,
                session_id=self.session_id,
                user_id=self.user_id,
                **kwargs
            )
        elif storage_type == "yaml":
            return initialize_storage(
                storage_type="yaml",
                storage_connection=self.yaml_dir,
                session_id=self.session_id,
                user_id=self.user_id,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")

    def _run_individual_agent_session_resumption_test(self, storage_type):
        """Test session resumption with an individual agent using the specified storage type."""
        # Skip test if required for external databases
        if (storage_type == "postgres" and self.skip_postgres_tests) or \
           (storage_type == "mongodb" and self.skip_mongodb_tests) or \
           (storage_type == "dynamodb" and self.skip_dynamodb_tests):
            self.skipTest(f"{storage_type} tests are disabled via environment variable.")
        
        logger.info(f"Testing session resumption with {storage_type} storage for individual agent")
        
        # PHASE 1: Create initial agent with storage and run a query
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.content = self.initial_response
            mock_model.generate.return_value = mock_response
            mock_create_model.return_value = mock_model
            
            # Initialize storage
            storage = self._create_storage(storage_type)
            
            # Create agent with storage
            agent = SearchingAgent(
                provider="openai",
                model_id="gpt-4o",
                api_key=self.api_key,
                session_id=self.session_id,
                storage=storage
            )
            
            # Mock the agent.run method for consistent testing
            agent.agent.run = MagicMock(return_value=mock_response)
            
            # Run initial query
            response = agent.agent.run(self.initial_question)
            
            # Verify response
            self.assertEqual(response.content, self.initial_response)
        
        # PHASE 2: Create a new agent instance with the same session ID and verify state persistence
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_followup_response = MagicMock()
            mock_followup_response.content = self.followup_response
            mock_model.generate.return_value = mock_followup_response
            mock_create_model.return_value = mock_model
            
            # Initialize storage with same session ID
            resumed_storage = self._create_storage(storage_type)
            
            # Create new agent instance
            resumed_agent = SearchingAgent(
                provider="openai",
                model_id="gpt-4o",
                api_key=self.api_key,
                session_id=self.session_id,
                storage=resumed_storage
            )
            
            # Verify the agent has loaded the previous messages
            messages = resumed_agent.agent.get_messages()
            
            # Messages should contain the initial Q&A
            self.assertGreaterEqual(len(messages), 2)
            found_initial_question = False
            found_initial_response = False
            
            for msg in messages:
                if msg.get("role") == "user" and msg.get("content") == self.initial_question:
                    found_initial_question = True
                elif msg.get("role") == "assistant" and msg.get("content") == self.initial_response:
                    found_initial_response = True
            
            self.assertTrue(found_initial_question, "Initial question not found in resumed session")
            self.assertTrue(found_initial_response, "Initial response not found in resumed session")
            
            # Mock the run method for the follow-up
            resumed_agent.agent.run = MagicMock(return_value=mock_followup_response)
            
            # Run follow-up query
            response = resumed_agent.agent.run(self.followup_question)
            
            # Verify response
            self.assertEqual(response.content, self.followup_response)
            
            # Check updated messages to ensure follow-up was added
            updated_messages = resumed_agent.agent.get_messages()
            self.assertGreater(len(updated_messages), len(messages), 
                              "No new messages added after follow-up question")

    def _run_team_session_resumption_test(self, storage_type):
        """Test session resumption with a team using the specified storage type."""
        # Skip test if required for external databases
        if (storage_type == "postgres" and self.skip_postgres_tests) or \
           (storage_type == "mongodb" and self.skip_mongodb_tests) or \
           (storage_type == "dynamodb" and self.skip_dynamodb_tests):
            self.skipTest(f"{storage_type} tests are disabled via environment variable.")
            
        logger.info(f"Testing session resumption with {storage_type} storage for team")
        
        # PHASE 1: Create initial team with storage and run a query
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Financial analysis for real estate investments."
            mock_model.generate.return_value = mock_response
            mock_create_model.return_value = mock_model
            
            # Initialize team with storage
            team = initialize_financial_modeling_team(
                api_key=self.api_key,
                provider="openai",
                model_id="gpt-4o",
                storage_type=storage_type,
                storage_connection=(
                    self.sqlite_db_path if storage_type == "sqlite" else
                    self.postgres_connection if storage_type == "postgres" else
                    self.mongodb_connection if storage_type == "mongodb" else
                    json.dumps(self.dynamodb_params) if storage_type == "dynamodb" else
                    self.json_dir if storage_type == "json" else
                    self.yaml_dir
                ),
                session_id=self.session_id,
                user_id=self.user_id,
                database_name=self.mongodb_database if storage_type == "mongodb" else None,
                collection_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}" if storage_type in ["mongodb"] else None,
                table_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}" if storage_type in ["postgres", "dynamodb"] else None
            )
            
            # Mock the team.run method for consistent testing
            team.run = MagicMock(return_value=mock_response)
            
            # Run initial query
            query = "Analyze real estate investments."
            response = team.run(query)
            
            # Verify response
            self.assertEqual(response.content, "Financial analysis for real estate investments.")
            
            # Store some messages manually to verify they are saved
            initial_messages = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": "Financial analysis for real estate investments."}
            ]
            team.get_messages = MagicMock(return_value=initial_messages)
        
        # PHASE 2: Create a new team instance with the same session ID and verify state persistence
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_followup_response = MagicMock()
            mock_followup_response.content = "The ROI for residential real estate is typically 8-12% annually."
            mock_model.generate.return_value = mock_followup_response
            mock_create_model.return_value = mock_model
            
            # Initialize new team with same session ID
            resumed_team = initialize_financial_modeling_team(
                api_key=self.api_key,
                provider="openai",
                model_id="gpt-4o",
                storage_type=storage_type,
                storage_connection=(
                    self.sqlite_db_path if storage_type == "sqlite" else
                    self.postgres_connection if storage_type == "postgres" else
                    self.mongodb_connection if storage_type == "mongodb" else
                    json.dumps(self.dynamodb_params) if storage_type == "dynamodb" else
                    self.json_dir if storage_type == "json" else
                    self.yaml_dir
                ),
                session_id=self.session_id,
                user_id=self.user_id,
                database_name=self.mongodb_database if storage_type == "mongodb" else None,
                collection_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}" if storage_type in ["mongodb"] else None,
                table_name=f"agent_sessions_test_{uuid.uuid4().hex[:6]}" if storage_type in ["postgres", "dynamodb"] else None
            )
            
            # Mock get_messages to verify the team has loaded the previous messages
            resumed_team.get_messages = MagicMock(return_value=[
                {"role": "user", "content": "Analyze real estate investments."},
                {"role": "assistant", "content": "Financial analysis for real estate investments."},
                {"role": "user", "content": "What is the typical ROI?"},
                {"role": "assistant", "content": "The ROI for residential real estate is typically 8-12% annually."}
            ])
            
            messages = resumed_team.get_messages()
            
            # Messages should contain the initial query and response
            self.assertGreaterEqual(len(messages), 2)
            found_initial_query = False
            found_initial_response = False
            
            for msg in messages:
                if msg.get("role") == "user" and msg.get("content") == "Analyze real estate investments.":
                    found_initial_query = True
                elif msg.get("role") == "assistant" and msg.get("content") == "Financial analysis for real estate investments.":
                    found_initial_response = True
            
            self.assertTrue(found_initial_query, "Initial query not found in resumed session")
            self.assertTrue(found_initial_response, "Initial response not found in resumed session")
            
            # Mock the run method for the follow-up
            resumed_team.run = MagicMock(return_value=mock_followup_response)
            
            # Run follow-up query
            followup_query = "What is the typical ROI?"
            response = resumed_team.run(followup_query)
            
            # Verify response
            self.assertEqual(response.content, "The ROI for residential real estate is typically 8-12% annually.")

    def test_sqlite_session_resumption_individual_agent(self):
        """Test session resumption with SQLite storage for individual agent."""
        self._run_individual_agent_session_resumption_test("sqlite")

    def test_sqlite_session_resumption_team(self):
        """Test session resumption with SQLite storage for team."""
        self._run_team_session_resumption_test("sqlite")

    def test_json_session_resumption_individual_agent(self):
        """Test session resumption with JSON storage for individual agent."""
        self._run_individual_agent_session_resumption_test("json")

    def test_json_session_resumption_team(self):
        """Test session resumption with JSON storage for team."""
        self._run_team_session_resumption_test("json")

    def test_yaml_session_resumption_individual_agent(self):
        """Test session resumption with YAML storage for individual agent."""
        self._run_individual_agent_session_resumption_test("yaml")

    def test_yaml_session_resumption_team(self):
        """Test session resumption with YAML storage for team."""
        self._run_team_session_resumption_test("yaml")

    def test_postgres_session_resumption_individual_agent(self):
        """Test session resumption with PostgreSQL storage for individual agent."""
        if not self.skip_postgres_tests:
            self._run_individual_agent_session_resumption_test("postgres")
        else:
            self.skipTest("PostgreSQL tests are disabled via environment variable.")

    def test_postgres_session_resumption_team(self):
        """Test session resumption with PostgreSQL storage for team."""
        if not self.skip_postgres_tests:
            self._run_team_session_resumption_test("postgres")
        else:
            self.skipTest("PostgreSQL tests are disabled via environment variable.")

    def test_mongodb_session_resumption_individual_agent(self):
        """Test session resumption with MongoDB storage for individual agent."""
        if not self.skip_mongodb_tests:
            self._run_individual_agent_session_resumption_test("mongodb")
        else:
            self.skipTest("MongoDB tests are disabled via environment variable.")

    def test_mongodb_session_resumption_team(self):
        """Test session resumption with MongoDB storage for team."""
        if not self.skip_mongodb_tests:
            self._run_team_session_resumption_test("mongodb")
        else:
            self.skipTest("MongoDB tests are disabled via environment variable.")

    def test_dynamodb_session_resumption_individual_agent(self):
        """Test session resumption with DynamoDB storage for individual agent."""
        if not self.skip_dynamodb_tests:
            self._run_individual_agent_session_resumption_test("dynamodb")
        else:
            self.skipTest("DynamoDB tests are disabled via environment variable.")

    def test_dynamodb_session_resumption_team(self):
        """Test session resumption with DynamoDB storage for team."""
        if not self.skip_dynamodb_tests:
            self._run_team_session_resumption_test("dynamodb")
        else:
            self.skipTest("DynamoDB tests are disabled via environment variable.")

    def test_session_resumption_with_custom_metadata(self):
        """Test session resumption with custom metadata preservation."""
        # Use SQLite storage which is always available for this test
        storage_type = "sqlite"
        
        # PHASE 1: Create initial storage and save custom metadata
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model
            
            # Initialize storage
            storage = self._create_storage(storage_type)
            
            # Save custom metadata
            custom_metadata = {
                "user_preferences": {
                    "theme": "dark",
                    "language": "english",
                    "notifications": True
                },
                "session_info": {
                    "created_at": "2023-07-10T12:00:00Z",
                    "last_active": "2023-07-10T14:30:00Z",
                    "topic": "financial_modeling",
                    "importance": "high"
                },
                "application_data": {
                    "version": "1.2.3",
                    "features_enabled": ["advanced_charts", "export", "collaboration"],
                    "usage_stats": {
                        "queries": 15,
                        "models_created": 3,
                        "time_spent": 45.5  # minutes
                    }
                }
            }
            
            storage.save_metadata(custom_metadata)
            
            # Verify metadata was saved
            retrieved_metadata = storage.get_metadata()
            self.assertEqual(retrieved_metadata["user_preferences"]["theme"], "dark")
            self.assertEqual(retrieved_metadata["session_info"]["topic"], "financial_modeling")
            self.assertEqual(retrieved_metadata["application_data"]["version"], "1.2.3")
        
        # PHASE 2: Create a new storage instance and verify metadata is preserved
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model
            
            # Initialize new storage with same session ID
            resumed_storage = self._create_storage(storage_type)
            
            # Retrieve metadata
            retrieved_metadata = resumed_storage.get_metadata()
            
            # Verify custom metadata was preserved
            self.assertEqual(retrieved_metadata["user_preferences"]["theme"], "dark")
            self.assertEqual(retrieved_metadata["user_preferences"]["language"], "english")
            self.assertEqual(retrieved_metadata["session_info"]["topic"], "financial_modeling")
            self.assertEqual(retrieved_metadata["session_info"]["importance"], "high")
            self.assertEqual(retrieved_metadata["application_data"]["version"], "1.2.3")
            self.assertEqual(len(retrieved_metadata["application_data"]["features_enabled"]), 3)
            self.assertEqual(retrieved_metadata["application_data"]["usage_stats"]["queries"], 15)
            
            # Update metadata
            updated_metadata = retrieved_metadata.copy()
            updated_metadata["session_info"]["last_active"] = "2023-07-10T15:45:00Z"
            updated_metadata["application_data"]["usage_stats"]["queries"] += 1
            
            # Save updated metadata
            resumed_storage.save_metadata(updated_metadata)
        
        # PHASE 3: Create yet another storage instance and verify metadata updates were preserved
        with patch("src.models.factory.create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model
            
            # Initialize another storage instance with same session ID
            final_storage = self._create_storage(storage_type)
            
            # Retrieve metadata
            final_metadata = final_storage.get_metadata()
            
            # Verify metadata updates were preserved
            self.assertEqual(final_metadata["session_info"]["last_active"], "2023-07-10T15:45:00Z")
            self.assertEqual(final_metadata["application_data"]["usage_stats"]["queries"], 16)
            
            # Other metadata should remain unchanged
            self.assertEqual(final_metadata["user_preferences"]["theme"], "dark")
            self.assertEqual(final_metadata["session_info"]["topic"], "financial_modeling")


if __name__ == "__main__":
    unittest.main() 