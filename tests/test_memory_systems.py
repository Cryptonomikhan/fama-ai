#!/usr/bin/env python3
"""
Test suite for memory systems functionality.

This module tests the integration of Agno's memory systems with our API,
focusing on chat history, user memories, and conversation summaries.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import run_task, TaskRequest
from agno.memory.agent import AgentMemory
from agno.memory.message import Message, MessageRole


class TestMemorySystems(unittest.TestCase):
    """Test cases for memory systems functionality."""

    def setUp(self):
        """Set up test environment with temporary directory for storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")

    def tearDown(self):
        """Clean up temporary directory after tests."""
        shutil.rmtree(self.temp_dir)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('agno.memory.agent.AgentMemory')
    @patch('src.api.main.SqliteMemoryDb')
    async def test_memory_initialization(
        self, 
        mock_sqlite_db,
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that memory is correctly initialized based on TaskRequest parameters."""
        # Mock storage initialization
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with memory parameters
        task_request = TaskRequest(
            message="Test message with memory",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id="test-session-123",
            user_id="test-user-456",
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True,
            memory_depth=15
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify storage was initialized correctly
        mock_initialize_storage.assert_called_once_with(
            storage_type="sqlite",
            storage_connection=self.db_path,
            table_name="agent_sessions",
            session_id="test-session-123",
            user_id="test-user-456"
        )
        
        # Verify SqliteMemoryDb was created correctly
        mock_sqlite_db.assert_called_once()
        self.assertEqual(mock_sqlite_db.call_args[1]['table_name'], "agent_memories")
        self.assertEqual(mock_sqlite_db.call_args[1]['db_file'], self.db_path)
        
        # Verify AgentMemory was initialized correctly
        mock_agent_memory.assert_called_once()
        memory_kwargs = mock_agent_memory.call_args[1]
        self.assertEqual(memory_kwargs['create_user_memories'], True)
        self.assertEqual(memory_kwargs['update_user_memories_after_run'], True)
        self.assertEqual(memory_kwargs['create_session_summary'], True)
        self.assertEqual(memory_kwargs['update_session_summary_after_run'], True)
        self.assertEqual(memory_kwargs['max_messages'], 15)
        
        # Verify Team was created with memory configuration
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        self.assertEqual(team_kwargs['memory'], mock_memory_instance)
        self.assertEqual(team_kwargs['storage'], mock_storage)
        self.assertEqual(team_kwargs['add_history_to_messages'], True)
        self.assertEqual(team_kwargs['num_history_responses'], 15)
        self.assertEqual(team_kwargs['read_chat_history'], True)
        self.assertEqual(team_kwargs['session_id'], "test-session-123")
        self.assertEqual(team_kwargs['user_id'], "test-user-456")

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    async def test_no_memory_when_no_storage(
        self, 
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that memory is not initialized when no storage is provided."""
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest without storage but with memory parameters
        task_request = TaskRequest(
            message="Test message without storage",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify Team was created without memory configuration
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        self.assertNotIn('memory', team_kwargs) or self.assertIsNone(team_kwargs.get('memory'))

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('src.api.main.AgentMemory')
    async def test_memory_features_configuration(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that memory features are correctly configured based on TaskRequest parameters."""
        # Mock storage initialization
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with partial memory features enabled
        task_request = TaskRequest(
            message="Test message with partial memory features",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id="test-session-123",
            user_id="test-user-456",
            enable_chat_history=True,
            enable_user_memories=False,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify AgentMemory was initialized with correct features
        mock_agent_memory.assert_called_once()
        memory_kwargs = mock_agent_memory.call_args[1]
        self.assertEqual(memory_kwargs['create_user_memories'], False)
        self.assertEqual(memory_kwargs['update_user_memories_after_run'], False)
        self.assertEqual(memory_kwargs['create_session_summary'], True)
        self.assertEqual(memory_kwargs['update_session_summary_after_run'], True)
        
        # Verify Team was created with correct memory configuration
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        self.assertEqual(team_kwargs['add_history_to_messages'], True)
        self.assertEqual(team_kwargs['read_chat_history'], True)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('src.api.main.AgentMemory')
    async def test_memory_instructions_included(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that memory-specific instructions are included when memory is enabled."""
        # Mock storage initialization
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with memory features enabled
        task_request = TaskRequest(
            message="Test message for memory instructions",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id="test-session-123",
            user_id="test-user-456",
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify Team was created with instructions containing memory section
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        instructions = team_kwargs['instructions']
        
        # Check that memory instructions are included
        self.assertIn("Memory Access", instructions)
        self.assertIn("conversation history", instructions)


if __name__ == "__main__":
    unittest.main() 