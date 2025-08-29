"""
Use cases module for Oligotools Application Layer
Contains all the specific use case implementations.
"""

# Project lifecycle use cases
from .project_use_cases import (
    CreateNewProjectUseCase, CreateProjectRequest,
    LoadProjectUseCase, LoadProjectRequest,
    SaveProjectUseCase, SaveProjectRequest,
    ValidateProjectUseCase, ValidateProjectRequest,
)

# File and folder operations (import/move/copy/delete/create-folder)
from .file_use_cases import (
    ImportFileUseCase, ImportFileRequest,
    CreateFolderUseCase, CreateFolderRequest,
    MoveItemUseCase, MoveItemRequest,
    CopyFileUseCase, CopyFileRequest,
    DeleteItemUseCase, DeleteItemRequest,
)

# Enhanced file management within a project (remove/rename/move/categorize/list-by-category)
from .file_management_use_cases import (
    RemoveFileFromProjectUseCase, RemoveFileFromProjectRequest,
    RenameFileInProjectUseCase, RenameFileInProjectRequest,
    MoveFileInProjectUseCase, MoveFileInProjectRequest,
    SetFileCategoryUseCase, SetFileCategoryRequest,
    GetFilesByCategoryUseCase, GetFilesByCategoryRequest,
)

# Tool execution & discovery
from .tool_use_cases import (
    RunToolUseCase, RunToolRequest,
    GetAvailableToolsUseCase, GetAvailableToolsRequest,
    GetProjectFastaFilesUseCase, GetProjectFastaFilesRequest,
)

__all__ = [
    # project
    'CreateNewProjectUseCase', 'CreateProjectRequest',
    'LoadProjectUseCase', 'LoadProjectRequest',
    'SaveProjectUseCase', 'SaveProjectRequest',
    'ValidateProjectUseCase', 'ValidateProjectRequest',

    # file_use_cases
    'ImportFileUseCase', 'ImportFileRequest',
    'CreateFolderUseCase', 'CreateFolderRequest',
    'MoveItemUseCase', 'MoveItemRequest',
    'CopyFileUseCase', 'CopyFileRequest',
    'DeleteItemUseCase', 'DeleteItemRequest',

    # file_management_use_cases
    'RemoveFileFromProjectUseCase', 'RemoveFileFromProjectRequest',
    'RenameFileInProjectUseCase', 'RenameFileInProjectRequest',
    'MoveFileInProjectUseCase', 'MoveFileInProjectRequest',
    'SetFileCategoryUseCase', 'SetFileCategoryRequest',
    'GetFilesByCategoryUseCase', 'GetFilesByCategoryRequest',

    # tool_use_cases
    'RunToolUseCase', 'RunToolRequest',
    'GetAvailableToolsUseCase', 'GetAvailableToolsRequest',
    'GetProjectFastaFilesUseCase', 'GetProjectFastaFilesRequest',
]
