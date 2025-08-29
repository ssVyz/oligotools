"""
File and folder management use cases for Oligotools
Handles operations within projects: import files, create folders, move/copy items.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from domain.entities import Project, FileReference, Folder
from domain.exceptions import DomainError, ItemNotFoundError, DuplicateNameError
from data.exceptions import DataError, FileNotFoundError
from data.format_detector import FormatDetector
from ..base_use_case import BaseUseCase, FileOperationRequest, FolderOperationRequest
from ..exceptions import UseCaseError, ValidationError, InvalidOperationError


@dataclass
class ImportFileRequest:
    """Request to import a file into a project."""
    project: Project
    source_file_path: str
    target_folder_path: str
    copy_file: bool = True
    auto_detect_format: bool = True


@dataclass
class ImportFileResponse:
    """Response from importing a file."""
    file_reference: FileReference
    detected_format: Optional[Dict[str, Any]] = None
    success_message: str = ""


@dataclass
class CreateFolderRequest:
    """Request to create a new folder in a project."""
    project: Project
    parent_folder_path: str
    folder_name: str


@dataclass
class CreateFolderResponse:
    """Response from creating a folder."""
    folder: Folder
    folder_path: str
    success_message: str


@dataclass
class MoveItemRequest:
    """Request to move an item (file or folder) within a project."""
    project: Project
    source_folder_path: str
    item_name: str
    destination_folder_path: str


@dataclass
class MoveItemResponse:
    """Response from moving an item."""
    success_message: str
    item_type: str  # 'file' or 'folder'


@dataclass
class CopyFileRequest:
    """Request to copy a file within a project."""
    project: Project
    source_folder_path: str
    file_name: str
    destination_folder_path: str
    new_name: Optional[str] = None


@dataclass
class CopyFileResponse:
    """Response from copying a file."""
    new_file_reference: FileReference
    success_message: str


@dataclass
class DeleteItemRequest:
    """Request to delete an item (file or folder) from a project."""
    project: Project
    folder_path: str
    item_name: str
    item_type: str  # 'file' or 'folder'


@dataclass
class DeleteItemResponse:
    """Response from deleting an item."""
    success_message: str
    deleted_item_type: str


class ImportFileUseCase(BaseUseCase[ImportFileRequest, ImportFileResponse]):
    """Use case for importing files into a project."""

    def validate_request(self, request: ImportFileRequest) -> None:
        """Validate import file request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.source_file_path or not request.source_file_path.strip():
            raise ValidationError("Source file path cannot be empty")

        if not request.target_folder_path:
            raise ValidationError("Target folder path cannot be empty")

        # Check source file exists
        source_path = Path(request.source_file_path)
        if not source_path.exists():
            raise ValidationError(f"Source file does not exist: {request.source_file_path}")

        if not source_path.is_file():
            raise ValidationError(f"Source path is not a file: {request.source_file_path}")

        # Check target folder exists in project
        try:
            request.project.get_folder_by_path(request.target_folder_path)
        except ItemNotFoundError:
            raise ValidationError(f"Target folder does not exist: {request.target_folder_path}")

    def execute(self, request: ImportFileRequest) -> ImportFileResponse:
        """Execute import file use case."""
        try:
            # Detect file format if requested
            detected_format = None
            if request.auto_detect_format:
                format_by_extension = FormatDetector.detect_format_by_extension(request.source_file_path)
                format_by_content = FormatDetector.detect_format_by_content(request.source_file_path)

                detected_format = {
                    'extension_based': format_by_extension,
                    'content_based': format_by_content
                }

            # Import the file using repository
            file_reference = self.project_repository.import_file_to_project(
                project=request.project,
                source_file_path=request.source_file_path,
                target_folder_path=request.target_folder_path,
                copy_file=request.copy_file
            )

            # Update file type with detected format if available
            if detected_format and detected_format['content_based']['confidence'] > 0.7:
                file_reference.file_type = detected_format['content_based']['format']

            action = "copied to" if request.copy_file else "linked to"
            success_message = f"File '{file_reference.name}' {action} '{request.target_folder_path}'"

            return ImportFileResponse(
                file_reference=file_reference,
                detected_format=detected_format,
                success_message=success_message
            )

        except FileNotFoundError as e:
            raise UseCaseError(f"File not found: {e}")
        except DataError as e:
            raise UseCaseError(f"Data layer error: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error importing file: {e}")


