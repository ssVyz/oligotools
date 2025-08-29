"""
Domain exceptions for Oligotools
Contains all business logic related exceptions.
"""


class DomainError(Exception):
    """Base exception for all domain-related errors."""
    pass


class ProjectError(DomainError):
    """Raised when there are issues with project operations."""
    pass

'''
class ToolError(DomainError):
    """Raised when there are issues with tool operations."""
    pass

class ToolParameterError(DomainError):
    """Raised when there are issues with tool operations."""
    pass
'''

class FolderError(DomainError):
    """Raised when there are issues with folder operations."""
    pass


class FileReferenceError(DomainError):
    """Raised when there are issues with file reference operations."""
    pass


class DuplicateNameError(DomainError):
    """Raised when attempting to create items with duplicate names in the same folder."""
    pass


class ItemNotFoundError(DomainError):
    """Raised when attempting to access a non-existent item."""
    pass


class InvalidPathError(DomainError):
    """Raised when provided paths are invalid or malformed."""
    pass