#!/usr/bin/env python3
"""
Test suite for DynamoDB storage integration with Agno agents and teams.

This module tests the DynamoDB storage connector's functionality with both 
individual agents and teams, ensuring proper state persistence across 
different interactions.
"""

import unittest
import os
import json
import uuid
import logging
import boto3
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from src.storage.factory import initialize_storage
from src.storage.dynamodb import create_dynamodb_storage
from src.agents.searcher import SearchingAgent
from src.agents.init_agents import initialize_financial_modeling_team
from agno.agent import Agent
from agno.team.team import Team
from agno.storage.agent.dynamodb import DynamoDbAgentStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDynamoDBStorage(unittest.TestCase):
    """Test suite for DynamoDB storage integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Use environment variables or default test configuration
        cls.region_name = os.environ.get("TEST_DYNAMODB_REGION", "us-east-1")
        cls.endpoint_url = os.environ.get("TEST_DYNAMODB_ENDPOINT", "http://localhost:8000")
        cls.aws_access_key_id = os.environ.get("TEST_AWS_ACCESS_KEY_ID", "dummy_access_key")
        cls.aws_secret_access_key = os.environ.get("TEST_AWS_SECRET_ACCESS_KEY", "dummy_secret_key")
        
        # Skip tests if environment variable is explicitly set to skip
        cls.skip_dynamodb_tests = os.environ.get("SKIP_DYNAMODB_TESTS", "").lower() == "true"
        if cls.skip_dynamodb_tests:
            logger.warning("DynamoDB tests are being skipped based on environment configuration.")

    def setUp(self):
        """Set up test environment before each test."""
        if self.skip_dynamodb_tests:
            self.skipTest("DynamoDB tests are disabled via environment variable.")
            
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.user_id = "test_user"

        # Mock API key for testing
        self.api_key = "mock-api-key"
        
        # Set the test table name with a unique identifier to avoid conflicts
        self.table_name = f"agent_sessions_test_{uuid.uuid4().hex[:6]}"
        
        # Connection parameters for DynamoDB
        self.dynamodb_params = {
            "region_name": self.region_name,
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "create_table_if_not_exists": True
        }
        
        # Clean up any existing test tables from previous failed runs
        try:
            cleanup_storage = create_dynamodb_storage(
                table_name=self.table_name,
                session_id=self.session_id,
                user_id=self.user_id,
                **self.dynamodb_params
            )
            # Delete the table if it exists
            cleanup_storage._delete_table_if_exists()
        except Exception as e:
            logger.warning(f"Cleanup before tests failed: {e}")

    def tearDown(self):
        """Clean up test environment after each test."""
        if self.skip_dynamodb_tests:
            return
            
        try:
            # Clean up by deleting the test table
            cleanup_storage = create_dynamodb_storage(
                table_name=self.table_name,
                session_id=self.session_id,
                user_id=self.user_id,
                **self.dynamodb_params
            )
            # Delete the table to clean up
            cleanup_storage._delete_table_if_exists()
        except Exception as e:
            logger.warning(f"Cleanup after tests failed: {e}")

    @patch("boto3.resource")
    @patch("src.models.factory.create_model")
    def test_dynamodb_storage_initialization(self, mock_create_model, mock_boto3_resource):
        """Test DynamoDB storage initialization."""
        # Arrange
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Act
        storage = initialize_storage(
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
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
        self.assertIsInstance(storage, DynamoDbAgentStorage)
        
        # Verify boto3 was called with the right parameters
        mock_boto3_resource.assert_called_with(
            'dynamodb',
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

    @patch("boto3.resource")
    @patch("src.models.factory.create_model")
    def test_dynamodb_storage_with_individual_agent(self, mock_create_model, mock_boto3_resource):
        """Test DynamoDB storage with an individual agent."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Test response")
        mock_create_model.return_value = mock_model
        
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Setup storage
        storage = initialize_storage(
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Mock table.get_item to return None initially (no session exists)
        mock_table.get_item.return_value = {"Item": None}
        
        # Act - Create agent with storage
        agent = SearchingAgent(
            provider="openai",
            model_id="gpt-4o",
            api_key=self.api_key,
            session_id=self.session_id,
            storage=storage
        )
        
        # Run a simple query to generate state
        query = "What is the capital of Japan?"
        mock_response = MagicMock()
        mock_response.content = "The capital of Japan is Tokyo."
        agent.agent.run = MagicMock(return_value=mock_response)
        
        response = agent.agent.run(query)
        
        # Assert - Check response and state persistence
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "The capital of Japan is Tokyo.")
        
        # Mock the table.put_item was called (to save state)
        mock_table.put_item.assert_called()
        
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
                         {"role": "assistant", "content": "The capital of Japan is Tokyo."}]
                         
        # Now mock table.get_item to return our session data
        mock_table.get_item.return_value = {
            "Item": {
                "sessionId": self.session_id,
                "userId": self.user_id,
                "messages": json.dumps(mock_messages),
                "metadata": json.dumps({})
            }
        }
        
        new_agent.agent.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify agent loaded the state
        messages = new_agent.agent.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "The capital of Japan is Tokyo.")

    @patch("boto3.resource")
    @patch("src.models.factory.create_model")
    def test_dynamodb_storage_with_team(self, mock_create_model, mock_boto3_resource):
        """Test DynamoDB storage with a financial modeling team."""
        # Arrange
        mock_model = MagicMock()
        mock_model.generate.return_value = MagicMock(content="Team response")
        mock_create_model.return_value = mock_model
        
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Mock table.get_item to return None initially (no session exists)
        mock_table.get_item.return_value = {"Item": None}
        
        # Act - Initialize team with storage
        team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Assert - Check team initialization with storage
        self.assertIsNotNone(team)
        self.assertTrue(isinstance(team, Team))
        
        # Mock the team.run method
        mock_response = MagicMock()
        mock_response.content = "Financial analysis for technology investments."
        team.run = MagicMock(return_value=mock_response)
        
        # Run a query
        query = "Analyze technology investments."
        response = team.run(query)
        
        # Assert - Check response
        self.assertEqual(response.content, "Financial analysis for technology investments.")
        
        # Mock table.put_item was called (to save state)
        mock_table.put_item.assert_called()
        
        # Initialize a new team with the same session ID
        mock_messages = [{"role": "user", "content": query}, 
                         {"role": "assistant", "content": "Financial analysis for technology investments."}]
                         
        # Now mock table.get_item to return our session data
        mock_table.get_item.return_value = {
            "Item": {
                "sessionId": self.session_id,
                "userId": self.user_id,
                "messages": json.dumps(mock_messages),
                "metadata": json.dumps({})
            }
        }
        
        new_team = initialize_financial_modeling_team(
            api_key=self.api_key,
            provider="openai",
            model_id="gpt-4o",
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
            session_id=self.session_id,
            user_id=self.user_id,
            table_name=self.table_name
        )
        
        # Mock the get_messages method to verify state was loaded
        new_team.get_messages = MagicMock(return_value=mock_messages)
        
        # Assert - Verify team loaded the state
        messages = new_team.get_messages()
        self.assertIsNotNone(messages)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], query)
        self.assertEqual(messages[1]["content"], "Financial analysis for technology investments.")

    @patch("boto3.resource")
    def test_dynamodb_storage_metadata(self, mock_boto3_resource):
        """Test DynamoDB storage metadata operations."""
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Mock table.get_item to return None initially (no session exists)
        mock_table.get_item.return_value = {"Item": None}
        
        # Arrange
        storage = initialize_storage(
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
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
        
        # Verify put_item was called with the right parameters
        mock_table.put_item.assert_called()
        
        # Now mock get_item to return our metadata
        mock_table.get_item.return_value = {
            "Item": {
                "sessionId": self.session_id,
                "userId": self.user_id,
                "messages": json.dumps([]),
                "metadata": json.dumps(metadata)
            }
        }
        
        # Retrieve metadata
        retrieved_metadata = storage.get_metadata()
        
        # Assert
        self.assertIsNotNone(retrieved_metadata)
        self.assertEqual(retrieved_metadata["model_id"], "gpt-4o")
        self.assertEqual(retrieved_metadata["provider"], "openai")
        self.assertEqual(retrieved_metadata["task_type"], "financial_modeling")
        self.assertEqual(retrieved_metadata["custom_data"]["model_version"], 1)
        self.assertEqual(retrieved_metadata["custom_data"]["parameters"]["temperature"], 0.1)

    @patch("boto3.resource")
    def test_dynamodb_storage_session_management(self, mock_boto3_resource):
        """Test DynamoDB storage session management capabilities."""
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Arrange
        storage = initialize_storage(
            storage_type="dynamodb",
            storage_connection=json.dumps(self.dynamodb_params),
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
                storage_type="dynamodb",
                storage_connection=json.dumps(self.dynamodb_params),
                session_id=session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
            
            # Mock saving metadata
            session_storage.save_metadata({"session_number": i, "created_at": str(i)})
        
        # Mock scan operation to return our sessions
        mock_items = []
        for i, session_id in enumerate(session_ids):
            mock_items.append({
                "sessionId": session_id,
                "userId": self.user_id,
                "messages": json.dumps([]),
                "metadata": json.dumps({"session_number": i, "created_at": str(i)})
            })
        
        mock_table.scan.return_value = {"Items": mock_items}
        
        # Test list_sessions functionality (requires SessionManager)
        from src.storage.session import create_session_manager
        session_manager = create_session_manager(storage)
        
        # List all sessions for the user
        all_sessions = session_manager.list_sessions(user_id=self.user_id)
        
        # Assert
        self.assertIsNotNone(all_sessions)
        self.assertEqual(len(all_sessions), 3)
        
        # Mock get_item to return session metadata for each session
        for i, session_id in enumerate(session_ids):
            mock_table.get_item.return_value = {
                "Item": {
                    "sessionId": session_id,
                    "userId": self.user_id,
                    "messages": json.dumps([]),
                    "metadata": json.dumps({"session_number": i, "created_at": str(i)})
                }
            }
            
            # Verify session metadata
            metadata = session_manager.get_session_metadata(session_id)
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata.get("session_number"), i)

    @patch("boto3.resource")
    def test_dynamodb_storage_error_handling(self, mock_boto3_resource):
        """Test DynamoDB storage error handling."""
        # Test invalid AWS credentials (simulate ClientError)
        mock_resource = MagicMock()
        mock_boto3_resource.return_value = mock_resource
        mock_resource.Table.side_effect = ClientError(
            {'Error': {'Code': 'InvalidCredentials', 'Message': 'The security token included in the request is invalid'}},
            'Table'
        )
        
        with self.assertRaises(Exception):
            storage = initialize_storage(
                storage_type="dynamodb",
                storage_connection=json.dumps({
                    "region_name": self.region_name,
                    "aws_access_key_id": "invalid_key",
                    "aws_secret_access_key": "invalid_secret",
                }),
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )
        
        # Test missing region_name
        with self.assertRaises(ValueError):
            storage = initialize_storage(
                storage_type="dynamodb",
                storage_connection=json.dumps({
                    "aws_access_key_id": self.aws_access_key_id,
                    "aws_secret_access_key": self.aws_secret_access_key,
                }),
                session_id=self.session_id,
                user_id=self.user_id,
                table_name=self.table_name
            )

    @patch("boto3.resource")
    def test_dynamodb_storage_table_operations(self, mock_boto3_resource):
        """Test DynamoDB storage table creation and deletion."""
        # Mock the DynamoDB resource and table
        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_table.table_status = "ACTIVE"
        mock_resource.Table.return_value = mock_table
        mock_resource.create_table.return_value = mock_table
        mock_boto3_resource.return_value = mock_resource
        
        # Mock table.get_item to return None initially (no session exists)
        mock_table.get_item.return_value = {"Item": None}
        
        # Test table creation
        storage = create_dynamodb_storage(
            table_name=self.table_name,
            session_id=self.session_id,
            user_id=self.user_id,
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            create_table_if_not_exists=True
        )
        
        # Verify create_table was called
        self.assertIsNotNone(storage)
        
        # Mock table.meta.client.describe_table to raise ResourceNotFoundException
        mock_table.meta.client.describe_table.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            'DescribeTable'
        )
        
        # Test table creation when table doesn't exist
        storage._create_table_if_not_exists()
        
        # Verify create_table was called with the right parameters
        mock_resource.create_table.assert_called()
        
        # Test table deletion
        storage._delete_table_if_exists()
        
        # Verify delete was called
        mock_table.delete.assert_called()


if __name__ == "__main__":
    unittest.main() 