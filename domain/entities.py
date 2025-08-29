"""
Domain entities for Oligotools
Contains the core business objects and their rules.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from dataclasses import dataclass, field

from .exceptions import (
    ProjectError, FolderError, FileReferenceError,
    DuplicateNameError, ItemNotFoundError, InvalidPathError
)


@dataclass
class FileReference:
    """Represents a reference to an imported file."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    original_path: str = ""
    relative_path: str = ""
    file_type: str = ""
    size_bytes: int = 0
    imported_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the file reference after initialization."""
        if not self.name.strip():
            raise FileReferenceError("File name cannot be empty")

        if not self.original_path:
            raise FileReferenceError("Original path must be specified")

        # Infer file type from extension if not provided
        if not self.file_type:
            self.file_type = Path(self.name).suffix.lower().lstrip('.')

    def update_metadata(self, **kwargs):
        """Update file metadata."""
        self.metadata.update(kwargs)
        self.last_modified = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'original_path': self.original_path,
            'relative_path': self.relative_path,
            'file_type': self.file_type,
            'size_bytes': self.size_bytes,
            'imported_date': self.imported_date.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileReference':
        """Create from dictionary (deserialization)."""
        file_ref = cls(
            id=data['id'],
            name=data['name'],
            original_path=data['original_path'],
            relative_path=data['relative_path'],
            file_type=data['file_type'],
            size_bytes=data['size_bytes'],
            imported_date=datetime.fromisoformat(data['imported_date']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            metadata=data.get('metadata', {})
        )
        return file_ref


@dataclass
class Folder:
    """Represents a folder in the project structure."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    subfolders: Dict[str, 'Folder'] = field(default_factory=dict)
    files: Dict[str, FileReference] = field(default_factory=dict)
    parent_id: Optional[str] = None

    def __post_init__(self):
        """Validate the folder after initialization."""
        if not self.name.strip():
            raise FolderError("Folder name cannot be empty")

        # Validate folder name (no invalid characters)
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.name for char in invalid_chars):
            raise FolderError(f"Folder name contains invalid characters: {invalid_chars}")

    def add_subfolder(self, folder: 'Folder') -> None:
        """Add a subfolder to this folder."""
        if folder.name in self.subfolders:
            raise DuplicateNameError(f"Subfolder '{folder.name}' already exists")

        if folder.name in self.files:
            raise DuplicateNameError(f"Name '{folder.name}' conflicts with existing file")

        folder.parent_id = self.id
        self.subfolders[folder.name] = folder

    def add_file(self, file_ref: FileReference) -> None:
        """Add a file reference to this folder."""
        if file_ref.name in self.files:
            raise DuplicateNameError(f"File '{file_ref.name}' already exists in this folder")

        if file_ref.name in self.subfolders:
            raise DuplicateNameError(f"Name '{file_ref.name}' conflicts with existing folder")

        self.files[file_ref.name] = file_ref

    def remove_subfolder(self, folder_name: str) -> 'Folder':
        """Remove and return a subfolder."""
        if folder_name not in self.subfolders:
            raise ItemNotFoundError(f"Subfolder '{folder_name}' not found")

        folder = self.subfolders[folder_name]
        del self.subfolders[folder_name]
        folder.parent_id = None
        return folder

    def remove_file(self, file_name: str) -> FileReference:
        """Remove and return a file reference."""
        if file_name not in self.files:
            raise ItemNotFoundError(f"File '{file_name}' not found")

        file_ref = self.files[file_name]
        del self.files[file_name]
        return file_ref

    def get_subfolder(self, folder_name: str) -> 'Folder':
        """Get a subfolder by name."""
        if folder_name not in self.subfolders:
            raise ItemNotFoundError(f"Subfolder '{folder_name}' not found")
        return self.subfolders[folder_name]

    def get_file(self, file_name: str) -> FileReference:
        """Get a file reference by name."""
        if file_name not in self.files:
            raise ItemNotFoundError(f"File '{file_name}' not found")
        return self.files[file_name]

    def rename_subfolder(self, old_name: str, new_name: str) -> None:
        """Rename a subfolder."""
        if old_name not in self.subfolders:
            raise ItemNotFoundError(f"Subfolder '{old_name}' not found")

        if new_name in self.subfolders or new_name in self.files:
            raise DuplicateNameError(f"Name '{new_name}' already exists")

        folder = self.subfolders[old_name]
        folder.name = new_name
        self.subfolders[new_name] = folder
        del self.subfolders[old_name]

    def rename_file(self, old_name: str, new_name: str) -> None:
        """Rename a file reference."""
        if old_name not in self.files:
            raise ItemNotFoundError(f"File '{old_name}' not found")

        if new_name in self.files or new_name in self.subfolders:
            raise DuplicateNameError(f"Name '{new_name}' already exists")

        file_ref = self.files[old_name]
        file_ref.name = new_name
        self.files[new_name] = file_ref
        del self.files[old_name]

    def get_path_items(self) -> List[str]:
        """Get all item names (folders and files) in this folder."""
        return list(self.subfolders.keys()) + list(self.files.keys())

    def is_empty(self) -> bool:
        """Check if folder is empty (no subfolders or files)."""
        return len(self.subfolders) == 0 and len(self.files) == 0

    def get_total_file_count(self) -> int:
        """Get total number of files in this folder and all subfolders recursively."""
        count = len(self.files)
        for subfolder in self.subfolders.values():
            count += subfolder.get_total_file_count()
        return count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'created_date': self.created_date.isoformat(),
            'parent_id': self.parent_id,
            'subfolders': {name: folder.to_dict() for name, folder in self.subfolders.items()},
            'files': {name: file_ref.to_dict() for name, file_ref in self.files.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Folder':
        """Create from dictionary (deserialization)."""
        folder = cls(
            id=data['id'],
            name=data['name'],
            created_date=datetime.fromisoformat(data['created_date']),
            parent_id=data.get('parent_id')
        )

        # Recursively load subfolders
        for name, subfolder_data in data.get('subfolders', {}).items():
            subfolder = cls.from_dict(subfolder_data)
            folder.subfolders[name] = subfolder

        # Load file references
        for name, file_data in data.get('files', {}).items():
            file_ref = FileReference.from_dict(file_data)
            folder.files[name] = file_ref

        return folder


@dataclass
class Project:
    """Represents a complete project with its folder structure and metadata."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    project_file_path: Optional[str] = None
    root_folder: Folder = field(default_factory=lambda: Folder(name="Root"))

    def __post_init__(self):
        """Validate the project after initialization."""
        if not self.name.strip():
            raise ProjectError("Project name cannot be empty")

        # Ensure root folder exists and has correct name
        if not self.root_folder:
            self.root_folder = Folder(name="Root")

    def create_folder_at_path(self, folder_path: str, folder_name: str) -> Folder:
        """Create a new folder at the specified path."""
        parent_folder = self.get_folder_by_path(folder_path)
        new_folder = Folder(name=folder_name)
        parent_folder.add_subfolder(new_folder)
        self.last_modified = datetime.now()
        return new_folder

    def add_file_to_path(self, folder_path: str, file_ref: FileReference) -> None:
        """Add a file reference to the specified folder path."""
        target_folder = self.get_folder_by_path(folder_path)
        target_folder.add_file(file_ref)
        self.last_modified = datetime.now()

    def move_item(self, source_path: str, item_name: str, dest_path: str) -> None:
        """Move a file or folder from source to destination path."""
        source_folder = self.get_folder_by_path(source_path)
        dest_folder = self.get_folder_by_path(dest_path)

        # Check if it's a subfolder or file
        if item_name in source_folder.subfolders:
            folder_to_move = source_folder.remove_subfolder(item_name)
            dest_folder.add_subfolder(folder_to_move)
        elif item_name in source_folder.files:
            file_to_move = source_folder.remove_file(item_name)
            dest_folder.add_file(file_to_move)
        else:
            raise ItemNotFoundError(f"Item '{item_name}' not found in source folder")

        self.last_modified = datetime.now()

    def copy_file(self, source_path: str, file_name: str, dest_path: str,
                  new_name: Optional[str] = None) -> FileReference:
        """Copy a file from source to destination path."""
        source_folder = self.get_folder_by_path(source_path)
        dest_folder = self.get_folder_by_path(dest_path)

        if file_name not in source_folder.files:
            raise ItemNotFoundError(f"File '{file_name}' not found")

        original_file = source_folder.files[file_name]

        # Create a copy with new ID
        copied_file = FileReference(
            name=new_name or file_name,
            original_path=original_file.original_path,
            relative_path=original_file.relative_path,
            file_type=original_file.file_type,
            size_bytes=original_file.size_bytes,
            imported_date=original_file.imported_date,
            metadata=original_file.metadata.copy()
        )

        dest_folder.add_file(copied_file)
        self.last_modified = datetime.now()
        return copied_file

    def get_folder_by_path(self, folder_path: str) -> Folder:
        """Get a folder by its path (e.g., 'Root/Sequences/Primers')."""
        if not folder_path or folder_path == "/" or folder_path == "Root":
            return self.root_folder

        # Split path and navigate
        path_parts = [part for part in folder_path.split('/') if part and part != 'Root']
        current_folder = self.root_folder

        for part in path_parts:
            if part not in current_folder.subfolders:
                raise ItemNotFoundError(f"Folder path '{folder_path}' not found")
            current_folder = current_folder.subfolders[part]

        return current_folder

    def get_all_file_references(self) -> List[FileReference]:
        """Get all file references in the project recursively."""

        def collect_files(folder: Folder) -> List[FileReference]:
            files = list(folder.files.values())
            for subfolder in folder.subfolders.values():
                files.extend(collect_files(subfolder))
            return files

        return collect_files(self.root_folder)

    def find_file_by_id(self, file_id: str) -> Optional[FileReference]:
        """Find a file reference by its ID anywhere in the project."""
        for file_ref in self.get_all_file_references():
            if file_ref.id == file_id:
                return file_ref
        return None

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics (file count, types, etc.)."""
        all_files = self.get_all_file_references()
        file_types = {}
        total_size = 0

        for file_ref in all_files:
            file_types[file_ref.file_type] = file_types.get(file_ref.file_type, 0) + 1
            total_size += file_ref.size_bytes

        return {
            'total_files': len(all_files),
            'total_size_bytes': total_size,
            'file_types': file_types,
            'total_folders': self._count_folders(self.root_folder) - 1,  # Exclude root
            'created': self.created_date,
            'last_modified': self.last_modified
        }

    def _count_folders(self, folder: Folder) -> int:
        """Recursively count all folders."""
        count = 1  # Count this folder
        for subfolder in folder.subfolders.values():
            count += self._count_folders(subfolder)
        return count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'project_info': {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'version': self.version,
                'created_date': self.created_date.isoformat(),
                'last_modified': self.last_modified.isoformat(),
                'project_file_path': self.project_file_path
            },
            'folder_structure': self.root_folder.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary (deserialization)."""
        project_info = data['project_info']

        project = cls(
            id=project_info['id'],
            name=project_info['name'],
            description=project_info.get('description', ''),
            version=project_info.get('version', '1.0.0'),
            created_date=datetime.fromisoformat(project_info['created_date']),
            last_modified=datetime.fromisoformat(project_info['last_modified']),
            project_file_path=project_info.get('project_file_path'),
            root_folder=Folder.from_dict(data['folder_structure'])
        )

        return project