class CreateFolderUseCase(BaseUseCase[CreateFolderRequest, CreateFolderResponse]):
    """Use case for creating folders in a project."""

    def validate_request(self, request: CreateFolderRequest) -> None:
        """Validate create folder request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.folder_name or not request.folder_name.strip():
            raise ValidationError("Folder name cannot be empty")

        if not request.parent_folder_path:
            raise ValidationError("Parent folder path cannot be empty")

        # Validate folder name
        invalid_chars = '<>:"/\\|?*'
        if any(char in request.folder_name for char in invalid_chars):
            raise ValidationError(f"Folder name contains invalid characters: {invalid_chars}")

        # Check parent folder exists
        try:
            parent_folder = request.project.get_folder_by_path(request.parent_folder_path)
            # Check if folder name already exists
            if request.folder_name in parent_folder.get_path_items():
                raise ValidationError(f"Item '{request.folder_name}' already exists in '{request.parent_folder_path}'")
        except ItemNotFoundError:
            raise ValidationError(f"Parent folder does not exist: {request.parent_folder_path}")

    def execute(self, request: CreateFolderRequest) -> CreateFolderResponse:
        """Execute create folder use case."""
        try:
            # Create the folder using project
            folder = request.project.create_folder_at_path(
                folder_path=request.parent_folder_path,
                folder_name=request.folder_name
            )

            # Build full folder path
            if request.parent_folder_path == "Root":
                folder_path = f"Root/{request.folder_name}"
            else:
                folder_path = f"{request.parent_folder_path}/{request.folder_name}"

            return CreateFolderResponse(
                folder=folder,
                folder_path=folder_path,
                success_message=f"Folder '{request.folder_name}' created in '{request.parent_folder_path}'"
            )

        except DuplicateNameError as e:
            raise UseCaseError(f"Name conflict: {e}")
        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error creating folder: {e}")


class MoveItemUseCase(BaseUseCase[MoveItemRequest, MoveItemResponse]):
    """Use case for moving items within a project."""

    def validate_request(self, request: MoveItemRequest) -> None:
        """Validate move item request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.item_name or not request.item_name.strip():
            raise ValidationError("Item name cannot be empty")

        if not request.source_folder_path:
            raise ValidationError("Source folder path cannot be empty")

        if not request.destination_folder_path:
            raise ValidationError("Destination folder path cannot be empty")

        if request.source_folder_path == request.destination_folder_path:
            raise ValidationError("Source and destination folders cannot be the same")

        # Check source and destination folders exist
        try:
            source_folder = request.project.get_folder_by_path(request.source_folder_path)
            dest_folder = request.project.get_folder_by_path(request.destination_folder_path)

            # Check item exists in source folder
            if request.item_name not in source_folder.get_path_items():
                raise ValidationError(f"Item '{request.item_name}' not found in '{request.source_folder_path}'")

            # Check for name conflicts in destination
            if request.item_name in dest_folder.get_path_items():
                raise ValidationError(
                    f"Item '{request.item_name}' already exists in '{request.destination_folder_path}'")

        except ItemNotFoundError as e:
            raise ValidationError(f"Folder not found: {e}")

    def execute(self, request: MoveItemRequest) -> MoveItemResponse:
        """Execute move item use case."""
        try:
            # Check what type of item we're moving
            source_folder = request.project.get_folder_by_path(request.source_folder_path)

            if request.item_name in source_folder.files:
                item_type = "file"
            elif request.item_name in source_folder.subfolders:
                item_type = "folder"
            else:
                raise UseCaseError(f"Item '{request.item_name}' not found")

            # Move the item using project
            request.project.move_item(
                source_path=request.source_folder_path,
                item_name=request.item_name,
                dest_path=request.destination_folder_path
            )

            return MoveItemResponse(
                success_message=f"{item_type.title()} '{request.item_name}' moved from '{request.source_folder_path}' to '{request.destination_folder_path}'",
                item_type=item_type
            )

        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error moving item: {e}")


