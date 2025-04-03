#!/usr/bin/env python3
"""
Streaming log API for Fama AI.

This module implements the streaming log API for real-time logging.
"""
import json
import logging
import time
from typing import Dict, List, Any, Optional, Generator

# Set up logging
logger = logging.getLogger(__name__)

class LogStream:
    """
    A class to handle streaming logs for real-time updates.
    
    This provides a way to stream logs to the caller's host endpoint.
    """
    
    def __init__(self, request_id: str, caller_endpoint: Optional[str] = None):
        """
        Initialize a log stream for a specific request.
        
        Args:
            request_id: Unique identifier for the request
            caller_endpoint: Optional endpoint to forward logs to
        """
        self.request_id = request_id
        self.caller_endpoint = caller_endpoint
        self.logs: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
        logger.info(f"Log stream initialized for request {request_id}")
        
    def add_log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a log entry to the stream.
        
        Args:
            level: Log level (e.g., 'info', 'warning', 'error')
            message: Log message
            data: Optional additional data for the log
        """
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "request_id": self.request_id,
            "elapsed": timestamp - self.start_time
        }
        
        if data:
            log_entry["data"] = data
        
        self.logs.append(log_entry)
        
        # Log locally as well
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"[{self.request_id}] {message}")
        
        # Forward to caller endpoint if specified
        if self.caller_endpoint:
            self._forward_log(log_entry)
    
    def _forward_log(self, log_entry: Dict[str, Any]) -> None:
        """
        Forward a log entry to the caller's endpoint.
        
        In production, this would use an HTTP client to send the log.
        For development, this is a placeholder.
        
        Args:
            log_entry: The log entry to forward
        """
        # In production, this would use HTTP to send logs to the caller's endpoint
        # For development, we just log that we would send it
        logger.debug(f"Would forward log to {self.caller_endpoint}: {json.dumps(log_entry)}")
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Get all logs in the stream.
        
        Returns:
            List of log entries
        """
        return self.logs
    
    def stream_logs(self) -> Generator[str, None, None]:
        """
        Stream logs as a generator of JSON strings.
        
        This is used for the streaming log API endpoint.
        
        Yields:
            JSON string of each log entry
        """
        # First yield all existing logs
        for log in self.logs:
            yield json.dumps(log) + "\n"
        
        # Store the current log count
        current_count = len(self.logs)
        
        # Then yield new logs as they come in
        while True:
            # Check if new logs have been added
            if len(self.logs) > current_count:
                # Yield all new logs
                for i in range(current_count, len(self.logs)):
                    yield json.dumps(self.logs[i]) + "\n"
                
                # Update the current count
                current_count = len(self.logs)
            
            # Sleep to avoid busy waiting
            time.sleep(0.1)

# Global dictionary to store active log streams
log_streams: Dict[str, LogStream] = {}

def get_log_stream(request_id: str) -> Optional[LogStream]:
    """
    Get a log stream by request ID.
    
    Args:
        request_id: The request ID to look up
        
    Returns:
        The LogStream instance if found, None otherwise
    """
    return log_streams.get(request_id)

def create_log_stream(request_id: str, caller_endpoint: Optional[str] = None) -> LogStream:
    """
    Create a new log stream.
    
    Args:
        request_id: Unique identifier for the request
        caller_endpoint: Optional endpoint to forward logs to
        
    Returns:
        The newly created LogStream instance
    """
    stream = LogStream(request_id, caller_endpoint)
    log_streams[request_id] = stream
    return stream

def remove_log_stream(request_id: str) -> None:
    """
    Remove a log stream.
    
    Args:
        request_id: The request ID to remove
    """
    if request_id in log_streams:
        del log_streams[request_id]
        logger.info(f"Log stream removed for request {request_id}") 