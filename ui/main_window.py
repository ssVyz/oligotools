"""
Main Window UI for Oligotools
Provides the primary interface with project structure and content viewer.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QToolBar, QStatusBar, QLabel, QPushButton, QMenuBar,
    QMenu, QMessageBox, QFileDialog, QInputDialog, QDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from pathlib import Path
from typing import List

from application import ApplicationService
from .dialogs import NewProjectDialog
from .tool_dialogs import PrimerOverlapToolDialog


class ProjectTreeWidget(QTreeWidget):
    """Custom tree widget for displaying project structure."""

    def __init__(self):
        super().__init__()
        self.setHeaderLabel("Project file structure")
        self.setMinimumWidth(300)

        # Remove placeholder items - we'll populate this with real data


class ContentViewer(QWidget):
    """Content viewer panel for displaying sequences, results, etc."""

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the content viewer interface."""
        layout = QVBoxLayout(self)

        # Title label
        title_label = QLabel("Content viewer")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(title_label)

        # Subtitle label
        subtitle_label = QLabel("(sequences, results, etc)")
        subtitle_label.setStyleSheet("color: gray; margin: 0 10px 10px 10px;")
        layout.addWidget(subtitle_label)

        # Main content area (placeholder)
        self.content_area = QTextEdit()
        self.content_area.setPlainText(
            "Select an item from the project structure to view its contents.\n\n"
            "This area will display:\n"
            "• Sequence files (FASTA, etc.)\n"
            "• Analysis results\n"
            "• Tool outputs\n"
            "• File previews"
        )
        self.content_area.setReadOnly(True)
        layout.addWidget(self.content_area)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oligotools")
        self.setMinimumSize(QSize(800, 600))
        self.resize(QSize(1200, 800))

        # Initialize application service
        self.app_service = ApplicationService()

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._update_ui_state()

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Horizontal splitter for two-panel layout
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left panel: Project structure
        self.project_tree = ProjectTreeWidget()
        splitter.addWidget(self.project_tree)

        # Right panel: Content viewer
        self.content_viewer = ContentViewer()
        splitter.addWidget(self.content_viewer)

        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        # Connect tree selection to content viewer
        self.project_tree.itemClicked.connect(self._on_tree_item_clicked)

    def _setup_menubar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)

        open_project_action = QAction("&Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)

        save_project_action = QAction("&Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(save_project_action)

        file_menu.addSeparator()

        import_action = QAction("&Import File", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_file)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        close_project_action = QAction("&Close Project", self)
        close_project_action.triggered.connect(self._close_project)
        file_menu.addAction(close_project_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Analysis tools submenu
        analysis_menu = tools_menu.addMenu("&Analysis")

        primer_overlap_action = QAction("&Primer Overlap Analyzer", self)
        primer_overlap_action.setToolTip("Analyze 3'-end overlaps between primers to predict dimer formation")
        primer_overlap_action.triggered.connect(self._launch_primer_overlap_tool)
        analysis_menu.addAction(primer_overlap_action)

        tools_menu.addSeparator()

        create_folder_action = QAction("Create &Folder", self)
        create_folder_action.triggered.connect(self._create_folder)
        tools_menu.addAction(create_folder_action)

        validate_project_action = QAction("&Validate Project", self)
        validate_project_action.triggered.connect(self._validate_project)
        tools_menu.addAction(validate_project_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_project_tree)
        view_menu.addAction(refresh_action)

        # Store actions for enabling/disabling
        self.project_actions = [
            save_project_action, import_action, close_project_action,
            create_folder_action, validate_project_action, refresh_action
        ]

        # Store tool actions separately (they need project + appropriate files)
        self.tool_actions = [primer_overlap_action]

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        # Add some basic actions
        new_action = QAction("New Project", self)
        new_action.setToolTip("Create a new project")
        new_action.triggered.connect(self._new_project)
        toolbar.addAction(new_action)

        open_action = QAction("Open Project", self)
        open_action.setToolTip("Open existing project")
        open_action.triggered.connect(self._open_project)
        toolbar.addAction(open_action)

        save_action = QAction("Save Project", self)
        save_action.setToolTip("Save current project")
        save_action.triggered.connect(self._save_project)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        import_action = QAction("Import", self)
        import_action.setToolTip("Import sequence files")
        import_action.triggered.connect(self._import_file)
        toolbar.addAction(import_action)

        create_folder_action = QAction("New Folder", self)
        create_folder_action.setToolTip("Create new folder")
        create_folder_action.triggered.connect(self._create_folder)
        toolbar.addAction(create_folder_action)

        toolbar.addSeparator()

        validate_action = QAction("Validate", self)
        validate_action.setToolTip("Validate project")
        validate_action.triggered.connect(self._validate_project)
        toolbar.addAction(validate_action)

        # Store toolbar actions for enabling/disabling
        self.toolbar_project_actions = [
            save_action, import_action, create_folder_action, validate_action
        ]

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add permanent widgets
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.progress_label = QLabel("")
        self.status_bar.addPermanentWidget(self.progress_label)

    def _on_tree_item_clicked(self, item, column):
        """Handle tree item clicks."""
        item_text = item.text(0)

        # Check if this is a file item (has FileReference in user data)
        file_ref = item.data(0, Qt.UserRole)

        if file_ref:
            # This is a file - try to load and display its content
            self._display_file_content(file_ref)
        else:
            # This is a folder or project root
            if item_text == "No project open":
                self.content_viewer.content_area.setPlainText(
                    "Welcome to Oligotools!\n\n"
                    "To get started:\n"
                    "1. Create a new project (File → New Project)\n"
                    "2. Or open an existing project (File → Open Project)\n\n"
                    "Once you have a project open, you can:\n"
                    "• Import sequence files\n"
                    "• Create folders to organize your files\n"
                    "• Run analysis tools on your sequences"
                )
            else:
                # Show folder information
                if self.app_service.has_current_project():
                    project = self.app_service.get_current_project()
                    try:
                        folder_path = self._get_item_path(item)
                        folder = project.get_folder_by_path(folder_path)

                        content = f"Folder: {folder.name}\n"
                        content += f"Path: {folder_path}\n\n"
                        content += f"Contains:\n"
                        content += f"  Subfolders: {len(folder.subfolders)}\n"
                        content += f"  Files: {len(folder.files)}\n\n"

                        if folder.subfolders:
                            content += "Subfolders:\n"
                            for subfolder_name in folder.subfolders.keys():
                                content += f"  📁 {subfolder_name}\n"
                            content += "\n"

                        if folder.files:
                            content += "Files:\n"
                            for file_name, file_ref in folder.files.items():
                                content += f"  📄 {file_name} ({file_ref.file_type}, {file_ref.size_bytes} bytes)\n"

                        self.content_viewer.content_area.setPlainText(content)
                    except Exception as e:
                        self.content_viewer.content_area.setPlainText(f"Error displaying folder info: {e}")
                else:
                    self.content_viewer.content_area.setPlainText(
                        f"Selected: {item_text}\n\nNo project is currently open."
                    )

        # Update status bar
        self.status_label.setText(f"Selected: {item_text}")

    def _display_file_content(self, file_ref):
        """Display file content in the content viewer."""
        try:
            # Get the absolute path to the file
            if hasattr(self.app_service.project_repository.file_manager, 'resolve_relative_path'):
                file_path = self.app_service.project_repository.file_manager.resolve_relative_path(
                    file_ref.relative_path
                )
            else:
                # Fallback to original path
                file_path = Path(file_ref.original_path)

            # Check if file exists
            if not file_path.exists():
                self.content_viewer.content_area.setPlainText(
                    f"File: {file_ref.name}\n"
                    f"Type: {file_ref.file_type}\n"
                    f"Size: {file_ref.size_bytes} bytes\n"
                    f"Imported: {file_ref.imported_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"⚠️ File not found at: {file_ref.relative_path}\n\n"
                    f"The file may have been moved or deleted.\n"
                    f"Original location: {file_ref.original_path}"
                )
                return

            # Read and display file content (first part only for large files)
            content_header = (
                f"File: {file_ref.name}\n"
                f"Type: {file_ref.file_type}\n"
                f"Size: {file_ref.size_bytes} bytes\n"
                f"Imported: {file_ref.imported_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Path: {file_ref.relative_path}\n"
                f"{'=' * 50}\n\n"
            )

            try:
                # Read file content (limit to first 50KB for display)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read(50000)  # First 50KB

                    if len(file_content) >= 50000:
                        file_content += f"\n\n... (file truncated for display, showing first 50KB of {file_ref.size_bytes} bytes total)"

                    self.content_viewer.content_area.setPlainText(content_header + file_content)

            except UnicodeDecodeError:
                # Binary file
                self.content_viewer.content_area.setPlainText(
                    content_header +
                    f"📋 Binary file - content cannot be displayed as text.\n\n"
                    f"This appears to be a binary file (e.g., Excel, compressed file, etc.)\n"
                    f"Use appropriate tools to view the file content."
                )

        except Exception as e:
            self.content_viewer.content_area.setPlainText(
                f"Error loading file '{file_ref.name}': {str(e)}"
            )

    def _update_ui_state(self):
        """Update UI state based on current project status."""
        has_project = self.app_service.has_current_project()

        # Enable/disable project-specific actions
        for action in self.project_actions:
            action.setEnabled(has_project)

        for action in self.toolbar_project_actions:
            action.setEnabled(has_project)

        # Tool actions need project + check for appropriate files
        has_fasta_files = False
        if has_project:
            # Check if project has FASTA files for tools
            result = self.app_service.get_project_fasta_files()
            has_fasta_files = result.success and len(result.data.fasta_files) > 0

        for action in self.tool_actions:
            action.setEnabled(has_project and has_fasta_files)

        # Update window title
        if has_project:
            project = self.app_service.get_current_project()
            title = f"Oligotools - {project.name}"
            if self.app_service.has_unsaved_changes():
                title += " *"
            self.setWindowTitle(title)
        else:
            self.setWindowTitle("Oligotools")

        # Update project tree
        self._refresh_project_tree()

    def _refresh_project_tree(self):
        """Refresh the project tree display."""
        self.project_tree.clear()

        if not self.app_service.has_current_project():
            # Show placeholder when no project is open
            placeholder = QTreeWidgetItem(self.project_tree, ["No project open"])
            placeholder.setFlags(Qt.NoItemFlags)  # Make it non-selectable
            return

        project = self.app_service.get_current_project()
        self._populate_tree_folder(project.root_folder, None)

    def _populate_tree_folder(self, folder, parent_item):
        """Recursively populate tree with folder contents."""
        # Create tree item for this folder
        if parent_item is None:
            # Root folder
            folder_item = QTreeWidgetItem(self.project_tree, [folder.name])
        else:
            folder_item = QTreeWidgetItem(parent_item, [folder.name])

        folder_item.setExpanded(True)

        # Add subfolders
        for subfolder in folder.subfolders.values():
            self._populate_tree_folder(subfolder, folder_item)

        # Add files
        for file_ref in folder.files.values():
            file_item = QTreeWidgetItem(folder_item, [file_ref.name])
            # Store file reference for later use
            file_item.setData(0, Qt.UserRole, file_ref)

    # Action Methods

    def _new_project(self):
        """Create a new project."""
        dialog = NewProjectDialog(self)

        if dialog.exec() == QDialog.Accepted:
            # Create project with dialog values
            result = self.app_service.create_new_project(
                project_name=dialog.project_name,
                project_file_path=dialog.project_path,
                description=dialog.description
            )

            if result.success:
                self._show_success(result.data.success_message)
                self._update_ui_state()
            else:
                self._show_error("Failed to create project", result.error)

    def _open_project(self):
        """Open an existing project."""
        # Check for unsaved changes
        if self.app_service.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Current project has unsaved changes. Do you want to save before opening another project?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                if not self._save_project():
                    return  # Save failed or was cancelled

        # Get project file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Oligotools Project Files (*.oligoproj);;All Files (*)"
        )

        if not file_path:
            return

        # Load project
        result = self.app_service.load_project(file_path)

        if result.success:
            message = f"Project '{result.data.project.name}' loaded successfully"
            if result.data.warnings:
                message += f"\n\nWarnings:\n" + "\n".join(result.data.warnings)

            self._show_success(message)
            self._update_ui_state()
        else:
            self._show_error("Failed to load project", result.error)

    def _save_project(self) -> bool:
        """Save the current project. Returns True if successful."""
        if not self.app_service.has_current_project():
            return False

        result = self.app_service.save_current_project()

        if result.success:
            self._show_success(result.data.success_message)
            self._update_ui_state()
            return True
        else:
            self._show_error("Failed to save project", result.error)
            return False

    def _close_project(self):
        """Close the current project."""
        if not self.app_service.has_current_project():
            return

        # Check for unsaved changes
        if self.app_service.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Project has unsaved changes. Do you want to save before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                if not self._save_project():
                    return  # Save failed

        result = self.app_service.close_project(force=True)

        if result.success:
            self._show_success("Project closed successfully")
            self._update_ui_state()
        else:
            self._show_error("Failed to close project", result.error)

    def _import_file(self):
        """Import a file into the current project."""
        if not self.app_service.has_current_project():
            return

        # Get selected folder from tree
        selected_items = self.project_tree.selectedItems()
        target_folder = "Root"  # Default to root

        if selected_items:
            item = selected_items[0]
            # Build folder path - this is a simplified version
            # In a full implementation, you'd track the full path
            target_folder = self._get_item_path(item)

        # Get file to import
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import File",
            "",
            "All Files (*);;FASTA Files (*.fasta *.fa *.fas);;FASTQ Files (*.fastq *.fq)"
        )

        if not file_path:
            return

        # Import file
        result = self.app_service.import_file(
            source_file_path=file_path,
            target_folder_path=target_folder,
            copy_file=True,
            auto_detect_format=True
        )

        if result.success:
            message = result.data.success_message
            if result.data.detected_format:
                format_info = result.data.detected_format['content_based']
                if format_info['confidence'] > 0.7:
                    message += f"\nDetected format: {format_info['format']}"

            self._show_success(message)
            self._update_ui_state()
        else:
            self._show_error("Failed to import file", result.error)

    def _create_folder(self):
        """Create a new folder in the current project."""
        if not self.app_service.has_current_project():
            return

        # Get selected folder from tree
        selected_items = self.project_tree.selectedItems()
        parent_folder = "Root"  # Default to root

        if selected_items:
            item = selected_items[0]
            parent_folder = self._get_item_path(item)

        # Get folder name from user
        folder_name, ok = QInputDialog.getText(
            self, "Create Folder", f"Enter folder name (parent: {parent_folder}):"
        )

        if not ok or not folder_name.strip():
            return

        # Create folder
        result = self.app_service.create_folder(
            parent_folder_path=parent_folder,
            folder_name=folder_name.strip()
        )

        if result.success:
            self._show_success(result.data.success_message)
            self._update_ui_state()
        else:
            self._show_error("Failed to create folder", result.error)

    def _validate_project(self):
        """Validate the current project."""
        if not self.app_service.has_current_project():
            return

        result = self.app_service.validate_current_project()

        if result.success:
            validation = result.data.validation_results
            message = f"Project validation completed.\n\n"
            message += f"Valid: {result.data.is_valid}\n"
            message += f"Files checked: {validation['total_files']}\n"
            message += f"Valid files: {validation['valid_count']}\n"
            message += f"Missing files: {validation['missing_count']}\n"
            message += f"Files with errors: {validation['error_count']}\n"

            if result.data.recommendations:
                message += f"\nRecommendations:\n"
                for rec in result.data.recommendations:
                    message += f"• {rec}\n"

            if result.data.is_valid:
                self._show_success(message)
            else:
                self._show_warning("Project Validation", message)
        else:
            self._show_error("Failed to validate project", result.error)

    def _get_item_path(self, item):
        """Get the full path of a tree item."""
        # This is a simplified version - build path from item hierarchy
        path_parts = []
        current_item = item

        while current_item:
            path_parts.insert(0, current_item.text(0))
            current_item = current_item.parent()

        return "/".join(path_parts) if path_parts else "Root"

    # tool launcher

    def _launch_primer_overlap_tool(self):
        """Open the Primer Overlap Analysis tool dialog."""
        try:
            # 1. Ensure a project is open
            project = getattr(self.app_service, "current_project", None)
            if not project:
                QMessageBox.warning(
                    self,
                    "No Project Open",
                    "Please create or open a project before running tools."
                )
                return

            # 2. Try to pre-select a file from the project tree
            preselected = []
            try:
                item = self.project_tree.currentItem()
                if item and hasattr(item, "file_ref") and item.file_ref:
                    rel = getattr(item.file_ref, "relative_path", None)
                    if isinstance(rel, str):
                        preselected = [rel]
            except Exception:
                pass

            # 3. Launch the dialog
            dialog = PrimerOverlapToolDialog(
                self.app_service,
                preselected_files=preselected,
                parent=self
            )
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Tool Error",
                f"Failed to launch Primer Overlap tool:\n{e}"
            )

    # Message Display Methods

    def _show_success(self, message):
        """Show success message."""
        QMessageBox.information(self, "Success", message)
        self.status_label.setText("Operation completed successfully")

    def _show_error(self, title, message):
        """Show error message."""
        QMessageBox.critical(self, title, message)
        self.status_label.setText("Operation failed")

    def _show_warning(self, title, message):
        """Show warning message."""
        QMessageBox.warning(self, title, message)
        self.status_label.setText("Operation completed with warnings")

    def closeEvent(self, event):
        """Handle window close event."""
        if self.app_service.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Project has unsaved changes. Do you want to save before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                if not self._save_project():
                    event.ignore()
                    return

        event.accept()