#!/usr/bin/env python3
"""
Session handling utilities for Fama AI.

This module provides utilities for managing agent sessions with various
storage backends, including session creation, resumption, and metadata.
"""
import os
import uuid
import time
import logging
import json
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

from src.storage.factory import AgentStorage, StorageError, StorageConnectionError
from src.storage.connection import with_connection_retry, ensure_storage_healthy
from agno.utils.log import logger

# Set up logging
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager for handling agent session operations.
    
    This class provides utilities for creating, resuming, listing and
    managing agent sessions across different storage backends.
    """
    
    def __init__(self, storage: AgentStorage):
        """
        Initialize the session manager with a storage backend.
        
        Args:
            storage: An initialized AgentStorage instance
            
        Raises:
            StorageError: If the storage is not properly initialized
        """
        self.storage = storage
        self.storage_type = type(storage).__name__
        
        # Validate that the storage is healthy and connected
        try:
            ensure_storage_healthy(storage)
            logger.info(f"Session manager initialized with {self.storage_type}")
        except StorageConnectionError as e:
            logger.error(f"Failed to initialize session manager: {str(e)}")
            raise StorageError(f"Storage validation failed during session manager initialization: {str(e)}")
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a unique session ID.
        
        Returns:
            A unique session ID string
        """
        # Generate a UUID4-based session ID with timestamp prefix for sortability
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:12]
        return f"{timestamp}_{unique_id}"
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session with optional metadata.
        
        Args:
            user_id: User identifier for the session
            metadata: Optional metadata to associate with the session
            
        Returns:
            The newly created session ID
            
        Raises:
            StorageError: If the session cannot be created
        """
        session_id = self.generate_session_id()
        
        # Initialize empty message list - following Agno's pattern
        messages = []
        
        # If metadata is provided, add it as system messages with metadata marker
        if metadata:
            # Convert any non-serializable values to strings
            serialized_metadata = self._sanitize_metadata(metadata)
            
            # Add metadata as a system message with special marker
            messages.append({
                "role": "system",
                "content": "Session initialized with metadata",
                "metadata": serialized_metadata,
                "timestamp": datetime.now().isoformat()
            })
        
        try:
            # Save the initial session state
            self.storage.save_session(session_id, user_id, messages)
            logger.info(f"Created new session {session_id} for user {user_id}")
            return session_id
        except Exception as e:
            error_msg = f"Failed to create session: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def resume_session(self, session_id: str, validate_exists: bool = True) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Resume an existing session.
        
        Args:
            session_id: The session ID to resume
            validate_exists: Whether to validate that the session exists
            
        Returns:
            Tuple of (user_id, messages) if session exists, (None, []) otherwise
            
        Raises:
            StorageError: If validate_exists is True and the session doesn't exist
        """
        try:
            # Check if session exists if validation is required
            if validate_exists:
                if not self._session_exists(session_id):
                    raise StorageError(f"Session {session_id} not found")
            
            # Load the session messages
            messages = self.storage.load_session(session_id)
            
            # Extract user_id - use appropriate method based on storage type
            if hasattr(self.storage, 'get_user_id'):
                # If the storage has a specific method for user ID
                user_id = self.storage.get_user_id(session_id)
            else:
                # Extract from session metadata (fallback approach)
                user_id = self._extract_user_id_from_messages(session_id, messages)
            
            logger.info(f"Resumed session {session_id} for user {user_id}")
            return user_id, messages
        except Exception as e:
            error_msg = f"Failed to resume session {session_id}: {str(e)}"
            logger.error(error_msg)
            
            if validate_exists:
                raise StorageError(error_msg)
            return None, []
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """
        List available sessions, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID to filter sessions
            
        Returns:
            List of session IDs
            
        Raises:
            StorageError: If sessions cannot be listed
        """
        try:
            if hasattr(self.storage, 'list_sessions'):
                # If storage provides a list_sessions method
                sessions = self.storage.list_sessions(user_id=user_id)
                logger.info(f"Listed {len(sessions)} sessions" + 
                           (f" for user {user_id}" if user_id else ""))
                return sessions
            else:
                # Fallback implementation if not supported
                logger.warning(f"Storage type {self.storage_type} doesn't support listing sessions")
                return []
        except Exception as e:
            error_msg = f"Failed to list sessions: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific session.
        
        Args:
            session_id: The session ID to get metadata for
            
        Returns:
            Dictionary containing session metadata
            
        Raises:
            StorageError: If the metadata cannot be retrieved
        """
        try:
            # First check if the session exists
            if not self._session_exists(session_id):
                raise StorageError(f"Session {session_id} not found")
            
            # Load the session messages
            messages = self.storage.load_session(session_id)
            
            # Extract metadata from system messages
            metadata = {}
            
            # Extract creation timestamp from session ID (if format matches)
            if "_" in session_id:
                try:
                    timestamp_str = session_id.split("_")[0]
                    timestamp = int(timestamp_str)
                    metadata["created_at"] = datetime.fromtimestamp(timestamp).isoformat()
                except (ValueError, IndexError):
                    # Invalid format, skip
                    pass
            
            # Look for metadata in system messages
            for msg in messages:
                if msg.get("role") == "system" and "metadata" in msg:
                    # Update metadata with contents from this message
                    metadata.update(msg.get("metadata", {}))
            
            # Add basic session info
            metadata["session_id"] = session_id
            metadata["message_count"] = len(messages)
            
            # Get user ID if available
            try:
                if hasattr(self.storage, 'get_user_id'):
                    metadata["user_id"] = self.storage.get_user_id(session_id)
                else:
                    metadata["user_id"] = self._extract_user_id_from_messages(session_id, messages)
            except Exception:
                # User ID not available
                pass
            
            # Get last updated timestamp if available
            try:
                if hasattr(self.storage, 'get_last_updated'):
                    metadata["last_updated"] = self.storage.get_last_updated(session_id)
                else:
                    # Try to find the timestamp in the most recent message
                    for msg in reversed(messages):
                        if "timestamp" in msg:
                            metadata["last_updated"] = msg["timestamp"]
                            break
            except Exception:
                # Last updated not available
                pass
            
            logger.info(f"Retrieved metadata for session {session_id}")
            return metadata
        except Exception as e:
            error_msg = f"Failed to get metadata for session {session_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a specific session.
        
        Args:
            session_id: The session ID to update metadata for
            metadata: Dictionary containing metadata to update
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If the metadata cannot be updated
        """
        try:
            # First check if the session exists
            if not self._session_exists(session_id):
                raise StorageError(f"Session {session_id} not found")
            
            # Load the session messages
            messages = self.storage.load_session(session_id)
            
            # Sanitize metadata (convert non-serializable values to strings)
            serialized_metadata = self._sanitize_metadata(metadata)
            
            # Add a new system message with updated metadata
            metadata_message = {
                "role": "system",
                "content": "Session metadata updated",
                "metadata": serialized_metadata,
                "timestamp": datetime.now().isoformat()
            }
            
            # Insert at the beginning for quick access
            messages.insert(0, metadata_message)
            
            # Save the updated messages
            if hasattr(self.storage, 'get_user_id'):
                user_id = self.storage.get_user_id(session_id)
            else:
                user_id = self._extract_user_id_from_messages(session_id, messages)
                
            self.storage.save_session(session_id, user_id, messages)
            logger.info(f"Updated metadata for session {session_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to update metadata for session {session_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
    
    @with_connection_retry(max_retries=2, retry_delay=0.5)
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If the session cannot be deleted
        """
        try:
            # Attempt to delete the session
            self.storage.delete_session(session_id)
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to delete session {session_id}: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
    
    def _session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: The session ID to check
            
        Returns:
            True if the session exists, False otherwise
        """
        try:
            # Try to load the session
            messages = self.storage.load_session(session_id)
            # If no exception and we got messages (even empty list), session exists
            return messages is not None
        except Exception:
            # Any exception means the session doesn't exist or is inaccessible
            return False
    
    def _extract_user_id_from_messages(self, session_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        Extract user ID from messages for storage backends that don't store it separately.
        
        Args:
            session_id: The session ID
            messages: The session messages
            
        Returns:
            The extracted user ID or a fallback value
        
        Note:
            This is a fallback method for storage backends that don't store user ID separately.
            It looks for user ID in metadata or uses a fallback based on session ID.
        """
        # First, try to find user ID in metadata
        for msg in messages:
            if msg.get("role") == "system" and "metadata" in msg:
                if "user_id" in msg["metadata"]:
                    return msg["metadata"]["user_id"]
        
        # If not found, use a fallback based on session ID
        return f"user_{session_id.split('_')[0]}"
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata to ensure it's serializable.
        
        Args:
            metadata: The metadata dictionary to sanitize
            
        Returns:
            A sanitized copy of the metadata
        """
        result = {}
        for key, value in metadata.items():
            # Convert non-serializable values to strings
            try:
                # Test if JSON serializable
                json.dumps({key: value})
                result[key] = value
            except (TypeError, OverflowError):
                # Convert to string if not serializable
                result[key] = str(value)
        return result


def create_session_manager(storage: AgentStorage) -> SessionManager:
    """
    Create and initialize a session manager.
    
    Args:
        storage: An initialized storage instance
        
    Returns:
        An initialized SessionManager
        
    Raises:
        StorageError: If the session manager cannot be initialized
    """
    try:
        return SessionManager(storage)
    except Exception as e:
        error_msg = f"Failed to create session manager: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg) 