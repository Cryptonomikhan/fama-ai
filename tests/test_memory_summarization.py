#!/usr/bin/env python3
"""
Test suite for memory summarization functionality.

This module tests the integration of Agno's memory summarization capabilities,
focusing on session summaries and conversation tracking.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
import json
import tempfile
import shutil
import uuid

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import run_task, TaskRequest
from agno.memory.agent import AgentMemory
from agno.memory.storage import SqliteMemoryDb
from agno.memory.summary import Summary
from agno.memory.message import Message, MessageRole


class TestMemorySummarization(unittest.TestCase):
    """Test cases for memory summarization functionality."""

    def setUp(self):
        """Set up test environment with temporary directory for storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memory.db")
        self.session_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())

    def tearDown(self):
        """Clean up temporary directory after tests."""
        shutil.rmtree(self.temp_dir)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('src.api.main.AgentMemory')
    async def test_summary_creation_enabled(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that session summaries are created when enabled."""
        # Mock storage
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with summaries enabled
        task_request = TaskRequest(
            message="Test summary creation",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id,
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify AgentMemory was initialized with summary-related parameters
        mock_agent_memory.assert_called_once()
        memory_kwargs = mock_agent_memory.call_args[1]
        self.assertEqual(memory_kwargs['create_session_summary'], True)
        self.assertEqual(memory_kwargs['update_session_summary_after_run'], True)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('src.api.main.AgentMemory')
    async def test_summary_creation_disabled(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that session summaries are not created when disabled."""
        # Mock storage
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with summaries disabled
        task_request = TaskRequest(
            message="Test no summary creation",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id,
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=False  # Explicitly disable summaries
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify AgentMemory was initialized with summary-related parameters disabled
        mock_agent_memory.assert_called_once()
        memory_kwargs = mock_agent_memory.call_args[1]
        self.assertEqual(memory_kwargs['create_session_summary'], False)
        self.assertEqual(memory_kwargs['update_session_summary_after_run'], False)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    async def test_summary_generation_and_persistence(self, mock_team, mock_create_model):
        """Test that summaries are generated and persisted across API calls."""
        # First API call - create memory and summary
        mock_team_instance1 = MagicMock()
        mock_team.return_value = mock_team_instance1
        mock_team_instance1.arun.return_value = MagicMock(content="First response")
        
        # Set up real memory for testing
        memory_db = SqliteMemoryDb(table_name="agent_memories", db_file=self.db_path)
        
        with patch('src.api.main.SqliteMemoryDb', return_value=memory_db):
            with patch('src.api.main.AgentMemory') as mock_agent_memory:
                # Use a real AgentMemory
                real_memory = AgentMemory(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    memory_db=memory_db,
                    create_session_summary=True,
                    update_session_summary_after_run=True
                )
                mock_agent_memory.return_value = real_memory
                
                # Manually set a summary to simulate summary generation
                test_summary = Summary(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    content="This is a test summary of the conversation",
                    updated_at="2023-06-15T12:00:00Z"
                )
                real_memory._session_summary = test_summary
                
                # Add some messages
                real_memory.add_message(Message(
                    role=MessageRole.SYSTEM,
                    content="System message for testing summaries"
                ))
                real_memory.add_message(Message(
                    role=MessageRole.USER,
                    content="Tell me about financial models"
                ))
                
                # First request
                task_request1 = TaskRequest(
                    message="How do I create a DCF model?",
                    provider="openai",
                    model="gpt-4o",
                    provider_api_key="sk-test-key",
                    stream=False,
                    storage_type="sqlite",
                    storage_connection=self.db_path,
                    session_id=self.session_id,
                    user_id=self.user_id,
                    enable_chat_history=True,
                    enable_user_memories=True,
                    enable_summaries=True
                )
                
                # Force summary to be saved - this would normally happen after run
                real_memory.save_session_summary()
                
                # Call run_task
                await run_task(task_request1)
        
        # Second API call - verify summary persists
        mock_team_instance2 = MagicMock()
        mock_team.return_value = mock_team_instance2
        mock_team_instance2.arun.return_value = MagicMock(content="Second response")
        
        with patch('src.api.main.SqliteMemoryDb', return_value=memory_db):
            with patch('src.api.main.AgentMemory') as mock_agent_memory:
                # Create a new memory object that should load from DB
                second_memory = AgentMemory(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    memory_db=memory_db,
                    create_session_summary=True,
                    update_session_summary_after_run=True
                )
                mock_agent_memory.return_value = second_memory
                
                # Second request
                task_request2 = TaskRequest(
                    message="What about Monte Carlo simulations?",
                    provider="openai",
                    model="gpt-4o",
                    provider_api_key="sk-test-key",
                    stream=False,
                    storage_type="sqlite",
                    storage_connection=self.db_path,
                    session_id=self.session_id,
                    user_id=self.user_id,
                    enable_chat_history=True,
                    enable_user_memories=True,
                    enable_summaries=True
                )
                
                # Call run_task
                await run_task(task_request2)
                
                # Verify the summary persisted
                self.assertIsNotNone(second_memory._session_summary)
                if second_memory._session_summary:
                    self.assertEqual(second_memory._session_summary.content, 
                                     "This is a test summary of the conversation")

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('src.api.main.AgentMemory')
    async def test_summary_formatting_in_messages(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that summaries are correctly formatted in agent messages."""
        # Mock storage
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory with a summary
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_summary.return_value = "Previous conversation was about financial modeling approaches and DCF models."
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with summaries enabled
        task_request = TaskRequest(
            message="Tell me more about what we discussed earlier",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=self.session_id,
            user_id=self.user_id,
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify Team was created with memory access instructions
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        instructions = team_kwargs['instructions']
        
        # Check that instructions contain memory access section
        self.assertIn("Memory Access", instructions)
        self.assertIn("conversation history", instructions)

        # Verify get_summary was called
        mock_memory_instance.get_summary.assert_called_once()
        

if __name__ == "__main__":
    unittest.main() 