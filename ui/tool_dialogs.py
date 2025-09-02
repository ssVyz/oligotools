"""
Tool dialogs for Oligotools UI
Provides dialog interfaces for configuring and running analysis tools.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QMessageBox, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from typing import Dict, Any, List, Optional
from pathlib import Path
from PySide6.QtWidgets import QApplication
from domain.tools import BaseTool, ToolParameter, get_tool_by_id
from domain.entities import FileReference
from application import ApplicationService


class ToolExecutionThread(QThread):
    """Thread for running tools in the background to keep UI responsive."""

    finished = Signal(object)  # Emits UseCaseResult
    progress = Signal(str)     # Emits progress messages

    def __init__(self, app_service: ApplicationService, tool_id: str,
                 input_files: List[str], parameters: Dict[str, Any]):
        super().__init__()
        self.app_service = app_service
        self.tool_id = tool_id
        self.input_files = input_files
        self.parameters = parameters

    def run(self):
        """Execute the tool in a separate thread."""
        self.progress.emit("Initializing tool...")

        try:
            # Run the tool
            result = self.app_service.run_tool(
                tool_id=self.tool_id,
                input_files=self.input_files,
                parameters=self.parameters,
                output_to_project=True
            )

            self.finished.emit(result)

        except Exception as e:
            # Create a failure result
            from application.base_use_case import UseCaseResult
            result = UseCaseResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
            self.finished.emit(result)


class BaseToolDialog(QDialog):
    """Base class for tool configuration dialogs."""

    def __init__(self, app_service: ApplicationService, tool_id: str,
                 preselected_files: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.app_service = app_service
        self.tool_id = tool_id
        self.preselected_files = preselected_files or []

        # Get tool instance
        self.tool = get_tool_by_id(tool_id)
        if not self.tool:
            raise ValueError(f"Tool '{tool_id}' not found")

        self.setModal(True)
        self.resize(800, 600)
        self.setWindowTitle(f"{self.tool.tool_name} - Configuration")

        # Data
        self.available_files = []
        self.parameter_widgets = {}
        self.execution_thread = None

        self._setup_ui()
        self._load_project_files()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Tool info section
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QVBoxLayout(info_frame)

        title_label = QLabel(self.tool.tool_name)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        info_layout.addWidget(title_label)

        desc_label = QLabel(self.tool.tool_description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        info_layout.addWidget(desc_label)

        version_label = QLabel(f"Version: {self.tool.tool_version}")
        version_label.setStyleSheet("font-size: 10px; color: #95a5a6;")
        info_layout.addWidget(version_label)

        layout.addWidget(info_frame)

        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left panel: File selection
        self._create_file_selection_panel(splitter)

        # Right panel: Parameters
        self._create_parameters_panel(splitter)

        # Set splitter sizes
        splitter.setSizes([400, 400])

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.status_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.run_button = QPushButton("Run Tool")
        self.run_button.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        self.run_button.clicked.connect(self._run_tool)

        # Placeholder for future worklist functionality
        self.add_to_worklist_button = QPushButton("Add to Worklist")
        self.add_to_worklist_button.setEnabled(False)
        self.add_to_worklist_button.setToolTip("Worklist functionality coming soon")

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.add_to_worklist_button)
        button_layout.addWidget(self.run_button)

        layout.addLayout(button_layout)

    def _create_file_selection_panel(self, parent):
        """Create the file selection panel."""
        file_widget = QGroupBox("Input Files")
        parent.addWidget(file_widget)

        layout = QVBoxLayout(file_widget)

        # Instructions
        req = self.tool.get_input_requirements()[0]  # Assume first requirement for now
        file_types_str = ", ".join(req.file_types)
        instruction_text = f"{req.description}\n\nAccepted types: {file_types_str}"
        if req.min_files > 1:
            instruction_text += f"\nMinimum files: {req.min_files}"
        if req.max_files:
            instruction_text += f"\nMaximum files: {req.max_files}"

        instructions = QLabel(instruction_text)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.file_list)

        # File count label
        self.file_count_label = QLabel("0 files selected")
        self.file_count_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.file_count_label)

        # Connect selection changes
        self.file_list.itemSelectionChanged.connect(self._update_file_count)

    def _create_parameters_panel(self, parent):
        """Create the parameters configuration panel."""
        params_widget = QGroupBox("Tool Parameters")
        parent.addWidget(params_widget)

        layout = QVBoxLayout(params_widget)

        # Create parameter form
        form_layout = QFormLayout()

        for param in self.tool.get_parameters():
            widget = self._create_parameter_widget(param)
            self.parameter_widgets[param.name] = widget

            # Create label with tooltip
            label = QLabel(f"{param.display_name}:")
            if param.description:
                label.setToolTip(param.description)

            form_layout.addRow(label, widget)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _create_parameter_widget(self, param: ToolParameter):
        """Create appropriate widget for parameter type."""
        if param.parameter_type == 'int':
            widget = QSpinBox()
            if param.min_value is not None:
                widget.setMinimum(int(param.min_value))
            if param.max_value is not None:
                widget.setMaximum(int(param.max_value))
            widget.setValue(int(param.default_value))
            return widget

        elif param.parameter_type == 'float':
            widget = QDoubleSpinBox()
            if param.min_value is not None:
                widget.setMinimum(float(param.min_value))
            if param.max_value is not None:
                widget.setMaximum(float(param.max_value))
            widget.setValue(float(param.default_value))
            widget.setDecimals(3)
            return widget

        elif param.parameter_type == 'bool':
            widget = QCheckBox()
            widget.setChecked(bool(param.default_value))
            return widget

        elif param.parameter_type == 'choice':
            widget = QComboBox()
            if param.choices:
                widget.addItems(param.choices)
                if param.default_value in param.choices:
                    widget.setCurrentText(param.default_value)
            return widget

        else:  # string
            widget = QLineEdit()
            widget.setText(str(param.default_value))
            return widget

    def _load_project_files(self):
        """Load eligible files from the current project."""
        if not self.app_service.has_current_project():
            self.status_label.setText("No project open")
            return

        # Get FASTA files from project
        result = self.app_service.get_project_fasta_files(self.preselected_files)

        if not result.success:
            self.status_label.setText(f"Error loading files: {result.error}")
            return

        self.available_files = result.data.fasta_files
        preselected = result.data.preselected_files

        # Populate file list
        self.file_list.clear()
        preselected_names = {f.name for f in preselected}

        for file_ref in self.available_files:
            item = QListWidgetItem(f"{file_ref.name} ({file_ref.file_type})")
            item.setData(Qt.UserRole, file_ref)
            self.file_list.addItem(item)

            # Pre-select if in preselected list
            if file_ref.name in preselected_names:
                item.setSelected(True)

        self._update_file_count()

        if not self.available_files:
            self.status_label.setText("No FASTA files found in project")
            self.run_button.setEnabled(False)
        else:
            self.status_label.setText(f"Found {len(self.available_files)} eligible files")

    def _update_file_count(self):
        """Update file selection count display."""
        selected_count = len(self.file_list.selectedItems())
        self.file_count_label.setText(f"{selected_count} files selected")

        # Enable/disable run button based on selection and requirements
        req = self.tool.get_input_requirements()[0]
        valid_selection = selected_count >= req.min_files
        if req.max_files:
            valid_selection = valid_selection and selected_count <= req.max_files

        self.run_button.setEnabled(valid_selection and len(self.available_files) > 0)

    def _get_selected_files(self) -> List[str]:
        """Get list of selected file names."""
        selected_items = self.file_list.selectedItems()
        return [item.data(Qt.UserRole).name for item in selected_items]

    def _get_parameters(self) -> Dict[str, Any]:
        """Get parameter values from widgets."""
        parameters = {}

        for param_name, widget in self.parameter_widgets.items():
            if isinstance(widget, QSpinBox):
                parameters[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                parameters[param_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                parameters[param_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                parameters[param_name] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                parameters[param_name] = widget.text()

        return parameters

    def _run_tool(self):
        """Execute the tool with current configuration."""
        # Get selected files and parameters
        selected_files = self._get_selected_files()
        parameters = self._get_parameters()

        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one file to analyze.")
            return

        # Disable UI during execution
        self.run_button.setEnabled(False)
        self.add_to_worklist_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Running tool...")

        # Start execution thread
        self.execution_thread = ToolExecutionThread(
            self.app_service, self.tool_id, selected_files, parameters
        )
        self.execution_thread.progress.connect(self._update_progress)
        self.execution_thread.finished.connect(self._tool_finished)
        self.execution_thread.start()

    def _update_progress(self, message: str):
        """Update progress display."""
        self.status_label.setText(message)

    def _tool_finished(self, result):
        """Handle tool execution completion."""
        # Re-enable UI
        self.progress_bar.setVisible(False)
        self.run_button.setEnabled(True)

        if result.success:
            # Show success message with details
            tool_result = result.data.tool_result
            stats = tool_result.summary_statistics

            message = f"Tool completed successfully!\n\n"
            message += f"Execution time: {tool_result.execution_time_seconds:.2f} seconds\n"

            if 'total_sequences' in stats:
                message += f"Sequences analyzed: {stats['total_sequences']}\n"
            if 'total_overlaps_found' in stats:
                message += f"Overlaps found: {stats['total_overlaps_found']}\n"
            if 'high_risk_overlaps' in stats:
                message += f"High-risk overlaps: {stats['high_risk_overlaps']}\n"

            message += f"\nOutput files created: {len(result.data.output_files_created)}"

            if result.data.imported_files:
                message += f"\nFiles imported to project: {len(result.data.imported_files)}"

            if tool_result.warnings:
                message += f"\n\nWarnings:\n" + "\n".join(tool_result.warnings)

            # ADDED: Delay the UI update to ensure all operations are complete
            from PySide6.QtCore import QTimer

            def update_parent_ui():
                # Signal parent window to refresh project tree
                if hasattr(self.parent(), '_update_ui_state'):
                    self.parent()._update_ui_state()

                # Force immediate GUI processing
                QApplication.processEvents()

                # Also force a manual tree refresh
                if hasattr(self.parent(), '_refresh_project_tree'):
                    self.parent()._refresh_project_tree()
                    QApplication.processEvents()

            # Execute the UI update after a short delay
            QTimer.singleShot(200, update_parent_ui)

            QMessageBox.information(self, "Tool Completed", message)
            self.accept()  # Close dialog on success

        else:
            # Show error message
            QMessageBox.critical(self, "Tool Failed",
                                 f"Tool execution failed:\n\n{result.error}")
            self.status_label.setText("Tool execution failed")

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.execution_thread and self.execution_thread.isRunning():
            reply = QMessageBox.question(
                self, "Tool Running",
                "A tool is currently running. Do you want to cancel it?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.execution_thread.terminate()
                self.execution_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class PrimerOverlapToolDialog(BaseToolDialog):
    """Specialized dialog for the Primer Overlap Analysis tool."""

    def __init__(self, app_service: ApplicationService,
                 preselected_files: Optional[List[str]] = None, parent=None):
        super().__init__(app_service, 'primer_overlap', preselected_files, parent)

    def _create_parameters_panel(self, parent):
        """Create enhanced parameters panel with primer-specific help."""
        super()._create_parameters_panel(parent)

        # Add primer-specific guidance
        params_widget = parent.widget(1)  # Get the parameters widget
        layout = params_widget.layout()

        # Add explanation text
        help_text = QTextEdit()
        help_text.setMaximumHeight(120)
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <b>Parameter Guidelines:</b><br>
        • <b>Overlap Length:</b> 3-10 bases covers most primer-dimer interactions<br>
        • <b>Risk Levels:</b> HIGH (≥4 perfect matches), MEDIUM (2-3 perfect or ≥4 with 1 mismatch), LOW (other)<br>
        • <b>Self-Comparison:</b> Enable to detect self-dimers within individual primers<br>
        • <b>Mismatches:</b> 0-1 mismatches covers most biologically relevant interactions
        """)
        help_text.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 8px;")

        layout.addWidget(help_text)