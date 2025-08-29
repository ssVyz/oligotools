"""
Data layer for Oligotools
Handles persistence, file I/O, and data access operations.
"""

from .project_repository import ProjectRepository
from .file_manager import FileManager
from .format_detector import FormatDetector
from .exceptions import (
    DataError,
    ProjectFileError,
    FileNotFoundError,
    CorruptedProjectError,
    PathResolutionError
)

__all__ = [
    'ProjectRepository',
    'FileManager',
    'FormatDetector',
    'DataError',
    'ProjectFileError',
    'FileNotFoundError',
    'CorruptedProjectError',
    'PathResolutionError'
]