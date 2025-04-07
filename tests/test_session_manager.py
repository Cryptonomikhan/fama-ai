#!/usr/bin/env python3
"""
Tests for session handling utilities in the Agno framework.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, call

# Mock the agno module to prevent actual imports
import sys
sys.modules['agno'] = MagicMock()
sys.modules['agno.utils'] = MagicMock()
sys.modules['agno.utils.log'] = MagicMock()

from src.storage.session import SessionManager, create_session_manager, StorageError
from datetime import datetime

# Mock storage class for testing
class MockStorage:
    def __init__(self):
        self.sessions = {}  # session_id -> (user_id, messages)
        self.user_sessions = {}  # user_id -> [session_id, ...]
    
    def save_session(self, session_id, user_id, messages):
        self.sessions[session_id] = (user_id, messages)
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        if session_id not in self.user_sessions[user_id]:
            self.user_sessions[user_id].append(session_id)
    
    def load_session(self, session_id):
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id][1]
    
    def delete_session(self, session_id):
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        user_id = self.sessions[session_id][0]
        if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
            self.user_sessions[user_id].remove(session_id)
        del self.sessions[session_id]
    
    def list_sessions(self, user_id=None):
        if user_id:
            return self.user_sessions.get(user_id, [])
        return list(self.sessions.keys())
    
    def get_user_id(self, session_id):
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return self.sessions[session_id][0]
    
    def test_connection(self):
        # Just a placeholder for connection testing
        return True

class TestSessionManager:
    """Tests for session management utilities."""
    
    def setup_method(self):
        """Set up test environment."""
        self.storage = MockStorage()
        self.session_manager = SessionManager(self.storage)
    
    def test_create_session_manager(self):
        """Test creating a session manager."""
        # Test successful creation
        manager = create_session_manager(self.storage)
        assert isinstance(manager, SessionManager)
        assert manager.storage == self.storage
        
        # Test error handling
        with patch('src.storage.session.SessionManager', side_effect=ValueError("Test error")):
            with pytest.raises(StorageError):
                create_session_manager(self.storage)
    
    def test_generate_session_id(self):
        """Test generating unique session IDs."""
        # Generate multiple session IDs and verify uniqueness
        session_ids = [SessionManager.generate_session_id() for _ in range(10)]
        assert len(session_ids) == len(set(session_ids))  # All IDs should be unique
        
        # Verify format (timestamp_uniqueid)
        for session_id in session_ids:
            parts = session_id.split('_')
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert len(parts[1]) == 12
    
    def test_create_session(self):
        """Test creating a new session."""
        # Create a session without metadata
        user_id = "test_user"
        session_id = self.session_manager.create_session(user_id)
        
        assert session_id in self.storage.sessions
        assert self.storage.sessions[session_id][0] == user_id
        assert len(self.storage.sessions[session_id][1]) == 0  # No messages initially
        
        # Create a session with metadata
        metadata = {"app_version": "1.0", "client_info": "test client"}
        session_id2 = self.session_manager.create_session(user_id, metadata)
        
        assert session_id2 in self.storage.sessions
        assert self.storage.sessions[session_id2][0] == user_id
        assert len(self.storage.sessions[session_id2][1]) == 1  # One system message with metadata
        assert self.storage.sessions[session_id2][1][0]["role"] == "system"
        assert "metadata" in self.storage.sessions[session_id2][1][0]
        assert self.storage.sessions[session_id2][1][0]["metadata"]["app_version"] == "1.0"
    
    def test_resume_session(self):
        """Test resuming an existing session."""
        # Create a session first
        user_id = "test_user"
        session_id = self.session_manager.create_session(user_id)
        
        # Resume the session
        resumed_user_id, messages = self.session_manager.resume_session(session_id)
        
        assert resumed_user_id == user_id
        assert isinstance(messages, list)
        
        # Try to resume non-existent session
        with pytest.raises(StorageError):
            self.session_manager.resume_session("nonexistent_session")
        
        # Try with validate_exists=False
        nonexistent_user_id, nonexistent_messages = self.session_manager.resume_session(
            "nonexistent_session", validate_exists=False)
        assert nonexistent_user_id is None
        assert nonexistent_messages == []
    
    def test_list_sessions(self):
        """Test listing available sessions."""
        # Create some sessions
        user1 = "user1"
        user2 = "user2"
        session1 = self.session_manager.create_session(user1)
        session2 = self.session_manager.create_session(user1)
        session3 = self.session_manager.create_session(user2)
        
        # List all sessions
        all_sessions = self.session_manager.list_sessions()
        assert len(all_sessions) == 3
        assert session1 in all_sessions
        assert session2 in all_sessions
        assert session3 in all_sessions
        
        # List sessions for user1
        user1_sessions = self.session_manager.list_sessions(user1)
        assert len(user1_sessions) == 2
        assert session1 in user1_sessions
        assert session2 in user1_sessions
        assert session3 not in user1_sessions
        
        # List sessions for user2
        user2_sessions = self.session_manager.list_sessions(user2)
        assert len(user2_sessions) == 1
        assert session3 in user2_sessions
    
    def test_session_metadata(self):
        """Test getting and updating session metadata."""
        # Create a session with initial metadata
        user_id = "test_user"
        initial_metadata = {"version": "1.0", "app": "test_app"}
        session_id = self.session_manager.create_session(user_id, initial_metadata)
        
        # Get metadata
        metadata = self.session_manager.get_session_metadata(session_id)
        assert metadata["session_id"] == session_id
        assert metadata["user_id"] == user_id
        assert metadata["version"] == "1.0"
        assert metadata["app"] == "test_app"
        
        # Update metadata
        updated_metadata = {"version": "2.0", "new_field": "new_value"}
        result = self.session_manager.update_session_metadata(session_id, updated_metadata)
        assert result is True
        
        # Get updated metadata
        updated = self.session_manager.get_session_metadata(session_id)
        assert updated["version"] == "2.0"  # Updated value
        assert updated["app"] == "test_app"  # Original value preserved
        assert updated["new_field"] == "new_value"  # New field added
    
    def test_delete_session(self):
        """Test deleting a session."""
        # Create a session
        user_id = "test_user"
        session_id = self.session_manager.create_session(user_id)
        
        # Verify it exists
        assert session_id in self.storage.sessions
        
        # Delete it
        result = self.session_manager.delete_session(session_id)
        assert result is True
        
        # Verify it's gone
        assert session_id not in self.storage.sessions
        
        # Try to delete non-existent session
        with pytest.raises(StorageError):
            self.session_manager.delete_session("nonexistent_session")
    
    def test_session_exists(self):
        """Test checking if a session exists."""
        # Create a session
        user_id = "test_user"
        session_id = self.session_manager.create_session(user_id)
        
        # Check if it exists
        assert self.session_manager._session_exists(session_id) is True
        
        # Check if non-existent session exists
        assert self.session_manager._session_exists("nonexistent_session") is False
    
    def test_extract_user_id(self):
        """Test extracting user ID from messages."""
        # Create messages with user ID in metadata
        messages = [
            {
                "role": "system",
                "content": "Session initialized",
                "metadata": {"user_id": "metadata_user"}
            },
            {"role": "user", "content": "Hello"}
        ]
        
        # Extract user ID
        user_id = self.session_manager._extract_user_id_from_messages("test_session", messages)
        assert user_id == "metadata_user"
        
        # Test with no user ID in metadata
        messages = [
            {"role": "system", "content": "Session initialized", "metadata": {}},
            {"role": "user", "content": "Hello"}
        ]
        
        # Should use fallback based on session ID
        session_id = "1234567890_abcdef123456"
        user_id = self.session_manager._extract_user_id_from_messages(session_id, messages)
        assert user_id == "user_1234567890"
    
    def test_sanitize_metadata(self):
        """Test sanitizing metadata to ensure it's serializable."""
        # Create metadata with various types
        class NonSerializable:
            def __str__(self):
                return "NonSerializable object"
        
        metadata = {
            "string": "text",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"a": 1, "b": 2},
            "non_serializable": NonSerializable(),
            "date": datetime.now()
        }
        
        # Sanitize it
        sanitized = self.session_manager._sanitize_metadata(metadata)
        
        # Verify serializable values are preserved
        assert sanitized["string"] == "text"
        assert sanitized["number"] == 42
        assert sanitized["boolean"] is True
        assert sanitized["list"] == [1, 2, 3]
        assert sanitized["dict"] == {"a": 1, "b": 2}
        
        # Verify non-serializable values are converted to strings
        assert isinstance(sanitized["non_serializable"], str)
        assert "NonSerializable object" in sanitized["non_serializable"]
        assert isinstance(sanitized["date"], str)
    
    def test_connection_retry(self):
        """Test connection retry mechanism."""
        # Create a failing storage
        failing_storage = MagicMock()
        failing_storage.save_session.side_effect = [
            ConnectionError("Connection failed"),
            None  # Second call succeeds
        ]
        failing_storage.test_connection.return_value = True
        
        # Create session manager with failing storage
        with patch('src.storage.session.ensure_storage_healthy'):
            manager = SessionManager(failing_storage)
        
        # Should succeed on the second attempt
        session_id = manager.create_session("test_user")
        
        # Verify save_session was called twice
        assert failing_storage.save_session.call_count == 2
    
    def test_error_handling(self):
        """Test error handling in session manager methods."""
        # Create a storage that raises exceptions
        error_storage = MagicMock()
        error_storage.load_session.side_effect = ValueError("Session not found")
        error_storage.test_connection.return_value = True
        
        # Create session manager with error storage
        with patch('src.storage.session.ensure_storage_healthy'):
            manager = SessionManager(error_storage)
        
        # Resume session should raise StorageError
        with pytest.raises(StorageError):
            manager.resume_session("nonexistent_session")

if __name__ == "__main__":
    pytest.main() 