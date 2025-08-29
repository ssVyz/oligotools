"""
Base use case classes for Oligotools Application Layer
Defines the structure and common functionality for all use cases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from domain.entities import Project
from dataclasses import dataclass
from datetime import datetime

from data import ProjectRepository
from .exceptions import UseCaseError, ValidationError

# Type variables for request and response
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


@dataclass
class UseCaseResult:
    """Standard result wrapper for use case execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: Optional[list] = None
    execution_time: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseUseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all use cases in the application.

    Provides common functionality for validation, execution, and error handling.
    """

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize the use case.

        Args:
            project_repository: Repository for project data operations
        """
        self.project_repository = project_repository

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """
        Execute the use case.

        Args:
            request: Use case specific request object

        Returns:
            Use case specific response object

        Raises:
            UseCaseError: If execution fails
            ValidationError: If request validation fails
        """
        pass

    def validate_request(self, request: TRequest) -> None:
        """
        Validate the request object.

        Args:
            request: Request to validate

        Raises:
            ValidationError: If validation fails
        """
        if request is None:
            raise ValidationError("Request cannot be None")

    def execute_safely(self, request: TRequest) -> UseCaseResult:
        """
        Execute the use case with error handling and result wrapping.

        Args:
            request: Use case request

        Returns:
            UseCaseResult with success/failure information
        """
        start_time = datetime.now()

        try:
            self.validate_request(request)
            result = self.execute(request)

            execution_time = (datetime.now() - start_time).total_seconds()

            return UseCaseResult(
                success=True,
                data=result,
                execution_time=execution_time
            )

        except ValidationError as e:
            return UseCaseResult(
                success=False,
                error=f"Validation error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except UseCaseError as e:
            return UseCaseResult(
                success=False,
                error=f"Use case error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            return UseCaseResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )


@dataclass
class ProjectRequest:
    """Base class for requests that operate on a project.
    Supports either a full Project object or a project_id."""
    project: Optional[Project] = None
    project_id: Optional[str] = None

@dataclass
class FileOperationRequest(ProjectRequest):
    """Base class for requests that operate on files."""
    folder_path: str = ""
    file_name: Optional[str] = None


@dataclass
class FolderOperationRequest(ProjectRequest):
    """Base class for requests that operate on folders."""
    folder_path: str = ""
    folder_name: Optional[str] = None