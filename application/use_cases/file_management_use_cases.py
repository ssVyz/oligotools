"""
Enhanced file management use cases for Oligotools
Handles file operations within projects: remove, rename, move, categorize files.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

from domain import Project, FileReference, FileCategory
from domain.exceptions import DomainError, ItemNotFoundError, DuplicateNameError
from data.exceptions import DataError
from ..base_use_case import BaseUseCase, FileOperationRequest
from ..exceptions import UseCaseError, ValidationError, InvalidOperationError


@dataclass
class RemoveFileFromProjectRequest(FileOperationRequest):
    """Request to remove a file from project (but not from disk)."""
    pass


@dataclass
class RemoveFileFromProjectResponse:
    """Response from removing a file from project."""
    removed_file: FileReference
    success_message: str


@dataclass
class RenameFileInProjectRequest(FileOperationRequest):
    """Request to rename a file within the project."""
    new_name: str = ""


@dataclass
class RenameFileInProjectResponse:
    """Response from renaming a file in project."""
    old_name: str
    new_name: str
    success_message: str


@dataclass
class MoveFileInProjectRequest(FileOperationRequest):
    """Request to move a file within the project."""
    destination_folder_path: str = ""
    new_name: Optional[str] = None


@dataclass
class MoveFileInProjectResponse:
    """Response from moving a file in project."""
    source_path: str
    destination_path: str
    success_message: str


@dataclass
class SetFileCategoryRequest(FileOperationRequest):
    """Request to set the category of a file."""
    category: FileCategory = FileCategory.UNCATEGORIZED


@dataclass
class SetFileCategoryResponse:
    """Response from setting file category."""
    file_name: str
    old_category: FileCategory
    new_category: FileCategory
    success_message: str


@dataclass
class GetFilesByCategoryRequest:
    """Request to get files by category."""
    project: Project
    categories: List[FileCategory]
    file_types: Optional[List[str]] = None


@dataclass
class GetFilesByCategoryResponse:
    """Response with files matching category criteria."""
    matching_files: List[FileReference]
    total_count: int


class RemoveFileFromProjectUseCase(BaseUseCase[RemoveFileFromProjectRequest, RemoveFileFromProjectResponse]):
    """Use case for removing files from project without deleting from disk."""

    def validate_request(self, request: RemoveFileFromProjectRequest) -> None:
        """Validate remove file request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.file_name or not request.file_name.strip():
            raise ValidationError("File name cannot be empty")

        if not request.folder_path:
            raise ValidationError("Folder path cannot be empty")

    def execute(self, request: RemoveFileFromProjectRequest) -> RemoveFileFromProjectResponse:
        """Execute remove file from project use case."""
        try:
            # Remove file from project
            removed_file = request.project.remove_file_from_project(
                folder_path=request.folder_path,
                file_name=request.file_name
            )

            return RemoveFileFromProjectResponse(
                removed_file=removed_file,
                success_message=f"File '{request.file_name}' removed from project (file remains on disk)"
            )

        except ItemNotFoundError as e:
            raise UseCaseError(f"File not found: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error removing file: {e}")