class CopyFileUseCase(BaseUseCase[CopyFileRequest, CopyFileResponse]):
    """Use case for copying files within a project."""

    def validate_request(self, request: CopyFileRequest) -> None:
        """Validate copy file request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.file_name or not request.file_name.strip():
            raise ValidationError("File name cannot be empty")

        if not request.source_folder_path:
            raise ValidationError("Source folder path cannot be empty")

        if not request.destination_folder_path:
            raise ValidationError("Destination folder path cannot be empty")

        # Check folders exist and file exists
        try:
            source_folder = request.project.get_folder_by_path(request.source_folder_path)
            dest_folder = request.project.get_folder_by_path(request.destination_folder_path)

            if request.file_name not in source_folder.files:
                raise ValidationError(f"File '{request.file_name}' not found in '{request.source_folder_path}'")

            # Check for name conflicts
            target_name = request.new_name or request.file_name
            if target_name in dest_folder.get_path_items():
                raise ValidationError(f"Item '{target_name}' already exists in '{request.destination_folder_path}'")

        except ItemNotFoundError as e:
            raise ValidationError(f"Folder not found: {e}")

    def execute(self, request: CopyFileRequest) -> CopyFileResponse:
        """Execute copy file use case."""
        try:
            # Copy the file using project
            new_file_ref = request.project.copy_file(
                source_path=request.source_folder_path,
                file_name=request.file_name,
                dest_path=request.destination_folder_path,
                new_name=request.new_name
            )

            target_name = request.new_name or request.file_name
            success_message = f"File '{request.file_name}' copied to '{request.destination_folder_path}' as '{target_name}'"

            return CopyFileResponse(
                new_file_reference=new_file_ref,
                success_message=success_message
            )

        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error copying file: {e}")


class DeleteItemUseCase(BaseUseCase[DeleteItemRequest, DeleteItemResponse]):
    """Use case for deleting items from a project."""

    def validate_request(self, request: DeleteItemRequest) -> None:
        """Validate delete item request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.item_name or not request.item_name.strip():
            raise ValidationError("Item name cannot be empty")

        if not request.folder_path:
            raise ValidationError("Folder path cannot be empty")

        if request.item_type not in ['file', 'folder']:
            raise ValidationError("Item type must be 'file' or 'folder'")

        # Check folder exists and item exists
        try:
            folder = request.project.get_folder_by_path(request.folder_path)

            if request.item_type == 'file' and request.item_name not in folder.files:
                raise ValidationError(f"File '{request.item_name}' not found in '{request.folder_path}'")

            if request.item_type == 'folder' and request.item_name not in folder.subfolders:
                raise ValidationError(f"Folder '{request.item_name}' not found in '{request.folder_path}'")

        except ItemNotFoundError as e:
            raise ValidationError(f"Folder not found: {e}")

    def execute(self, request: DeleteItemRequest) -> DeleteItemResponse:
        """Execute delete item use case."""
        try:
            folder = request.project.get_folder_by_path(request.folder_path)

            if request.item_type == 'file':
                folder.remove_file(request.item_name)
            else:  # folder
                # Check if folder is empty (safety check)
                subfolder = folder.get_subfolder(request.item_name)
                if not subfolder.is_empty():
                    raise InvalidOperationError(f"Cannot delete folder '{request.item_name}' - it is not empty")

                folder.remove_subfolder(request.item_name)

            # Update project modification time
            request.project.last_modified = datetime.now()

            return DeleteItemResponse(
                success_message=f"{request.item_type.title()} '{request.item_name}' deleted from '{request.folder_path}'",
                deleted_item_type=request.item_type
            )

        except DomainError as e:
            raise UseCaseError(f"Domain error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error deleting item: {e}")