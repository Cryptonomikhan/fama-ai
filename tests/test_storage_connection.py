#!/usr/bin/env python3
"""
Tests for storage connection error handling in the Agno framework.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, call

# Mock the agno module to prevent actual imports
import sys
sys.modules['agno'] = MagicMock()
sys.modules['agno.storage'] = MagicMock()
sys.modules['agno.storage.agent'] = MagicMock()
sys.modules['agno.storage.error'] = MagicMock()
sys.modules['agno.utils'] = MagicMock()
sys.modules['agno.utils.log'] = MagicMock()

from src.storage.factory import initialize_storage, StorageConnectionError, StorageError
from src.storage.connection import (
    with_connection_retry,
    test_storage_connection,
    ensure_storage_healthy,
    monitor_connection_health
)

# Mock storage classes
class MockStorage:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def test_connection(self):
        pass
    
    def list_sessions(self):
        return []
    
    def save_session(self, session_id, user_id, messages):
        pass
    
    def load_session(self, session_id):
        return []
    
    def delete_session(self, session_id):
        pass

class TestStorageConnectionError:
    """Tests for storage connection error handling."""
    
    @patch('src.storage.factory.create_sqlite_storage')
    def test_connection_retry_on_failure(self, mock_create_sqlite):
        """Test that connection is retried on failure."""
        # Configure the mock to fail twice, then succeed
        mock_storage = MagicMock()
        mock_create_sqlite.side_effect = [
            ConnectionError("Test connection error 1"),
            ConnectionError("Test connection error 2"),
            mock_storage
        ]
        
        # Patch the test_storage_connection function to avoid actual testing
        with patch('src.storage.connection.test_storage_connection', return_value={"success": True}):
            # Set retry params for faster tests
            storage = initialize_storage(
                storage_type="sqlite",
                storage_connection="memory.db",
                max_retries=3,
                retry_delay=0.01
            )
        
        # Should have been called 3 times (2 failures, 1 success)
        assert mock_create_sqlite.call_count == 3
        assert storage == mock_storage
    
    @patch('src.storage.factory.create_sqlite_storage')
    def test_connection_failure_after_max_retries(self, mock_create_sqlite):
        """Test that connection fails after max retries."""
        # Configure the mock to always fail
        error_message = "Test persistent connection error"
        mock_create_sqlite.side_effect = ConnectionError(error_message)
        
        # Set retry params for faster tests
        with pytest.raises(StorageConnectionError) as excinfo:
            initialize_storage(
                storage_type="sqlite",
                storage_connection="memory.db",
                max_retries=2,
                retry_delay=0.01
            )
        
        # Should have been called the maximum number of times
        assert mock_create_sqlite.call_count == 2
        assert error_message in str(excinfo.value)
    
    @patch('src.storage.factory.create_sqlite_storage')
    def test_non_connection_error_no_retry(self, mock_create_sqlite):
        """Test that non-connection errors are not retried."""
        # Configure the mock to raise a non-connection error
        error_message = "Non-connection error"
        mock_create_sqlite.side_effect = ValueError(error_message)
        
        # Set retry params for faster tests
        with pytest.raises(StorageError) as excinfo:
            initialize_storage(
                storage_type="sqlite",
                storage_connection="memory.db",
                max_retries=3,
                retry_delay=0.01
            )
        
        # Should have been called only once
        assert mock_create_sqlite.call_count == 1
        assert error_message in str(excinfo.value)
    
    def test_with_connection_retry_decorator(self):
        """Test the connection retry decorator."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            ConnectionError("Test error 1"),
            ConnectionError("Test error 2"),
            "success"
        ]
        
        # Create a decorated function
        @with_connection_retry(max_retries=2, retry_delay=0.01)
        def test_func():
            return mock_func()
        
        # Call the decorated function
        result = test_func()
        
        # Should have been called 3 times (2 failures, 1 success)
        assert mock_func.call_count == 3
        assert result == "success"
    
    def test_with_connection_retry_all_failures(self):
        """Test the connection retry decorator with all attempts failing."""
        mock_func = MagicMock()
        error_message = "Persistent error"
        mock_func.side_effect = ConnectionError(error_message)
        
        # Create a decorated function
        @with_connection_retry(max_retries=2, retry_delay=0.01)
        def test_func():
            return mock_func()
        
        # Call the decorated function
        with pytest.raises(StorageConnectionError) as excinfo:
            test_func()
        
        # Should have been called the maximum number of times
        assert mock_func.call_count == 3  # Initial + 2 retries
        assert error_message in str(excinfo.value)
    
    def test_test_storage_connection(self):
        """Test the connection testing function."""
        # Create a mock storage instance
        storage = MockStorage()
        
        # Test a successful connection
        with patch.object(storage, 'test_connection') as mock_test:
            result = test_storage_connection(storage)
            
            assert result["success"] is True
            assert "test_connection" in result["operations_tested"]
            assert mock_test.called
    
    def test_test_storage_connection_failure(self):
        """Test connection testing with a failure."""
        # Create a mock storage instance
        storage = MockStorage()
        
        # Mock a failed connection test
        error_message = "Connection test failed"
        with patch.object(storage, 'test_connection', side_effect=ConnectionError(error_message)):
            with pytest.raises(StorageConnectionError) as excinfo:
                test_storage_connection(storage)
            
            assert error_message in str(excinfo.value)
    
    def test_ensure_storage_healthy(self):
        """Test the ensure_storage_healthy function."""
        # Create a mock storage instance
        storage = MockStorage()
        
        # Mock a successful connection test
        with patch('src.storage.connection.test_storage_connection',
                  return_value={"success": True, "operations_tested": ["test_connection"]}):
            result = ensure_storage_healthy(storage)
            assert result is True
    
    def test_ensure_storage_healthy_with_write_test(self):
        """Test ensure_storage_healthy with a write test."""
        # Create a mock storage instance
        storage = MockStorage()
        
        # Mock a successful connection test without save_session
        with patch('src.storage.connection.test_storage_connection',
                  return_value={"success": True, "operations_tested": ["list_sessions"]}):
            # Should perform a write test
            with patch.object(storage, 'save_session') as mock_save, \
                 patch.object(storage, 'load_session', return_value=[{"role": "system", "content": "Health check message"}]) as mock_load, \
                 patch.object(storage, 'delete_session') as mock_delete:
                
                result = ensure_storage_healthy(storage, perform_write_test=True)
                
                assert result is True
                assert mock_save.called
                assert mock_load.called
                assert mock_delete.called
    
    def test_monitor_connection_health(self):
        """Test the connection health monitoring function."""
        # Create a mock storage instance
        storage = MockStorage()
        
        # Mock threading.Thread to avoid actually starting a thread
        mock_thread = MagicMock()
        
        with patch('threading.Thread', return_value=mock_thread) as mock_thread_class:
            # Call monitor_connection_health with a short interval for testing
            monitor_connection_health(storage, interval=0.1)
            
            # Thread should have been created and started
            assert mock_thread_class.called
            assert mock_thread.start.called

if __name__ == "__main__":
    pytest.main() 