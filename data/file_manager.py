"""
File Manager for Oligotools Data Layer
Handles file system operations, path resolution, and file validation.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib

from .exceptions import (
    FileNotFoundError,
    PathResolutionError,
    PermissionError as DataPermissionError
)


class FileManager:
    """Manages file system operations and path resolution for projects."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize FileManager.

        Args:
            project_root: Root directory for resolving relative paths.
                         If None, uses the directory containing the project file.
        """
        self.project_root = Path(project_root) if project_root else None

    def set_project_root(self, project_file_path: str) -> None:
        """Set the project root based on project file location."""
        self.project_root = Path(project_file_path).parent.absolute()

    def resolve_relative_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to an absolute path.

        Args:
            relative_path: Relative path string

        Returns:
            Absolute Path object

        Raises:
            PathResolutionError: If project root is not set or path cannot be resolved
        """
        if not self.project_root:
            raise PathResolutionError("Project root not set - cannot resolve relative paths")

        if not relative_path:
            raise PathResolutionError("Relative path cannot be empty")

        try:
            # Handle both forward and backward slashes
            normalized_path = relative_path.replace('\\', os.sep).replace('/', os.sep)
            resolved_path = (self.project_root / normalized_path).resolve()
            return resolved_path
        except Exception as e:
            raise PathResolutionError(f"Could not resolve path '{relative_path}': {e}")

    def make_relative_path(self, absolute_path: str) -> str:
        """
        Convert an absolute path to a relative path from project root.

        Args:
            absolute_path: Absolute path string

        Returns:
            Relative path string

        Raises:
            PathResolutionError: If project root is not set or path cannot be made relative
        """
        if not self.project_root:
            raise PathResolutionError("Project root not set - cannot create relative paths")

        try:
            abs_path = Path(absolute_path).resolve()
            relative_path = abs_path.relative_to(self.project_root)
            # Use forward slashes for JSON compatibility
            return str(relative_path).replace(os.sep, '/')
        except ValueError:
            # Path is not relative to project root, store as absolute
            return str(Path(absolute_path).resolve()).replace(os.sep, '/')
        except Exception as e:
            raise PathResolutionError(f"Could not make path relative '{absolute_path}': {e}")

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists at the given relative path."""
        try:
            resolved_path = self.resolve_relative_path(relative_path)
            return resolved_path.exists() and resolved_path.is_file()
        except PathResolutionError:
            return False

    def get_file_info(self, relative_path: str) -> Dict[str, Any]:
        """
        Get file information (size, modification time, etc.).

        Args:
            relative_path: Relative path to the file

        Returns:
            Dictionary with file information

        Raises:
            FileNotFoundError: If file doesn't exist
            PathResolutionError: If path cannot be resolved
        """
        resolved_path = self.resolve_relative_path(relative_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        if not resolved_path.is_file():
            raise FileNotFoundError(f"Path is not a file: {relative_path}")

        try:
            stat = resolved_path.stat()
            return {
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_readable': os.access(resolved_path, os.R_OK),
                'is_writable': os.access(resolved_path, os.W_OK),
                'absolute_path': str(resolved_path)
            }
        except OSError as e:
            raise DataPermissionError(f"Cannot access file info for '{relative_path}': {e}")

    def calculate_file_hash(self, relative_path: str, algorithm: str = 'md5') -> str:
        """
        Calculate hash of file contents.

        Args:
            relative_path: Relative path to the file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')

        Returns:
            Hex digest of file hash

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If algorithm is not supported
        """
        resolved_path = self.resolve_relative_path(relative_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        try:
            hasher = hashlib.new(algorithm)
        except ValueError:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        try:
            with open(resolved_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            raise DataPermissionError(f"Cannot read file for hashing '{relative_path}': {e}")

    def validate_file_references(self, file_references: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Validate that all file references point to existing files.

        Args:
            file_references: List of file reference dictionaries

        Returns:
            Dictionary with 'valid', 'missing', and 'errors' lists containing file names
        """
        result = {
            'valid': [],
            'missing': [],
            'errors': []
        }

        for file_ref in file_references:
            file_name = file_ref.get('name', 'unknown')
            relative_path = file_ref.get('relative_path', '')

            try:
                if self.file_exists(relative_path):
                    result['valid'].append(file_name)
                else:
                    result['missing'].append(file_name)
            except Exception as e:
                result['errors'].append(f"{file_name}: {str(e)}")

        return result

    def copy_file_to_project(self, source_path: str, dest_relative_path: str) -> Dict[str, Any]:
        """
        Copy a file into the project directory structure.

        Args:
            source_path: Absolute path to source file
            dest_relative_path: Destination path relative to project root

        Returns:
            Dictionary with copy operation results

        Raises:
            FileNotFoundError: If source file doesn't exist
            PathResolutionError: If paths cannot be resolved
            PermissionError: If copy operation fails due to permissions
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        dest = self.resolve_relative_path(dest_relative_path)

        # Create destination directory if it doesn't exist
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(source, dest)  # copy2 preserves metadata

            # Get file info for the copied file
            file_info = self.get_file_info(dest_relative_path)

            return {
                'success': True,
                'source_path': str(source),
                'dest_path': str(dest),
                'size_bytes': file_info['size_bytes'],
                'relative_path': dest_relative_path
            }

        except OSError as e:
            raise DataPermissionError(f"Failed to copy file '{source_path}' to '{dest_relative_path}': {e}")

    def create_directory(self, relative_path: str) -> Path:
        """
        Create a directory at the given relative path.

        Args:
            relative_path: Relative path for the new directory

        Returns:
            Absolute Path object of created directory

        Raises:
            PathResolutionError: If path cannot be resolved
            PermissionError: If directory creation fails
        """
        resolved_path = self.resolve_relative_path(relative_path)

        try:
            resolved_path.mkdir(parents=True, exist_ok=True)
            return resolved_path
        except OSError as e:
            raise DataPermissionError(f"Failed to create directory '{relative_path}': {e}")

    def cleanup_empty_directories(self, relative_path: str) -> List[str]:
        """
        Remove empty directories starting from the given path upward.

        Args:
            relative_path: Starting directory path

        Returns:
            List of removed directory paths

        Raises:
            PathResolutionError: If path cannot be resolved
        """
        removed_dirs = []
        current_path = self.resolve_relative_path(relative_path)

        # Don't remove the project root itself
        project_root = self.project_root

        while current_path != project_root and current_path.exists():
            try:
                # Only remove if directory is empty
                if current_path.is_dir() and not any(current_path.iterdir()):
                    current_path.rmdir()
                    removed_dirs.append(self.make_relative_path(str(current_path)))
                    current_path = current_path.parent
                else:
                    break
            except OSError:
                # Stop if we can't remove a directory
                break

        return removed_dirs