class RenameFileInProjectUseCase(BaseUseCase[RenameFileInProjectRequest, RenameFileInProjectResponse]):
    """Use case for renaming files within the project."""

    def validate_request(self, request: RenameFileInProjectRequest) -> None:
        """Validate rename file request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.file_name or not request.file_name.strip():
            raise ValidationError("Current file name cannot be empty")

        if not request.new_name or not request.new_name.strip():
            raise ValidationError("New file name cannot be empty")

        if not request.folder_path:
            raise ValidationError("Folder path cannot be empty")

        if request.file_name == request.new_name:
            raise ValidationError("New name must be different from current name")

        # Validate new name doesn't contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in request.new_name for char in invalid_chars):
            raise ValidationError(f"File name contains invalid characters: {invalid_chars}")

    def execute(self, request: RenameFileInProjectRequest) -> RenameFileInProjectResponse:
        """Execute rename file in project use case."""
        try:
            # Rename file in project
            request.project.rename_file_in_project(
                folder_path=request.folder_path,
                old_name=request.file_name,
                new_name=request.new_name.strip()
            )

            return RenameFileInProjectResponse(
                old_name=request.file_name,
                new_name=request.new_name.strip(),
                success_message=f"File renamed from '{request.file_name}' to '{request.new_name.strip()}'"
            )

        except ItemNotFoundError as e:
            raise UseCaseError(f"File not found: {e}")
        except DuplicateNameError as e:
            raise UseCaseError(f"Name conflict: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error renaming file: {e}")


class MoveFileInProjectUseCase(BaseUseCase[MoveFileInProjectRequest, MoveFileInProjectResponse]):
    """Use case for moving files within the project."""

    def validate_request(self, request: MoveFileInProjectRequest) -> None:
        """Validate move file request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.file_name or not request.file_name.strip():
            raise ValidationError("File name cannot be empty")

        if not request.folder_path:
            raise ValidationError("Source folder path cannot be empty")

        if not request.destination_folder_path:
            raise ValidationError("Destination folder path cannot be empty")

        if request.folder_path == request.destination_folder_path and not request.new_name:
            raise ValidationError("Cannot move file to same folder without renaming")

        # Validate new name if provided
        if request.new_name:
            invalid_chars = '<>:"/\\|?*'
            if any(char in request.new_name for char in invalid_chars):
                raise ValidationError(f"New file name contains invalid characters: {invalid_chars}")

    def execute(self, request: MoveFileInProjectRequest) -> MoveFileInProjectResponse:
        """Execute move file in project use case."""
        try:
            # Move file in project
            request.project.move_file_in_project(
                source_path=request.folder_path,
                file_name=request.file_name,
                dest_path=request.destination_folder_path,
                new_name=request.new_name.strip() if request.new_name else None
            )

            action_desc = f"moved from '{request.folder_path}' to '{request.destination_folder_path}'"
            if request.new_name:
                action_desc += f" and renamed to '{request.new_name.strip()}'"

            return MoveFileInProjectResponse(
                source_path=request.folder_path,
                destination_path=request.destination_folder_path,
                success_message=f"File '{request.file_name}' {action_desc}"
            )

        except ItemNotFoundError as e:
            raise UseCaseError(f"File or folder not found: {e}")
        except DuplicateNameError as e:
            raise UseCaseError(f"Name conflict: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error moving file: {e}")


class SetFileCategoryUseCase(BaseUseCase[SetFileCategoryRequest, SetFileCategoryResponse]):
    """Use case for setting file categories."""

    def validate_request(self, request: SetFileCategoryRequest) -> None:
        """Validate set file category request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.file_name or not request.file_name.strip():
            raise ValidationError("File name cannot be empty")

        if not request.folder_path:
            raise ValidationError("Folder path cannot be empty")

        if not isinstance(request.category, FileCategory):
            raise ValidationError("Invalid category type")

    def execute(self, request: SetFileCategoryRequest) -> SetFileCategoryResponse:
        """Execute set file category use case."""
        try:
            # Get current category for response
            file_ref = request.project.find_file_by_path(request.folder_path, request.file_name)
            if not file_ref:
                raise ItemNotFoundError(f"File '{request.file_name}' not found in '{request.folder_path}'")

            old_category = file_ref.file_category

            # Set new category
            request.project.set_file_category(
                folder_path=request.folder_path,
                file_name=request.file_name,
                category=request.category
            )

            return SetFileCategoryResponse(
                file_name=request.file_name,
                old_category=old_category,
                new_category=request.category,
                success_message=f"File '{request.file_name}' category changed from '{old_category.get_display_name(old_category)}' to '{request.category.get_display_name(request.category)}'"
            )

        except ItemNotFoundError as e:
            raise UseCaseError(f"File not found: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error setting category: {e}")


class GetFilesByCategoryUseCase(BaseUseCase[GetFilesByCategoryRequest, GetFilesByCategoryResponse]):
    """Use case for getting files by category and type."""

    def validate_request(self, request: GetFilesByCategoryRequest) -> None:
        """Validate get files by category request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.categories:
            raise ValidationError("At least one category must be specified")

        for category in request.categories:
            if not isinstance(category, FileCategory):
                raise ValidationError(f"Invalid category type: {category}")

    def execute(self, request: GetFilesByCategoryRequest) -> GetFilesByCategoryResponse:
        """Execute get files by category use case."""
        try:
            # Get files matching criteria
            if request.file_types:
                matching_files = request.project.get_files_by_type_and_category(
                    file_types=request.file_types,
                    categories=request.categories,
                    recursive=True
                )
            else:
                matching_files = request.project.get_files_by_category(
                    categories=request.categories,
                    recursive=True
                )

            return GetFilesByCategoryResponse(
                matching_files=matching_files,
                total_count=len(matching_files)
            )

        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error getting files: {e}")