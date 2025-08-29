"""
Domain layer for Oligotools
Contains core business entities, rules, and operations.
"""

from .entities import Project, Folder, FileReference
from .tools import (
    BaseTool, PrimerOverlapTool, ToolResult, ToolParameter,
    ToolInputRequirement, get_available_tools, get_tool_by_id,
    ToolError, ToolParameterError
)
from .exceptions import DomainError, ProjectError, FolderError, FileReferenceError

__all__ = [
    'Project',
    'Folder',
    'FileReference',
    'BaseTool',
    'PrimerOverlapTool',
    'ToolResult',
    'ToolParameter',
    'ToolInputRequirement',
    'get_available_tools',
    'get_tool_by_id',
    'DomainError',
    'ProjectError',
    'FolderError',
    'FileReferenceError',
    'ToolError',
    'ToolParameterError'
]