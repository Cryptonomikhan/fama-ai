#!/usr/bin/env python3
"""
Session management API endpoints for Fama AI.

This module provides REST API endpoints for managing sessions with various
storage backends, following the Agno pattern for session management.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.storage.factory import initialize_storage, StorageError
from src.storage.session import create_session_manager, SessionManager

# Set up logging
logger = logging.getLogger(__name__)

# Create router for session endpoints
session_router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionCreationRequest(BaseModel):
    """Request model for creating a new session"""
    
    user_id: str = Field(..., description="User identifier for the session")
    storage_type: str = Field(..., description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: str = Field(..., description="Connection string for storage backend")
    table_name: str = Field("agent_sessions", description="Table or collection name for storing sessions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata to associate with the session")


class SessionResponse(BaseModel):
    """Response model for session operations"""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier for the session")
    created_at: str = Field(..., description="ISO-format timestamp when the session was created")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class SessionResumeRequest(BaseModel):
    """Request model for resuming an existing session"""
    
    session_id: str = Field(..., description="Session ID to resume")
    storage_type: str = Field(..., description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: str = Field(..., description="Connection string for storage backend")
    table_name: str = Field("agent_sessions", description="Table or collection name for storing sessions")
    validate_exists: bool = Field(True, description="Whether to validate that the session exists")


class SessionMessagesResponse(BaseModel):
    """Response model for session with messages"""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier for the session")
    created_at: str = Field(..., description="ISO-format timestamp when the session was created")
    messages: List[Dict[str, Any]] = Field(..., description="Session messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class SessionMetadataRequest(BaseModel):
    """Request model for getting or updating session metadata"""
    
    session_id: str = Field(..., description="Session ID to get or update metadata for")
    storage_type: str = Field(..., description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: str = Field(..., description="Connection string for storage backend")
    table_name: str = Field("agent_sessions", description="Table or collection name for storing sessions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata to update (if updating)")


class SessionMetadataResponse(BaseModel):
    """Response model for session metadata operations"""
    
    session_id: str = Field(..., description="Unique session identifier")
    metadata: Dict[str, Any] = Field(..., description="Session metadata")
    user_id: Optional[str] = Field(None, description="User identifier for the session")
    created_at: Optional[str] = Field(None, description="ISO-format timestamp when the session was created")
    last_updated: Optional[str] = Field(None, description="ISO-format timestamp when the session was last updated")
    message_count: Optional[int] = Field(None, description="Number of messages in the session")


class SessionDeleteRequest(BaseModel):
    """Request model for deleting a session"""
    
    session_id: str = Field(..., description="Session ID to delete")
    storage_type: str = Field(..., description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: str = Field(..., description="Connection string for storage backend")
    table_name: str = Field("agent_sessions", description="Table or collection name for storing sessions")


class SessionCleanupRequest(BaseModel):
    """Request model for cleaning up sessions"""
    
    storage_type: str = Field(..., description="Storage type (sqlite, postgres, mongodb, dynamodb, json, yaml)")
    storage_connection: str = Field(..., description="Connection string for storage backend")
    table_name: str = Field("agent_sessions", description="Table or collection name for storing sessions")
    user_id: Optional[str] = Field(None, description="User ID to filter sessions (if None, cleans up all users)")
    max_age_days: Optional[int] = Field(30, description="Maximum age of sessions to keep in days (default: 30)")
    keep_latest_per_user: Optional[int] = Field(5, description="Number of latest sessions to keep per user (default: 5)")


class SessionCleanupResponse(BaseModel):
    """Response model for session cleanup operations"""
    
    deleted_count: int = Field(..., description="Number of sessions deleted")
    remaining_count: int = Field(..., description="Number of sessions remaining")
    deleted_sessions: Optional[List[str]] = Field(None, description="List of deleted session IDs")


@session_router.post("/create", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreationRequest) -> SessionResponse:
    """
    Create a new session with the specified storage backend.
    
    This endpoint initializes a storage backend and creates a new session,
    returning the session ID and metadata.
    
    Args:
        request: The session creation request with user ID, storage settings, and optional metadata
        
    Returns:
        SessionResponse with the created session details
        
    Raises:
        HTTPException: If the session cannot be created due to storage errors
    """
    try:
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=request.storage_type,
            storage_connection=request.storage_connection,
            table_name=request.table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Create a new session with the provided user ID and metadata
        session_id = session_manager.create_session(
            user_id=request.user_id,
            metadata=request.metadata
        )
        
        # Get session metadata to return in the response
        metadata = session_manager.get_session_metadata(session_id)
        
        # Return the session details
        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            created_at=metadata.get("created_at", ""),
            metadata=metadata
        )
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@session_router.post("/resume", response_model=SessionMessagesResponse, status_code=status.HTTP_200_OK)
async def resume_session(request: SessionResumeRequest) -> SessionMessagesResponse:
    """
    Resume an existing session with the specified storage backend.
    
    This endpoint initializes a storage backend and loads an existing session,
    returning the session details and messages.
    
    Args:
        request: The session resume request with session ID and storage settings
        
    Returns:
        SessionMessagesResponse with the session details and messages
        
    Raises:
        HTTPException: If the session cannot be resumed due to storage errors or if it doesn't exist
    """
    try:
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=request.storage_type,
            storage_connection=request.storage_connection,
            table_name=request.table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Resume the session with the provided session ID
        user_id, messages = session_manager.resume_session(
            session_id=request.session_id,
            validate_exists=request.validate_exists
        )
        
        # If session doesn't exist and validate_exists is False, return 404
        if user_id is None and request.validate_exists is False:
            logger.warning(f"Session {request.session_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        # Get session metadata
        metadata = session_manager.get_session_metadata(request.session_id)
        
        # Return the session details and messages
        return SessionMessagesResponse(
            session_id=request.session_id,
            user_id=user_id,
            created_at=metadata.get("created_at", ""),
            messages=messages,
            metadata=metadata
        )
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        error_msg = f"Failed to resume session: {str(e)}"
        logger.error(error_msg)
        
        # If the error is that the session doesn't exist, return 404
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Otherwise, return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error resuming session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@session_router.get("/metadata/{session_id}", response_model=SessionMetadataResponse, status_code=status.HTTP_200_OK)
async def get_session_metadata(
    session_id: str,
    storage_type: str,
    storage_connection: str,
    table_name: str = "agent_sessions"
) -> SessionMetadataResponse:
    """
    Get metadata for an existing session.
    
    This endpoint initializes a storage backend and retrieves the metadata for
    an existing session, returning the session details without messages.
    
    Args:
        session_id: The session ID to get metadata for
        storage_type: The storage type (sqlite, postgres, mongodb, etc.)
        storage_connection: Connection string for the storage backend
        table_name: Table or collection name for storing sessions
        
    Returns:
        SessionMetadataResponse with the session metadata
        
    Raises:
        HTTPException: If the session metadata cannot be retrieved
    """
    try:
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=storage_type,
            storage_connection=storage_connection,
            table_name=table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Get session metadata
        metadata = session_manager.get_session_metadata(session_id)
        
        # Return the session metadata
        return SessionMetadataResponse(
            session_id=session_id,
            metadata=metadata,
            user_id=metadata.get("user_id"),
            created_at=metadata.get("created_at"),
            last_updated=metadata.get("last_updated"),
            message_count=metadata.get("message_count")
        )
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        error_msg = f"Failed to get session metadata: {str(e)}"
        logger.error(error_msg)
        
        # If the error is that the session doesn't exist, return 404
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Otherwise, return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error getting session metadata: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@session_router.put("/metadata", response_model=SessionMetadataResponse, status_code=status.HTTP_200_OK)
async def update_session_metadata(request: SessionMetadataRequest) -> SessionMetadataResponse:
    """
    Update metadata for an existing session.
    
    This endpoint initializes a storage backend and updates the metadata for
    an existing session, returning the updated session metadata.
    
    Args:
        request: The session metadata request with session ID, storage settings, and metadata
        
    Returns:
        SessionMetadataResponse with the updated session metadata
        
    Raises:
        HTTPException: If the session metadata cannot be updated
    """
    try:
        # Ensure metadata is provided
        if not request.metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Metadata is required for update operation"
            )
        
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=request.storage_type,
            storage_connection=request.storage_connection,
            table_name=request.table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Update session metadata
        success = session_manager.update_session_metadata(
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        if not success:
            raise StorageError(f"Failed to update metadata for session {request.session_id}")
        
        # Get updated session metadata
        updated_metadata = session_manager.get_session_metadata(request.session_id)
        
        # Return the updated session metadata
        return SessionMetadataResponse(
            session_id=request.session_id,
            metadata=updated_metadata,
            user_id=updated_metadata.get("user_id"),
            created_at=updated_metadata.get("created_at"),
            last_updated=updated_metadata.get("last_updated"),
            message_count=updated_metadata.get("message_count")
        )
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        error_msg = f"Failed to update session metadata: {str(e)}"
        logger.error(error_msg)
        
        # If the error is that the session doesn't exist, return 404
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Otherwise, return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error updating session metadata: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@session_router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    storage_type: str,
    storage_connection: str,
    table_name: str = "agent_sessions"
):
    """
    Delete a specific session.
    
    This endpoint initializes a storage backend and deletes a specific session.
    
    Args:
        session_id: The session ID to delete
        storage_type: The storage type (sqlite, postgres, mongodb, etc.)
        storage_connection: Connection string for the storage backend
        table_name: Table or collection name for storing sessions
        
    Returns:
        204 No Content on success
        
    Raises:
        HTTPException: If the session cannot be deleted
    """
    try:
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=storage_type,
            storage_connection=storage_connection,
            table_name=table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Delete the session
        success = session_manager.delete_session(session_id)
        
        if not success:
            # If we couldn't delete the session, it might not exist
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found or could not be deleted"
            )
        
        logger.info(f"Session {session_id} deleted successfully")
        # Return 204 No Content on success (no body)
        return
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        error_msg = f"Failed to delete session: {str(e)}"
        logger.error(error_msg)
        
        # If the error is that the session doesn't exist, return 404
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Otherwise, return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error deleting session: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@session_router.post("/cleanup", response_model=SessionCleanupResponse, status_code=status.HTTP_200_OK)
async def cleanup_sessions(request: SessionCleanupRequest) -> SessionCleanupResponse:
    """
    Clean up sessions based on age and retention policy.
    
    This endpoint initializes a storage backend and cleans up sessions that are older
    than the specified age, while keeping a specified number of latest sessions per user.
    
    Args:
        request: The session cleanup request with storage settings and cleanup parameters
        
    Returns:
        SessionCleanupResponse with counts of deleted and remaining sessions
        
    Raises:
        HTTPException: If the sessions cannot be cleaned up
    """
    try:
        # Initialize storage with the provided parameters
        storage = initialize_storage(
            storage_type=request.storage_type,
            storage_connection=request.storage_connection,
            table_name=request.table_name
        )
        
        # Create session manager with the initialized storage
        session_manager = create_session_manager(storage)
        
        # Get all sessions, filtered by user ID if provided
        all_sessions = session_manager.list_sessions(user_id=request.user_id)
        
        # If no sessions found, return early
        if not all_sessions:
            return SessionCleanupResponse(
                deleted_count=0,
                remaining_count=0,
                deleted_sessions=[]
            )
        
        # Group sessions by user ID
        sessions_by_user = {}
        for session_id in all_sessions:
            try:
                # Get metadata to determine user ID and creation time
                metadata = session_manager.get_session_metadata(session_id)
                user_id = metadata.get("user_id", "unknown")
                
                # Parse created_at timestamp - if not available, treat as old
                created_at = None
                if "created_at" in metadata:
                    try:
                        created_at = datetime.fromisoformat(metadata["created_at"])
                    except (ValueError, TypeError):
                        # If we can't parse the timestamp, use a default old date
                        created_at = datetime.now() - timedelta(days=request.max_age_days * 2)
                else:
                    # If created_at is not available, try to parse from session_id
                    if "_" in session_id:
                        try:
                            timestamp_str = session_id.split("_")[0]
                            timestamp = int(timestamp_str)
                            created_at = datetime.fromtimestamp(timestamp)
                        except (ValueError, IndexError):
                            # Default to old date if parsing fails
                            created_at = datetime.now() - timedelta(days=request.max_age_days * 2)
                            
                # Fall back to a very old date if still None
                if created_at is None:
                    created_at = datetime.now() - timedelta(days=request.max_age_days * 2)
                
                # Add to sessions_by_user
                if user_id not in sessions_by_user:
                    sessions_by_user[user_id] = []
                
                sessions_by_user[user_id].append((session_id, created_at))
                
            except StorageError:
                # Skip sessions with errors
                logger.warning(f"Skipping session {session_id} due to metadata retrieval error")
                continue
        
        # Determine which sessions to delete
        sessions_to_delete = []
        cutoff_date = datetime.now() - timedelta(days=request.max_age_days)
        
        for user_id, sessions in sessions_by_user.items():
            # Sort sessions by creation time (newest first)
            sorted_sessions = sorted(sessions, key=lambda x: x[1], reverse=True)
            
            # Keep the latest N sessions per user, delete the rest
            # Also delete old sessions based on max_age_days
            for i, (session_id, created_at) in enumerate(sorted_sessions):
                if i >= request.keep_latest_per_user or created_at < cutoff_date:
                    sessions_to_delete.append(session_id)
        
        # Delete the selected sessions
        deleted_sessions = []
        for session_id in sessions_to_delete:
            try:
                success = session_manager.delete_session(session_id)
                if success:
                    deleted_sessions.append(session_id)
                    logger.info(f"Deleted session {session_id} during cleanup")
            except Exception as e:
                logger.warning(f"Failed to delete session {session_id} during cleanup: {str(e)}")
        
        # Count remaining sessions
        remaining_count = len(all_sessions) - len(deleted_sessions)
        
        # Return the cleanup results
        return SessionCleanupResponse(
            deleted_count=len(deleted_sessions),
            remaining_count=remaining_count,
            deleted_sessions=deleted_sessions
        )
    
    except StorageError as e:
        # Log the error and raise an HTTP exception
        error_msg = f"Failed to clean up sessions: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        # Log unexpected errors
        error_msg = f"Unexpected error cleaning up sessions: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        ) 