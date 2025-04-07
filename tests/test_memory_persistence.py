#!/usr/bin/env python3
"""
Test suite for memory persistence functionality.

This module tests that memory persists correctly across multiple API calls
and can be retrieved in subsequent sessions using the same storage backend.
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
from agno.memory.message import Message, MessageRole


class TestMemoryPersistence(unittest.TestCase):
    """Test cases for memory persistence functionality."""

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
    async def test_memory_persists_across_calls(self, mock_team, mock_create_model):
        """Test that memory persists across multiple API calls using the same session ID."""
        # First API call - create memory
        mock_team_instance1 = MagicMock()
        mock_team.return_value = mock_team_instance1
        mock_team_instance1.arun.return_value = MagicMock(content="First response")
        
        # Set up real memory for testing persistence
        memory_db = SqliteMemoryDb(table_name="agent_memories", db_file=self.db_path)
        
        with patch('src.api.main.SqliteMemoryDb', return_value=memory_db):
            with patch('src.api.main.AgentMemory') as mock_agent_memory:
                # Use a real AgentMemory so we can verify it actually gets saved
                real_memory = AgentMemory(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    memory_db=memory_db,
                    create_user_memories=True,
                    create_session_summary=True
                )
                mock_agent_memory.return_value = real_memory
                
                # Add a system message to memory
                real_memory.add_message(Message(
                    role=MessageRole.SYSTEM,
                    content="This is a system message for testing"
                ))
                
                # First request
                task_request1 = TaskRequest(
                    message="First test message",
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
                await run_task(task_request1)
                
                # Verify the message was added to the memory during the request
                self.assertEqual(len(real_memory.messages), 2)  # System message + user message
                self.assertEqual(real_memory.messages[0].role, MessageRole.SYSTEM)
                self.assertEqual(real_memory.messages[1].role, MessageRole.USER)
                self.assertEqual(real_memory.messages[1].content, "First test message")
        
        # Second API call - verify memory persists
        mock_team_instance2 = MagicMock()
        mock_team.return_value = mock_team_instance2
        mock_team_instance2.arun.return_value = MagicMock(content="Second response")
        
        with patch('src.api.main.SqliteMemoryDb', return_value=memory_db):
            with patch('src.api.main.AgentMemory') as mock_agent_memory:
                # We want to verify the memory is loaded from the database
                # So let's call the original implementation but monitor it
                second_memory = AgentMemory(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    memory_db=memory_db,
                    create_user_memories=True,
                    create_session_summary=True
                )
                mock_agent_memory.return_value = second_memory
                
                # Second request
                task_request2 = TaskRequest(
                    message="Second test message",
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
                
                # Verify previous messages were loaded from database
                self.assertGreaterEqual(len(second_memory.messages), 3)  # Should have at least 3 messages
                
                # Check that we have messages from both API calls
                roles = [msg.role for msg in second_memory.messages]
                contents = [msg.content for msg in second_memory.messages]
                
                self.assertIn(MessageRole.SYSTEM, roles)
                self.assertIn(MessageRole.USER, roles)
                self.assertIn("First test message", contents)
                self.assertIn("Second test message", contents)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('agno.memory.agent.AgentMemory')
    async def test_user_memories_persistence(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that user memories persist and can be accessed across sessions."""
        # Mock storage
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        mock_agent_memory.return_value = mock_memory_instance
        # Set up user memories for testing
        mock_memory_instance.user_memories = {
            "preferences": "The user prefers detailed explanations",
            "previous_topics": "Financial models, risk assessment"
        }
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # First request - create user memories
        task_request1 = TaskRequest(
            message="Tell me about memory persistence",
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
        await run_task(task_request1)
        
        # Verify user memories were created
        mock_agent_memory.assert_called_once()
        
        # Reset mocks for second request
        mock_agent_memory.reset_mock()
        mock_team.reset_mock()
        
        # Second request - should load existing user memories
        new_session_id = str(uuid.uuid4())  # Different session ID
        task_request2 = TaskRequest(
            message="Another question",
            provider="openai",
            model="gpt-4o",
            provider_api_key="sk-test-key",
            stream=False,
            storage_type="sqlite",
            storage_connection=self.db_path,
            session_id=new_session_id,  # Different session
            user_id=self.user_id,  # Same user
            enable_chat_history=True,
            enable_user_memories=True,
            enable_summaries=True
        )
        
        # Call run_task
        await run_task(task_request2)
        
        # Verify AgentMemory was created with same user_id
        mock_agent_memory.assert_called_once()
        self.assertEqual(mock_agent_memory.call_args[1]['user_id'], self.user_id)
        self.assertEqual(mock_agent_memory.call_args[1]['session_id'], new_session_id)

    @patch('src.api.main.create_model')
    @patch('src.api.main.Team')
    @patch('src.api.main.initialize_storage')
    @patch('agno.memory.agent.AgentMemory')
    async def test_memory_pruning(
        self, 
        mock_agent_memory,
        mock_initialize_storage, 
        mock_team,
        mock_create_model
    ):
        """Test that memory pruning works correctly based on memory_depth parameter."""
        # Mock storage
        mock_storage = MagicMock()
        mock_initialize_storage.return_value = mock_storage
        
        # Mock AgentMemory
        mock_memory_instance = MagicMock()
        # Simulate a memory with 20 messages
        mock_memory_instance.messages = [
            MagicMock(role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT, content=f"Message {i}")
            for i in range(20)
        ]
        mock_agent_memory.return_value = mock_memory_instance
        
        # Mock Team
        mock_team_instance = MagicMock()
        mock_team.return_value = mock_team_instance
        mock_team_instance.arun.return_value = MagicMock(content="Test response")
        
        # Create a TaskRequest with memory_depth set to 5
        task_request = TaskRequest(
            message="Test memory pruning",
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
            enable_summaries=True,
            memory_depth=5  # Only keep 5 most recent messages
        )
        
        # Call run_task
        await run_task(task_request)
        
        # Verify memory settings
        mock_agent_memory.assert_called_once()
        memory_kwargs = mock_agent_memory.call_args[1]
        self.assertEqual(memory_kwargs['max_messages'], 5)
        
        # Verify Team was configured with correct history depth
        mock_team.assert_called_once()
        team_kwargs = mock_team.call_args[1]
        self.assertEqual(team_kwargs['num_history_responses'], 5)


if __name__ == "__main__":
    unittest.main() 