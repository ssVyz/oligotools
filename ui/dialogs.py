"""
Dialogs for Oligotools UI
Custom dialog boxes for user interaction.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from pathlib import Path


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setModal(True)
        self.resize(500, 300)

        self.project_name = ""
        self.project_path = ""
        self.description = ""

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Project info group
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)

        # Project name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        info_layout.addRow("Project Name:", self.name_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional project description...")
        self.description_edit.setMaximumHeight(80)
        info_layout.addRow("Description:", self.description_edit)

        layout.addWidget(info_group)

        # File location group
        location_group = QGroupBox("Project File Location")
        location_layout = QVBoxLayout(location_group)

        # File path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Choose where to save the project file...")
        self.path_edit.setReadOnly(True)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_location)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)

        location_layout.addLayout(path_layout)
        layout.addWidget(location_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.create_button = QPushButton("Create Project")
        self.create_button.clicked.connect(self._create_project)
        self.create_button.setDefault(True)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.create_button)

        layout.addLayout(button_layout)

        # Connect name change to auto-update path
        self.name_edit.textChanged.connect(self._update_suggested_path)

    def _browse_location(self):
        """Browse for project file location."""
        suggested_name = self.name_edit.text().strip()
        if not suggested_name:
            suggested_name = "New Project"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            f"{suggested_name}.oligoproj",
            "Oligotools Project Files (*.oligoproj);;All Files (*)"
        )

        if file_path:
            self.path_edit.setText(file_path)

    def _update_suggested_path(self, name):
        """Update suggested file path based on project name."""
        if name.strip() and not self.path_edit.text():
            # Only suggest if no path is set yet
            suggested_path = Path.home() / f"{name.strip()}.oligoproj"
            self.path_edit.setText(str(suggested_path))

    def _create_project(self):
        """Validate and create project."""
        # Get values
        self.project_name = self.name_edit.text().strip()
        self.project_path = self.path_edit.text().strip()
        self.description = self.description_edit.toPlainText().strip()

        # Validate
        if not self.project_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name.")
            self.name_edit.setFocus()
            return

        if not self.project_path:
            QMessageBox.warning(self, "Invalid Input", "Please choose a location for the project file.")
            self.browse_button.setFocus()
            return

        # Check if file already exists
        if Path(self.project_path).exists():
            reply = QMessageBox.question(
                self, "File Exists",
                f"The file '{self.project_path}' already exists. Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Ensure .oligoproj extension
        if not self.project_path.lower().endswith('.oligoproj'):
            self.project_path += '.oligoproj'

        self.accept()


class FolderSelectionDialog(QDialog):
    """Dialog for selecting a folder within a project."""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Folder")
        self.setModal(True)
        self.resize(400, 300)

        self.project = project
        self.selected_folder_path = "Root"

        self._setup_ui()
        self._populate_folder_tree()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Select a folder for the operation:")
        layout.addWidget(label)

        # Folder tree
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("Project Folders")
        self.folder_tree.itemClicked.connect(self._on_folder_selected)
        layout.addWidget(self.folder_tree)

        # Selected path display
        self.selected_label = QLabel(f"Selected: {self.selected_folder_path}")
        layout.addWidget(self.selected_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

    def _populate_folder_tree(self):
        """Populate the folder tree with project folders."""
        if not self.project:
            return

        self._add_folder_to_tree(self.project.root_folder, None)

        # Expand all items
        self.folder_tree.expandAll()

    def _add_folder_to_tree(self, folder, parent_item):
        """Recursively add folders to tree."""
        from PySide6.QtWidgets import QTreeWidgetItem

        if parent_item is None:
            item = QTreeWidgetItem(self.folder_tree, [folder.name])
        else:
            item = QTreeWidgetItem(parent_item, [folder.name])

        # Store folder path in item data
        path = self._build_folder_path(item)
        item.setData(0, Qt.UserRole, path)

        # Add subfolders
        for subfolder in folder.subfolders.values():
            self._add_folder_to_tree(subfolder, item)

    def _build_folder_path(self, item):
        """Build full folder path from tree item."""
        path_parts = []
        current = item

        while current:
            path_parts.insert(0, current.text(0))
            current = current.parent()

        return "/".join(path_parts)

    def _on_folder_selected(self, item, column):
        """Handle folder selection."""
        self.selected_folder_path = item.data(0, Qt.UserRole)
        self.selected_label.setText(f"Selected: {self.selected_folder_path}")