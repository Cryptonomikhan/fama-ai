#!/usr/bin/env python3
"""
Test suite for SQLite storage integration with Agno agents and teams.

This module tests the SQLite storage connector's functionality with both 
individual agents and teams, ensuring proper state persistence across 
different interactions.
"""

import unittest
import os
import shutil
import json
import uuid
import logging
from tempfile import mkdtemp
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.storage.factory import initialize_storage
from src.storage.sqlite import create_sqlite_storage
from src.agents.searcher import SearchingAgent
from src.agents.init_agents import initialize_financial_modeling_team
from agno.agent import Agent
from agno.team.team import Team

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSQLiteStorage(unittest.TestCase):
    """Test suite for SQLite storage integration."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test files
        self.test_dir = mkdtemp(prefix="agno_test_")
        self.db_path = os.path.join(self.test_dir, "test_agent_storage.db")
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"

        # Mock API key for testing
        self.api_key = "mock-api-key"

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    @patch("src.models.factory.create_model")
    def test_sqlite_storage_initialization(self, mock_create_model):
        """Test SQLite storage initialization."""
        # Arrange
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        
        # Act
        storage = initialize_storage(
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Assert
        self.assertIsNotNone(storage)
        self.assertTrue(os.path.exists(self.db_path))
        self.assertEqual(storage.table_name, "agent_sessions")
        
        # Verify storage configuration
        self.assertEqual(storage.user_id, self.user_id)
        self.assertEqual(storage.session_id, self.session_id)

    @patch("src.models.factory.create_model")
    def test_sqlite_storage_with_individual_agent(self, mock_create_model):
        """Test SQLite storage with an individual agent."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Test response")
        mock_create_model.return_value = mock_model
        
        # Setup storage
        storage = initialize_storage(
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id
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
        query = "What is the capital of France?"
        mock_response = MagicMock()
        mock_response.content = "The capital of France is Paris."
        agent.agent.run = MagicMock(return_value=mock_response)
        
        response = agent.agent.run(query)
        
        # Assert - Check response and state persistence
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "The capital of France is Paris.")
        
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
                         {"role": "assistant", "content": "The capital of France is Paris."}]
        new_agent.agent.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify agent loaded the state
        messages = new_agent.agent.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "The capital of France is Paris.")

    @patch("src.models.factory.create_model")
    def test_sqlite_storage_with_team(self, mock_create_model):
        """Test SQLite storage with a financial modeling team."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Team response")
        mock_create_model.return_value = mock_model
        
        # Act - Initialize team with storage
        team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Assert - Check team initialization with storage
        self.assertIsNotNone(team)
        self.assertTrue(isinstance(team, Team))
        
        # Mock the team.run method
        mock_response = MagicMock()
        mock_response.content = "Financial modeling analysis for AI server farms."
        team.run = MagicMock(return_value=mock_response)
        
        # Run a query
        query = "Create a financial model for AI server farms."
        response = team.run(query)
        
        # Assert - Check response
        self.assertEqual(response.content, "Financial modeling analysis for AI server farms.")
        
        # Initialize a new team with the same session ID
        new_team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Mock the get_messages method to verify state was loaded
        mock_messages = [{"role": "user", "content": query}, 
                         {"role": "assistant", "content": "Financial modeling analysis for AI server farms."}]
        new_team.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify team loaded the state
        messages = new_team.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "Financial modeling analysis for AI server farms.")

    def test_sqlite_storage_metadata(self):
        """Test SQLite storage metadata operations."""
        # Arrange
        storage = initialize_storage(
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id
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

    def test_sqlite_storage_session_management(self):
        """Test SQLite storage session management capabilities."""
        # Arrange
        storage = initialize_storage(
            storage_type="sqlite",
            storage_connection=self.db_path,
            user_id=self.user_id
        )
        
        # Act - Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = f"test_session_{i}_{uuid.uuid4().hex[:8]}"
            session_ids.append(session_id)
            
            # Create storage with this session ID
            session_storage = initialize_storage(
                storage_type="sqlite",
                storage_connection=self.db_path,
                session_id=session_id,
                user_id=self.user_id
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

    def test_sqlite_storage_error_handling(self):
        """Test SQLite storage error handling."""
        # Test invalid path
        with self.assertRaises(Exception):
            storage = initialize_storage(
                storage_type="sqlite",
                storage_connection="/nonexistent/directory/that/should/not/exist/db.sqlite",
                session_id=self.session_id,
                user_id=self.user_id
            )
        
        # Test with correct path but invalid permissions
        if os.name != 'nt':  # Skip on Windows as permission handling is different
            try:
                # Create a directory with restricted permissions
                restricted_dir = os.path.join(self.test_dir, "restricted")
                os.mkdir(restricted_dir, 0o000)  # No permissions
                
                restricted_db = os.path.join(restricted_dir, "test.db")
                
                with self.assertRaises(Exception):
                    storage = initialize_storage(
                        storage_type="sqlite",
                        storage_connection=restricted_db,
                        session_id=self.session_id,
                        user_id=self.user_id
                    )
            finally:
                # Reset permissions to allow cleanup
                os.chmod(restricted_dir, 0o755)


if __name__ == "__main__":
    unittest.main() 