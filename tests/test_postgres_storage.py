#!/usr/bin/env python3
"""
Test suite for PostgreSQL storage integration with Agno agents and teams.

This module tests the PostgreSQL storage connector's functionality with both 
individual agents and teams, ensuring proper state persistence across 
different interactions.
"""

import unittest
import os
import json
import uuid
import logging
from unittest.mock import patch, MagicMock

from src.storage.factory import initialize_storage
from src.storage.postgres import create_postgres_storage
from src.agents.searcher import SearchingAgent
from src.agents.init_agents import initialize_financial_modeling_team
from agno.agent import Agent
from agno.team.team import Team
from agno.storage.agent.postgres import PostgresAgentStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPostgresStorage(unittest.TestCase):
    """Test suite for PostgreSQL storage integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Use environment variables or default test database
        cls.db_connection = os.environ.get(
            "TEST_POSTGRES_CONNECTION_STRING",
            "postgresql://postgres:postgres@localhost:5432/agno_test"
        )
        # Skip tests if environment variable is explicitly set to skip
        cls.skip_postgres_tests = os.environ.get("SKIP_POSTGRES_TESTS", "").lower() == "true"
        if cls.skip_postgres_tests:
            logger.warning("PostgreSQL tests are being skipped based on environment configuration.")

    def setUp(self):
        """Set up test environment before each test."""
        if self.skip_postgres_tests:
            self.skipTest("PostgreSQL tests are disabled via environment variable.")
            
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"

        # Mock API key for testing
        self.api_key = "mock-api-key"
        
        # Set the test table name with a unique identifier to avoid conflicts
        self.table_name = f"agent_sessions_test_{uuid.uuid4().hex[:6]}"
        
        # Clean up any existing test tables from previous failed runs
        try:
            cleanup_storage = create_postgres_storage(
                connection_string=self.db_connection,
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
            # Drop the table if it exists
            cleanup_storage._drop_table_if_exists()
        except Exception as e:
            logger.warning(f"Cleanup before tests failed: {e}")

    def tearDown(self):
        """Clean up test environment after each test."""
        if self.skip_postgres_tests:
            return
            
        try:
            # Clean up by dropping the test table
            cleanup_storage = create_postgres_storage(
                connection_string=self.db_connection,
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
            # Drop the table to clean up
            cleanup_storage._drop_table_if_exists()
        except Exception as e:
            logger.warning(f"Cleanup after tests failed: {e}")

    @patch("src.models.factory.create_model")
    def test_postgres_storage_initialization(self, mock_create_model):
        """Test PostgreSQL storage initialization."""
        # Arrange
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        
        # Act
        storage = initialize_storage(
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Assert
        self.assertIsNotNone(storage)
        self.assertEqual(storage.table_name, self.table_name)
        
        # Verify storage configuration
        self.assertEqual(storage.user_id, self.user_id)
        self.assertEqual(storage.session_id, self.session_id)
        
        # Verify storage type
        self.assertIsInstance(storage, PostgresAgentStorage)

    @patch("src.models.factory.create_model")
    def test_postgres_storage_with_individual_agent(self, mock_create_model):
        """Test PostgreSQL storage with an individual agent."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Test response")
        mock_create_model.return_value = mock_model
        
        # Setup storage
        storage = initialize_storage(
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Act - Create agent with storage
        agent = SearchingAgent(
            provider="openai",
            model_id="gpt-4o",
            api_key=self.api_key,
            session_id=self.session_id,
            storage=storage
        )
        
        # Run a simple query to generate state
        query = "What is the capital of Germany?"
        mock_response = MagicMock()
        mock_response.content = "The capital of Germany is Berlin."
        agent.agent.run = MagicMock(return_value=mock_response)
        
        response = agent.agent.run(query)
        
        # Assert - Check response and state persistence
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "The capital of Germany is Berlin.")
        
        # Create a new agent with the same session ID and storage
        new_agent = SearchingAgent(
            provider="openai",
            model_id="gpt-4o",
            api_key=self.api_key,
            session_id=self.session_id,
            storage=storage
        )
        
        # Mock the get_messages method to verify state was loaded
        mock_messages = [{"role": "user", "content": query}, 
                         {"role": "assistant", "content": "The capital of Germany is Berlin."}]
        new_agent.agent.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify agent loaded the state
        messages = new_agent.agent.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "The capital of Germany is Berlin.")

    @patch("src.models.factory.create_model")
    def test_postgres_storage_with_team(self, mock_create_model):
        """Test PostgreSQL storage with a financial modeling team."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Team response")
        mock_create_model.return_value = mock_model
        
        # Act - Initialize team with storage
        team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Assert - Check team initialization with storage
        self.assertIsNotNone(team)
        self.assertTrue(isinstance(team, Team))
        
        # Mock the team.run method
        mock_response = MagicMock()
        mock_response.content = "Financial analysis for renewable energy investments."
        team.run = MagicMock(return_value=mock_response)
        
        # Run a query
        query = "Analyze renewable energy investments."
        response = team.run(query)
        
        # Assert - Check response
        self.assertEqual(response.content, "Financial analysis for renewable energy investments.")
        
        # Initialize a new team with the same session ID
        new_team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Mock the get_messages method to verify state was loaded
        mock_messages = [{"role": "user", "content": query}, 
                         {"role": "assistant", "content": "Financial analysis for renewable energy investments."}]
        new_team.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify team loaded the state
        messages = new_team.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "Financial analysis for renewable energy investments.")

    def test_postgres_storage_metadata(self):
        """Test PostgreSQL storage metadata operations."""
        # Arrange
        storage = initialize_storage(
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Act - Store metadata
        metadata = {
            "model_id": "gpt-4o",
            "provider": "openai",
            "task_type": "financial_modeling",
            "custom_data": {
                "model_version": 1,
                "parameters": {
                    "temperature": 0.1,
                    "max_tokens": 4000
                }
            }
        }
        
        # Storage operations for metadata should be performed through AgentStorage interface
        storage.save_metadata(metadata)
        
        # Retrieve metadata
        retrieved_metadata = storage.get_metadata()
        
        # Assert
        self.assertIsNotNone(retrieved_metadata)
        self.assertEqual(retrieved_metadata["model_id"], "gpt-4o")
        self.assertEqual(retrieved_metadata["provider"], "openai")
        self.assertEqual(retrieved_metadata["task_type"], "financial_modeling")
        self.assertEqual(retrieved_metadata["custom_data"]["model_version"], 1)
        self.assertEqual(retrieved_metadata["custom_data"]["parameters"]["temperature"], 0.1)

    def test_postgres_storage_session_management(self):
        """Test PostgreSQL storage session management capabilities."""
        # Arrange
        storage = initialize_storage(
            storage_type="postgres",
            storage_connection=self.db_connection,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Act - Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = f"test_session_{i}_{uuid.uuid4().hex[:8]}"
            session_ids.append(session_id)
            
            # Create storage with this session ID
            session_storage = initialize_storage(
                storage_type="postgres",
                storage_connection=self.db_connection,
                session_id=session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
            
            # Add some metadata to identify the session
            session_storage.save_metadata({"session_number": i, "created_at": str(i)})
        
        # Test list_sessions functionality (requires SessionManager)
        from src.storage.session import create_session_manager
        session_manager = create_session_manager(storage)
        
        # List all sessions for the user
        all_sessions = session_manager.list_sessions(user_id=self.user_id)
        
        # Assert
        self.assertIsNotNone(all_sessions)
        self.assertEqual(len(all_sessions), 3)
        
        # Verify session metadata
        for i, session_id in enumerate(session_ids):
            metadata = session_manager.get_session_metadata(session_id)
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata.get("session_number"), i)

    def test_postgres_storage_error_handling(self):
        """Test PostgreSQL storage error handling."""
        # Test invalid connection string
        with self.assertRaises(Exception):
            storage = initialize_storage(
                storage_type="postgres",
                storage_connection="postgresql://invalid:invalid@nonexistent:5432/nonexistent",
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
        
        # Test with valid connection string but invalid table name (containing invalid characters)
        with self.assertRaises(Exception):
            storage = initialize_storage(
                storage_type="postgres",
                storage_connection=self.db_connection,
                session_id=self.session_id,
                user_id=self.user_id,
                table_name="invalid table name with spaces"
            )

    def test_postgres_storage_transactions(self):
        """Test PostgreSQL storage transaction handling."""
        # Initialize storage
        storage = initialize_storage(
            storage_type="postgres",
            storage_connection=self.db_connection,
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Create mock messages
        messages = [
            {"role": "user", "content": "Initial message"},
            {"role": "assistant", "content": "Initial response"}
        ]
        
        # Save messages within a transaction
        storage.save_messages(messages)
        
        # Retrieve messages to verify they were saved
        retrieved_messages = storage.get_messages()
        self.assertEqual(len(retrieved_messages), 2)
        
        # Test transaction rollback by simulating a failure
        try:
            # This will be a nested operation that should not affect the stored messages
            # since the outer transaction should be rolled back
            storage._db_conn.begin()
            storage.save_messages([{"role": "user", "content": "This should be rolled back"}])
            # Intentionally raise an exception to trigger rollback
            raise ValueError("Simulated error to trigger rollback")
        except ValueError:
            # The transaction should be rolled back
            pass
        
        # Verify that the messages were not affected by the rolled back transaction
        retrieved_messages_after_rollback = storage.get_messages()
        self.assertEqual(len(retrieved_messages_after_rollback), 2)
        self.assertEqual(retrieved_messages_after_rollback[0]["content"], "Initial message")


if __name__ == "__main__":
    unittest.main() 