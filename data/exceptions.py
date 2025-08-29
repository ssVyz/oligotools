"""
Data layer exceptions for Oligotools
Contains all data persistence and file I/O related exceptions.
"""


class DataError(Exception):
    """Base exception for all data layer errors."""
    pass


class ProjectFileError(DataError):
    """Raised when there are issues with project file operations."""
    pass


class FileNotFoundError(DataError):
    """Raised when referenced files cannot be found on disk."""
    pass


class CorruptedProjectError(DataError):
    """Raised when project files are corrupted or invalid."""
    pass


class PathResolutionError(DataError):
    """Raised when file paths cannot be resolved."""
    pass


class JsonSerializationError(DataError):
    """Raised when JSON serialization/deserialization fails."""
    pass


class BackupError(DataError):
    """Raised when project backup operations fail."""
    pass


class PermissionError(DataError):
    """Raised when file system permissions prevent operations."""
    pass