"""
Application Service for Oligotools
Main coordinator that provides a unified interface to all use cases.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from domain.entities import Project
from data import ProjectRepository
from .base_use_case import UseCaseResult
from .use_cases import (
    CreateNewProjectUseCase, CreateProjectRequest,
    LoadProjectUseCase, LoadProjectRequest,
    SaveProjectUseCase, SaveProjectRequest,
    ValidateProjectUseCase, ValidateProjectRequest,
    ImportFileUseCase, ImportFileRequest,
    CreateFolderUseCase, CreateFolderRequest,
    MoveItemUseCase, MoveItemRequest,
    CopyFileUseCase, CopyFileRequest,
    DeleteItemUseCase, DeleteItemRequest,
    RunToolUseCase, RunToolRequest,
    GetAvailableToolsUseCase, GetAvailableToolsRequest,
    GetProjectFastaFilesUseCase, GetProjectFastaFilesRequest
)
from .exceptions import ApplicationError, InvalidOperationError


class ApplicationService:
    """
    Main application service that coordinates all use cases.

    This is the primary interface between the UI layer and the business logic.
    It maintains application state and provides a unified API.
    """

    def __init__(self):
        """Initialize the application service."""
        self.project_repository = ProjectRepository()
        self.current_project: Optional[Project] = None
        self.project_modified: bool = False

        # Initialize use cases
        self._create_project_use_case = CreateNewProjectUseCase(self.project_repository)
        self._load_project_use_case = LoadProjectUseCase(self.project_repository)
        self._save_project_use_case = SaveProjectUseCase(self.project_repository)
        self._validate_project_use_case = ValidateProjectUseCase(self.project_repository)
        self._import_file_use_case = ImportFileUseCase(self.project_repository)
        self._create_folder_use_case = CreateFolderUseCase(self.project_repository)
        self._move_item_use_case = MoveItemUseCase(self.project_repository)
        self._copy_file_use_case = CopyFileUseCase(self.project_repository)
        self._delete_item_use_case = DeleteItemUseCase(self.project_repository)

        # Tool use cases
        self._run_tool_use_case = RunToolUseCase(self.project_repository)
        self._get_available_tools_use_case = GetAvailableToolsUseCase(self.project_repository)
        self._get_project_fasta_files_use_case = GetProjectFastaFilesUseCase(self.project_repository)

    # Project Management Operations

    def create_new_project(self, project_name: str, project_file_path: str, description: str = "") -> UseCaseResult:
        """
        Create a new project.

        Args:
            project_name: Name for the new project
            project_file_path: Where to save the project file
            description: Optional project description

        Returns:
            UseCaseResult with project creation results
        """
        request = CreateProjectRequest(
            project_name=project_name,
            project_file_path=project_file_path,
            description=description
        )

        result = self._create_project_use_case.execute_safely(request)

        if result.success:
            self.current_project = result.data.project
            self.project_modified = False

        return result

    # Tool Operations

    def get_available_tools(self) -> UseCaseResult:
        """
        Get list of available analysis tools.

        Returns:
            UseCaseResult with available tools information
        """
        request = GetAvailableToolsRequest(project=self.current_project)
        return self._get_available_tools_use_case.execute_safely(request)

    def get_project_fasta_files(self, selected_files: Optional[List[str]] = None) -> UseCaseResult:
        """
        Get FASTA files from the current project.

        Args:
            selected_files: Optional list of pre-selected file names

        Returns:
            UseCaseResult with FASTA files from the project
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = GetProjectFastaFilesRequest(
            project=self.current_project,
            selected_files=selected_files
        )

        return self._get_project_fasta_files_use_case.execute_safely(request)

    def run_tool(self, tool_id: str, input_files: List[str],
                 parameters: Dict[str, Any], output_to_project: bool = True) -> UseCaseResult:
        """
        Run an analysis tool on selected files.

        Args:
            tool_id: ID of the tool to run
            input_files: List of file names/IDs to analyze
            parameters: Dictionary of tool parameters
            output_to_project: Whether to import results back to project

        Returns:
            UseCaseResult with tool execution results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        # Find file references by name
        all_files = self.current_project.get_all_file_references()
        file_refs = []

        for file_name in input_files:
            matching_files = [f for f in all_files if f.name == file_name]
            if matching_files:
                file_refs.append(matching_files[0])  # Take first match
            else:
                return UseCaseResult(
                    success=False,
                    error=f"File '{file_name}' not found in project"
                )

        request = RunToolRequest(
            project=self.current_project,
            tool_id=tool_id,
            input_files=file_refs,
            parameters=parameters,
            output_to_project=output_to_project
        )

        result = self._run_tool_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    def load_project(self, project_file_path: str) -> UseCaseResult:
        """
        Load an existing project.

        Args:
            project_file_path: Path to the project file

        Returns:
            UseCaseResult with project loading results
        """
        # Check if current project needs saving
        if self.has_unsaved_changes():
            return UseCaseResult(
                success=False,
                error="Current project has unsaved changes. Save or discard changes before loading a new project."
            )

        request = LoadProjectRequest(project_file_path=project_file_path)
        result = self._load_project_use_case.execute_safely(request)

        if result.success:
            self.current_project = result.data.project
            self.project_modified = False

        return result

    def save_current_project(self, create_backup: bool = True) -> UseCaseResult:
        """
        Save the current project.

        Args:
            create_backup: Whether to create a backup before saving

        Returns:
            UseCaseResult with save results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = SaveProjectRequest(
            project=self.current_project,
            create_backup=create_backup
        )

        result = self._save_project_use_case.execute_safely(request)

        if result.success:
            self.project_modified = False

        return result

    def validate_current_project(self) -> UseCaseResult:
        """
        Validate the current project.

        Returns:
            UseCaseResult with validation results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = ValidateProjectRequest(project=self.current_project)
        return self._validate_project_use_case.execute_safely(request)

    def close_project(self, force: bool = False) -> UseCaseResult:
        """
        Close the current project.

        Args:
            force: If True, close without checking for unsaved changes

        Returns:
            UseCaseResult indicating success or failure
        """
        if not self.current_project:
            return UseCaseResult(
                success=True,
                data="No project was open"
            )

        if not force and self.has_unsaved_changes():
            return UseCaseResult(
                success=False,
                error="Project has unsaved changes. Save changes or use force=True to discard them."
            )

        project_name = self.current_project.name
        self.current_project = None
        self.project_modified = False
        self.project_repository.close_project()

        return UseCaseResult(
            success=True,
            data=f"Project '{project_name}' closed successfully"
        )

    # File and Folder Operations

    def import_file(self, source_file_path: str, target_folder_path: str,
                   copy_file: bool = True, auto_detect_format: bool = True) -> UseCaseResult:
        """
        Import a file into the current project.

        Args:
            source_file_path: Path to the source file
            target_folder_path: Target folder in the project
            copy_file: Whether to copy the file or just reference it
            auto_detect_format: Whether to auto-detect the file format

        Returns:
            UseCaseResult with import results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = ImportFileRequest(
            project=self.current_project,
            source_file_path=source_file_path,
            target_folder_path=target_folder_path,
            copy_file=copy_file,
            auto_detect_format=auto_detect_format
        )

        result = self._import_file_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    def create_folder(self, parent_folder_path: str, folder_name: str) -> UseCaseResult:
        """
        Create a new folder in the current project.

        Args:
            parent_folder_path: Path to the parent folder
            folder_name: Name for the new folder

        Returns:
            UseCaseResult with folder creation results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = CreateFolderRequest(
            project=self.current_project,
            parent_folder_path=parent_folder_path,
            folder_name=folder_name
        )

        result = self._create_folder_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    def move_item(self, source_folder_path: str, item_name: str, destination_folder_path: str) -> UseCaseResult:
        """
        Move an item within the current project.

        Args:
            source_folder_path: Source folder path
            item_name: Name of the item to move
            destination_folder_path: Destination folder path

        Returns:
            UseCaseResult with move results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = MoveItemRequest(
            project=self.current_project,
            source_folder_path=source_folder_path,
            item_name=item_name,
            destination_folder_path=destination_folder_path
        )

        result = self._move_item_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    def copy_file(self, source_folder_path: str, file_name: str,
                 destination_folder_path: str, new_name: Optional[str] = None) -> UseCaseResult:
        """
        Copy a file within the current project.

        Args:
            source_folder_path: Source folder path
            file_name: Name of the file to copy
            destination_folder_path: Destination folder path
            new_name: Optional new name for the copied file

        Returns:
            UseCaseResult with copy results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = CopyFileRequest(
            project=self.current_project,
            source_folder_path=source_folder_path,
            file_name=file_name,
            destination_folder_path=destination_folder_path,
            new_name=new_name
        )

        result = self._copy_file_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    def delete_item(self, folder_path: str, item_name: str, item_type: str) -> UseCaseResult:
        """
        Delete an item from the current project.

        Args:
            folder_path: Folder containing the item
            item_name: Name of the item to delete
            item_type: Type of item ('file' or 'folder')

        Returns:
            UseCaseResult with deletion results
        """
        if not self.current_project:
            return UseCaseResult(
                success=False,
                error="No project is currently open"
            )

        request = DeleteItemRequest(
            project=self.current_project,
            folder_path=folder_path,
            item_name=item_name,
            item_type=item_type
        )

        result = self._delete_item_use_case.execute_safely(request)

        if result.success:
            self.project_modified = True

        return result

    # Project State Management

    def has_current_project(self) -> bool:
        """Check if a project is currently open."""
        return self.current_project is not None

    def has_unsaved_changes(self) -> bool:
        """Check if the current project has unsaved changes."""
        return self.project_modified

    def get_current_project(self) -> Optional[Project]:
        """Get the current project (read-only access)."""
        return self.current_project

    def get_project_statistics(self) -> Optional[Dict[str, Any]]:
        """Get statistics for the current project."""
        if not self.current_project:
            return None

        return self.current_project.get_project_statistics()

    def get_application_status(self) -> Dict[str, Any]:
        """Get the current application status."""
        status = {
            'has_project': self.has_current_project(),
            'has_unsaved_changes': self.has_unsaved_changes(),
            'timestamp': datetime.now()
        }

        if self.current_project:
            status.update({
                'project_name': self.current_project.name,
                'project_path': self.current_project.project_file_path,
                'project_statistics': self.get_project_statistics()
            })

        return status