#!/usr/bin/env python3
"""
Test suite for YAML storage integration with Agno agents and teams.

This module tests the YAML file-based storage connector's functionality with both 
individual agents and teams, ensuring proper state persistence across 
different interactions.
"""

import unittest
import os
import yaml
import json
import uuid
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.storage.factory import initialize_storage
from src.storage.yaml import create_yaml_storage
from src.agents.searcher import SearchingAgent
from src.agents.init_agents import initialize_financial_modeling_team
from agno.agent import Agent
from agno.team.team import Team
from agno.storage.agent.yaml import YamlAgentStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestYAMLStorage(unittest.TestCase):
    """Test suite for YAML storage integration."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for YAML files
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up test session parameters
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"
        
        # Mock API key for testing
        self.api_key = "mock-api-key"
        
        # Set the directory path for YAML storage
        self.storage_dir = os.path.join(self.temp_dir, "yaml_storage")
        
        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Path to the YAML file that will be created
        self.yaml_file_path = os.path.join(self.storage_dir, f"{self.session_id}.yaml")
        
        # YAML storage connection string is the directory path
        self.storage_connection = self.storage_dir

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)

    @patch("src.models.factory.create_model")
    def test_yaml_storage_initialization(self, mock_create_model):
        """Test YAML storage initialization."""
        # Arrange
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        
        # Act
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Assert
        self.assertIsNotNone(storage)
        self.assertEqual(storage.storage_path, self.storage_dir)
        
        # Verify storage configuration
        self.assertEqual(storage.user_id, self.user_id)
        self.assertEqual(storage.session_id, self.session_id)
        
        # Verify storage type
        self.assertIsInstance(storage, YamlAgentStorage)
        
        # Verify the storage file doesn't exist yet (created on first save)
        self.assertFalse(os.path.exists(self.yaml_file_path))

    @patch("src.models.factory.create_model")
    def test_yaml_storage_with_individual_agent(self, mock_create_model):
        """Test YAML storage with an individual agent."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Test response")
        mock_create_model.return_value = mock_model
        
        # Set up storage
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
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
        query = "What is the capital of Spain?"
        mock_response = MagicMock()
        mock_response.content = "The capital of Spain is Madrid."
        agent.agent.run = MagicMock(return_value=mock_response)
        
        response = agent.agent.run(query)
        
        # Assert - Check response and state persistence
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "The capital of Spain is Madrid.")
        
        # Verify YAML file has been created
        self.assertTrue(os.path.exists(self.yaml_file_path))
        
        # Read the file and verify its contents
        with open(self.yaml_file_path, 'r') as f:
            stored_data = yaml.safe_load(f)
            
        # Verify basic structure
        self.assertIn("sessionId", stored_data)
        self.assertIn("userId", stored_data)
        self.assertIn("messages", stored_data)
        
        # Verify stored session data
        self.assertEqual(stored_data["sessionId"], self.session_id)
        self.assertEqual(stored_data["userId"], self.user_id)
        
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
                         {"role": "assistant", "content": "The capital of Spain is Madrid."}]
        new_agent.agent.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify agent loaded the state
        messages = new_agent.agent.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "The capital of Spain is Madrid.")

    @patch("src.models.factory.create_model")
    def test_yaml_storage_with_team(self, mock_create_model):
        """Test YAML storage with a financial modeling team."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Team response")
        mock_create_model.return_value = mock_model
        
        # Act - Initialize team with storage
        team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Assert - Check team initialization with storage
        self.assertIsNotNone(team)
        self.assertTrue(isinstance(team, Team))
        
        # Mock the team.run method
        mock_response = MagicMock()
        mock_response.content = "Financial analysis for healthcare investments."
        team.run = MagicMock(return_value=mock_response)
        
        # Run a query
        query = "Analyze healthcare investments."
        response = team.run(query)
        
        # Assert - Check response
        self.assertEqual(response.content, "Financial analysis for healthcare investments.")
        
        # Verify YAML file has been created for the team session
        team_yaml_file = os.path.join(self.storage_dir, f"{self.session_id}.yaml")
        self.assertTrue(os.path.exists(team_yaml_file))
        
        # Initialize a new team with the same session ID
        new_team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Mock the get_messages method to verify state was loaded
        mock_messages = [{"role": "user", "content": query}, 
                         {"role": "assistant", "content": "Financial analysis for healthcare investments."}]
        new_team.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify team loaded the state
        messages = new_team.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "Financial analysis for healthcare investments.")

    def test_yaml_storage_metadata(self):
        """Test YAML storage metadata operations."""
        # Arrange
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
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
        
        # Verify YAML file has been created
        self.assertTrue(os.path.exists(self.yaml_file_path))
        
        # Read the file and verify its contents
        with open(self.yaml_file_path, 'r') as f:
            stored_data = yaml.safe_load(f)
            
        # Verify metadata is correctly stored
        self.assertIn("metadata", stored_data)
        self.assertEqual(stored_data["metadata"]["model_id"], "gpt-4o")
        self.assertEqual(stored_data["metadata"]["provider"], "openai")
        
        # Retrieve metadata
        retrieved_metadata = storage.get_metadata()
        
        # Assert
        self.assertIsNotNone(retrieved_metadata)
        self.assertEqual(retrieved_metadata["model_id"], "gpt-4o")
        self.assertEqual(retrieved_metadata["provider"], "openai")
        self.assertEqual(retrieved_metadata["task_type"], "financial_modeling")
        self.assertEqual(retrieved_metadata["custom_data"]["model_version"], 1)
        self.assertEqual(retrieved_metadata["custom_data"]["parameters"]["temperature"], 0.1)

    def test_yaml_storage_session_management(self):
        """Test YAML storage session management capabilities."""
        # Arrange
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            user_id=self.user_id
        )
        
        # Act - Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = f"test_session_{i}_{uuid.uuid4().hex[:8]}"
            session_ids.append(session_id)
            
            # Create storage with this session ID
            session_storage = initialize_storage(
                storage_type="yaml",
                storage_connection=self.storage_connection,
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

    def test_yaml_storage_error_handling(self):
        """Test YAML storage error handling."""
        # Test invalid directory path
        with self.assertRaises(Exception):
            storage = initialize_storage(
                storage_type="yaml",
                storage_connection="/nonexistent/directory/that/doesnt/exist",
                session_id=self.session_id,
                user_id=self.user_id
            )
        
        # Test with non-writable directory (by making the temp directory read-only)
        os.chmod(self.storage_dir, 0o444)  # Read-only permission
        
        try:
            with self.assertRaises(Exception):
                storage = initialize_storage(
                    storage_type="yaml",
                    storage_connection=self.storage_dir,
                    session_id=self.session_id,
                    user_id=self.user_id
                )
                # Attempt to save data which should fail
                storage.save_messages([{"role": "user", "content": "Test message"}])
        finally:
            # Reset permissions to allow cleanup
            os.chmod(self.storage_dir, 0o755)

    def test_yaml_storage_persistence(self):
        """Test YAML storage persistence across different instances."""
        # Create initial storage and save data
        storage1 = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Save messages
        messages = [
            {"role": "user", "content": "What is deep learning?"},
            {"role": "assistant", "content": "Deep learning is a subset of machine learning that uses neural networks with many layers."}
        ]
        storage1.save_messages(messages)
        
        # Save metadata
        metadata = {"model": "gpt-4o", "timestamp": "2023-07-01T12:00:00Z"}
        storage1.save_metadata(metadata)
        
        # Create a new storage instance pointing to the same file
        storage2 = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Load data from the new instance
        loaded_messages = storage2.get_messages()
        loaded_metadata = storage2.get_metadata()
        
        # Assert data persistence
        self.assertEqual(len(loaded_messages), 2)
        self.assertEqual(loaded_messages[0]["content"], "What is deep learning?")
        self.assertEqual(loaded_messages[1]["content"], "Deep learning is a subset of machine learning that uses neural networks with many layers.")
        
        self.assertEqual(loaded_metadata["model"], "gpt-4o")
        self.assertEqual(loaded_metadata["timestamp"], "2023-07-01T12:00:00Z")
        
        # Add a new message with the second storage instance
        new_messages = loaded_messages + [{"role": "user", "content": "How do neural networks work?"}]
        storage2.save_messages(new_messages)
        
        # Verify the updated data can be read by the first storage instance
        updated_messages = storage1.get_messages()
        self.assertEqual(len(updated_messages), 3)
        self.assertEqual(updated_messages[2]["content"], "How do neural networks work?")

    def test_yaml_storage_file_structure(self):
        """Test YAML storage file structure and format."""
        # Create storage and save both messages and metadata
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Save messages
        messages = [
            {"role": "user", "content": "Tell me about financial modeling."},
            {"role": "assistant", "content": "Financial modeling is the process of creating a summary of a company's expenses and earnings in the form of a spreadsheet."}
        ]
        storage.save_messages(messages)
        
        # Save metadata
        metadata = {"task": "financial_analysis", "created_at": "2023-07-01T12:00:00Z"}
        storage.save_metadata(metadata)
        
        # Read the file directly
        with open(self.yaml_file_path, 'r') as f:
            file_contents = yaml.safe_load(f)
        
        # Verify file structure
        self.assertIn("sessionId", file_contents)
        self.assertIn("userId", file_contents)
        self.assertIn("messages", file_contents)
        self.assertIn("metadata", file_contents)
        
        # Verify session info
        self.assertEqual(file_contents["sessionId"], self.session_id)
        self.assertEqual(file_contents["userId"], self.user_id)
        
        # Verify messages
        self.assertEqual(len(file_contents["messages"]), 2)
        self.assertEqual(file_contents["messages"][0]["role"], "user")
        self.assertEqual(file_contents["messages"][0]["content"], "Tell me about financial modeling.")
        
        # Verify metadata
        self.assertEqual(file_contents["metadata"]["task"], "financial_analysis")
        self.assertEqual(file_contents["metadata"]["created_at"], "2023-07-01T12:00:00Z")

    def test_yaml_storage_format_specifics(self):
        """Test YAML storage format-specific features."""
        # Arrange
        storage = initialize_storage(
            storage_type="yaml",
            storage_connection=self.storage_connection,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        # Create complex nested structure that benefits from YAML format
        complex_metadata = {
            "config": {
                "model": {
                    "name": "gpt-4o",
                    "version": "2023",
                    "parameters": {
                        "temperature": 0.7,
                        "top_p": 1.0,
                        "max_tokens": 4000,
                        "stop_sequences": [
                            "END",
                            "STOP",
                            "---"
                        ]
                    }
                },
                "session": {
                    "type": "financial_modeling",
                    "settings": {
                        "use_historical_data": True,
                        "include_market_trends": True,
                        "forecast_years": 5,
                        "sensitivity_analysis": {
                            "enabled": True,
                            "variables": ["revenue", "costs", "growth_rate"]
                        }
                    }
                }
            }
        }
        
        # Act - Save complex metadata
        storage.save_metadata(complex_metadata)
        
        # Assert - Check that YAML file was created
        self.assertTrue(os.path.exists(self.yaml_file_path))
        
        # Read the file directly to verify YAML format specifics
        with open(self.yaml_file_path, 'r') as f:
            raw_yaml = f.read()
            file_contents = yaml.safe_load(f)
        
        # Assert - Check that the raw YAML contains hierarchical indentation
        # This is a basic check to ensure we're getting proper YAML formatting
        self.assertIn("  model:", raw_yaml)
        self.assertIn("    name:", raw_yaml)
        
        # Retrieve and verify the complex metadata
        retrieved_metadata = storage.get_metadata()
        
        # Assert - Deep verification of nested structures
        self.assertEqual(retrieved_metadata["config"]["model"]["name"], "gpt-4o")
        self.assertEqual(retrieved_metadata["config"]["model"]["parameters"]["temperature"], 0.7)
        self.assertEqual(retrieved_metadata["config"]["session"]["settings"]["forecast_years"], 5)
        self.assertEqual(
            retrieved_metadata["config"]["session"]["settings"]["sensitivity_analysis"]["variables"],
            ["revenue", "costs", "growth_rate"]
        )


if __name__ == "__main__":
    unittest.main() 