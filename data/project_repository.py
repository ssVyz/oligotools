"""
Project Repository for Oligotools Data Layer
Handles project persistence, JSON serialization, and project file management.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from domain.entities import Project, FileReference
from .file_manager import FileManager
from .exceptions import (
    ProjectFileError,
    CorruptedProjectError,
    JsonSerializationError,
    BackupError,
    FileNotFoundError,
    PermissionError as DataPermissionError
)


class ProjectRepository:
    """Repository for project persistence and file management."""

    def __init__(self):
        """Initialize the project repository."""
        self.file_manager = FileManager()
        self._current_project_path: Optional[Path] = None

    def create_new_project(self, project_name: str, project_file_path: str, description: str = "") -> Project:
        """
        Create a new project and save it to disk.

        Args:
            project_name: Name for the new project
            project_file_path: Where to save the project file (.oligoproj)
            description: Optional project description

        Returns:
            New Project instance

        Raises:
            ProjectFileError: If project file cannot be created
            PermissionError: If insufficient permissions
        """
        project_path = Path(project_file_path)

        # Ensure the file has correct extension
        if project_path.suffix.lower() != '.oligoproj':
            project_path = project_path.with_suffix('.oligoproj')

        # Check if file already exists
        if project_path.exists():
            raise ProjectFileError(f"Project file already exists: {project_path}")

        # Create project directory if it doesn't exist
        project_path.parent.mkdir(parents=True, exist_ok=True)

        # Create new project
        project = Project(
            name=project_name,
            description=description,
            project_file_path=str(project_path)
        )

        # Set up file manager
        self.file_manager.set_project_root(str(project_path))
        self._current_project_path = project_path

        # Save the project
        self.save_project(project)

        return project

    def load_project(self, project_file_path: str) -> Project:
        """
        Load a project from disk.

        Args:
            project_file_path: Path to the project file

        Returns:
            Loaded Project instance

        Raises:
            ProjectFileError: If project file doesn't exist or cannot be read
            CorruptedProjectError: If project file is corrupted or invalid
            JsonSerializationError: If JSON parsing fails
        """
        project_path = Path(project_file_path)

        if not project_path.exists():
            raise ProjectFileError(f"Project file not found: {project_path}")

        if not project_path.is_file():
            raise ProjectFileError(f"Project path is not a file: {project_path}")

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except OSError as e:
            raise ProjectFileError(f"Cannot read project file '{project_path}': {e}")
        except json.JSONDecodeError as e:
            raise JsonSerializationError(f"Invalid JSON in project file '{project_path}': {e}")

        # Validate project file structure
        self._validate_project_data(data, project_path)

        try:
            # Load the project
            project = Project.from_dict(data)
            project.project_file_path = str(project_path)

            # Set up file manager
            self.file_manager.set_project_root(str(project_path))
            self._current_project_path = project_path

            return project

        except Exception as e:
            raise CorruptedProjectError(f"Failed to load project from '{project_path}': {e}")

    def save_project(self, project: Project, backup: bool = True) -> None:
        """
        Save a project to disk.

        Args:
            project: Project instance to save
            backup: Whether to create a backup before saving

        Raises:
            ProjectFileError: If project cannot be saved
            BackupError: If backup creation fails
            JsonSerializationError: If JSON serialization fails
        """
        if not project.project_file_path:
            raise ProjectFileError("Project file path not set - cannot save project")

        project_path = Path(project.project_file_path)

        # Update last modified timestamp
        project.last_modified = datetime.now()

        # Create backup if requested and file exists
        if backup and project_path.exists():
            try:
                self._create_backup(project_path)
            except Exception as e:
                raise BackupError(f"Failed to create backup: {e}")

        # Prepare data for serialization
        try:
            data = project.to_dict()
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise JsonSerializationError(f"Failed to serialize project: {e}")

        # Save to temporary file first, then move (atomic operation)
        temp_path = project_path.with_suffix(project_path.suffix + '.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            # Move temporary file to final location
            shutil.move(str(temp_path), str(project_path))

        except OSError as e:
            # Clean up temporary file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise ProjectFileError(f"Cannot save project to '{project_path}': {e}")

    def import_file_to_project(self, project: Project, source_file_path: str,
                               target_folder_path: str, copy_file: bool = True) -> FileReference:
        """
        Import a file into the project.

        Args:
            project: Target project
            source_file_path: Path to source file
            target_folder_path: Folder path within project (e.g., "Root/Sequences")
            copy_file: Whether to copy file into project directory

        Returns:
            FileReference for the imported file

        Raises:
            FileNotFoundError: If source file doesn't exist
            ProjectFileError: If import fails
        """
        source_path = Path(source_file_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file_path}")

        if not source_path.is_file():
            raise FileNotFoundError(f"Source path is not a file: {source_file_path}")

        # Get file information
        file_name = source_path.name
        file_size = source_path.stat().st_size

        if copy_file:
            # Create a relative path for storing the file
            # Use a subdirectory to avoid cluttering project root
            relative_storage_path = f"imported_files/{file_name}"

            # Handle name conflicts by adding a counter
            counter = 1
            original_relative_path = relative_storage_path
            while self.file_manager.file_exists(relative_storage_path):
                name_parts = Path(file_name).stem, Path(file_name).suffix
                new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                relative_storage_path = f"imported_files/{new_name}"
                file_name = new_name
                counter += 1

            # Copy file to project
            copy_result = self.file_manager.copy_file_to_project(
                str(source_path), relative_storage_path
            )
            relative_path = copy_result['relative_path']

        else:
            # Store reference to original file location
            relative_path = self.file_manager.make_relative_path(str(source_path))

        # Create file reference
        file_ref = FileReference(
            name=file_name,
            original_path=str(source_path),
            relative_path=relative_path,
            size_bytes=file_size,
            metadata={
                'imported_copy': copy_file,
                'import_date': datetime.now().isoformat()
            }
        )

        # Add to project
        project.add_file_to_path(target_folder_path, file_ref)

        return file_ref

    def validate_project_references(self, project: Project) -> Dict[str, Any]:
        """
        Validate all file references in a project.

        Args:
            project: Project to validate

        Returns:
            Validation results dictionary
        """
        all_files = project.get_all_file_references()
        file_refs_data = [file_ref.to_dict() for file_ref in all_files]

        validation_result = self.file_manager.validate_file_references(file_refs_data)

        # Add summary information
        validation_result['total_files'] = len(all_files)
        validation_result['valid_count'] = len(validation_result['valid'])
        validation_result['missing_count'] = len(validation_result['missing'])
        validation_result['error_count'] = len(validation_result['errors'])
        validation_result['all_valid'] = validation_result['missing_count'] == 0 and validation_result[
            'error_count'] == 0

        return validation_result

    def get_recent_projects(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of recently accessed project files.

        Args:
            max_count: Maximum number of recent projects to return

        Returns:
            List of project information dictionaries

        Note: This is a placeholder implementation. In a full application,
              you would track recent projects in user preferences/registry.
        """
        # This would typically read from a config file or user preferences
        # For now, return empty list as placeholder
        return []

    def _validate_project_data(self, data: Dict[str, Any], project_path: Path) -> None:
        """
        Validate project data structure.

        Args:
            data: Project data dictionary
            project_path: Path to project file (for error messages)

        Raises:
            CorruptedProjectError: If data structure is invalid
        """
        # Check required top-level keys
        required_keys = ['project_info', 'folder_structure']
        for key in required_keys:
            if key not in data:
                raise CorruptedProjectError(f"Missing required key '{key}' in project file '{project_path}'")

        # Check project_info structure
        project_info = data['project_info']
        required_info_keys = ['id', 'name', 'created_date', 'last_modified']
        for key in required_info_keys:
            if key not in project_info:
                raise CorruptedProjectError(f"Missing required project info key '{key}' in '{project_path}'")

        # Validate folder_structure has required keys
        folder_structure = data['folder_structure']
        required_folder_keys = ['id', 'name']
        for key in required_folder_keys:
            if key not in folder_structure:
                raise CorruptedProjectError(f"Missing required folder key '{key}' in project file '{project_path}'")

    def _create_backup(self, project_path: Path) -> Path:
        """
        Create a backup of the project file.

        Args:
            project_path: Path to project file

        Returns:
            Path to backup file

        Raises:
            BackupError: If backup creation fails
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{project_path.stem}_backup_{timestamp}{project_path.suffix}"
        backup_path = project_path.parent / backup_name

        try:
            shutil.copy2(project_path, backup_path)
            return backup_path
        except OSError as e:
            raise BackupError(f"Failed to create backup '{backup_path}': {e}")

    def get_project_directory(self) -> Optional[Path]:
        """Get the current project directory."""
        if self._current_project_path:
            return self._current_project_path.parent
        return None

    def close_project(self) -> None:
        """Close the current project and clean up resources."""
        self._current_project_path = None
        self.file_manager = FileManager()  # Reset file manager