"""
Storage-related error classes.
"""

class StorageError(Exception):
    """Base class for storage-related errors."""
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details 