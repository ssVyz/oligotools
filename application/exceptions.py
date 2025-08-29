"""
Application layer exceptions for Oligotools
Contains exceptions specific to application use cases and workflows.
"""


class ApplicationError(Exception):
    """Base exception for all application layer errors."""
    pass


class UseCaseError(ApplicationError):
    """Raised when a use case cannot be executed."""
    pass


class ValidationError(ApplicationError):
    """Raised when input validation fails."""
    pass


class ProjectNotFoundError(ApplicationError):
    """Raised when trying to operate on a non-existent project."""
    pass


class InvalidOperationError(ApplicationError):
    """Raised when an operation is not valid in the current context."""
    pass


class ConcurrencyError(ApplicationError):
    """Raised when concurrent operations conflict."""
    pass


class WorkflowError(ApplicationError):
    """Raised when a multi-step workflow fails."""
    pass


class AuthorizationError(ApplicationError):
    """Raised when user lacks permission for an operation."""
    pass