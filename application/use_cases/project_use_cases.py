"""
Project management use cases for Oligotools
Handles project lifecycle operations: create, load, save, validate.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

from domain.entities import Project
from domain.exceptions import ProjectError, DomainError
from data.exceptions import ProjectFileError, DataError
from ..base_use_case import BaseUseCase
from ..exceptions import UseCaseError, ValidationError


@dataclass
class CreateProjectRequest:
    """Request to create a new project."""
    project_name: str
    project_file_path: str
    description: str = ""


@dataclass
class CreateProjectResponse:
    """Response from creating a new project."""
    project: Project
    project_file_path: str
    success_message: str


@dataclass
class LoadProjectRequest:
    """Request to load an existing project."""
    project_file_path: str


@dataclass
class LoadProjectResponse:
    """Response from loading a project."""
    project: Project
    validation_results: Dict[str, Any]
    warnings: list = None


@dataclass
class SaveProjectRequest:
    """Request to save a project."""
    project: Project
    create_backup: bool = True


@dataclass
class SaveProjectResponse:
    """Response from saving a project."""
    project_file_path: str
    backup_created: bool
    success_message: str


@dataclass
class ValidateProjectRequest:
    """Request to validate a project."""
    project: Project


@dataclass
class ValidateProjectResponse:
    """Response from project validation."""
    is_valid: bool
    validation_results: Dict[str, Any]
    recommendations: list = None


class CreateNewProjectUseCase(BaseUseCase[CreateProjectRequest, CreateProjectResponse]):
    """Use case for creating a new project."""

    def validate_request(self, request: CreateProjectRequest) -> None:
        """Validate create project request."""
        super().validate_request(request)

        if not request.project_name or not request.project_name.strip():
            raise ValidationError("Project name cannot be empty")

        if not request.project_file_path or not request.project_file_path.strip():
            raise ValidationError("Project file path cannot be empty")

        # Validate project name doesn't contain invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in request.project_name for char in invalid_chars):
            raise ValidationError(f"Project name contains invalid characters: {invalid_chars}")

        # Check if file path is reasonable
        try:
            project_path = Path(request.project_file_path)
            if project_path.exists() and project_path.is_file():
                raise ValidationError("Project file already exists")
        except Exception as e:
            raise ValidationError(f"Invalid project file path: {e}")

    def execute(self, request: CreateProjectRequest) -> CreateProjectResponse:
        """Execute create new project use case."""
        try:
            # Create the project using repository
            project = self.project_repository.create_new_project(
                project_name=request.project_name,
                project_file_path=request.project_file_path,
                description=request.description
            )

            return CreateProjectResponse(
                project=project,
                project_file_path=project.project_file_path,
                success_message=f"Project '{request.project_name}' created successfully"
            )

        except ProjectFileError as e:
            raise UseCaseError(f"Failed to create project file: {e}")
        except DataError as e:
            raise UseCaseError(f"Data layer error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error creating project: {e}")


class LoadProjectUseCase(BaseUseCase[LoadProjectRequest, LoadProjectResponse]):
    """Use case for loading an existing project."""

    def validate_request(self, request: LoadProjectRequest) -> None:
        """Validate load project request."""
        super().validate_request(request)

        if not request.project_file_path or not request.project_file_path.strip():
            raise ValidationError("Project file path cannot be empty")

        project_path = Path(request.project_file_path)
        if not project_path.exists():
            raise ValidationError(f"Project file does not exist: {request.project_file_path}")

        if not project_path.is_file():
            raise ValidationError(f"Project path is not a file: {request.project_file_path}")

    def execute(self, request: LoadProjectRequest) -> LoadProjectResponse:
        """Execute load project use case."""
        try:
            # Load the project
            project = self.project_repository.load_project(request.project_file_path)

            # Validate file references
            validation_results = self.project_repository.validate_project_references(project)

            # Prepare warnings for missing files
            warnings = []
            if validation_results['missing_count'] > 0:
                warnings.append(f"{validation_results['missing_count']} file(s) could not be found")
            if validation_results['error_count'] > 0:
                warnings.append(f"{validation_results['error_count']} file(s) have errors")

            return LoadProjectResponse(
                project=project,
                validation_results=validation_results,
                warnings=warnings if warnings else None
            )

        except ProjectFileError as e:
            raise UseCaseError(f"Failed to load project file: {e}")
        except DataError as e:
            raise UseCaseError(f"Data layer error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error loading project: {e}")


class SaveProjectUseCase(BaseUseCase[SaveProjectRequest, SaveProjectResponse]):
    """Use case for saving a project."""

    def validate_request(self, request: SaveProjectRequest) -> None:
        """Validate save project request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.project.project_file_path:
            raise ValidationError("Project file path not set")

    def execute(self, request: SaveProjectRequest) -> SaveProjectResponse:
        """Execute save project use case."""
        try:
            project_file_path = request.project.project_file_path

            # Check if backup will be created
            backup_will_be_created = (
                    request.create_backup and
                    Path(project_file_path).exists()
            )

            # Save the project
            self.project_repository.save_project(
                project=request.project,
                backup=request.create_backup
            )

            return SaveProjectResponse(
                project_file_path=project_file_path,
                backup_created=backup_will_be_created,
                success_message=f"Project '{request.project.name}' saved successfully"
            )

        except ProjectFileError as e:
            raise UseCaseError(f"Failed to save project: {e}")
        except DataError as e:
            raise UseCaseError(f"Data layer error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error saving project: {e}")


class ValidateProjectUseCase(BaseUseCase[ValidateProjectRequest, ValidateProjectResponse]):
    """Use case for validating project integrity."""

    def validate_request(self, request: ValidateProjectRequest) -> None:
        """Validate project validation request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

    def execute(self, request: ValidateProjectRequest) -> ValidateProjectResponse:
        """Execute project validation use case."""
        try:
            # Get validation results from repository
            validation_results = self.project_repository.validate_project_references(
                request.project
            )

            # Check overall project validity
            is_valid = validation_results['all_valid']

            # Generate recommendations
            recommendations = []

            if validation_results['missing_count'] > 0:
                recommendations.append(
                    f"Relocate or remove {validation_results['missing_count']} missing file reference(s)"
                )

            if validation_results['error_count'] > 0:
                recommendations.append(
                    f"Fix {validation_results['error_count']} file reference error(s)"
                )

            # Check project statistics for additional recommendations
            stats = request.project.get_project_statistics()
            if stats['total_files'] == 0:
                recommendations.append("Project contains no files - consider importing some sequences")

            if stats['total_folders'] <= 1:  # Only root folder
                recommendations.append("Consider organizing files into folders for better structure")

            return ValidateProjectResponse(
                is_valid=is_valid,
                validation_results=validation_results,
                recommendations=recommendations if recommendations else None
            )

        except DataError as e:
            raise UseCaseError(f"Data layer error during validation: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error during validation: {e}")