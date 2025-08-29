#!/usr/bin/env python3
"""
Oligotools - Main Entry Point
A bioinformatics tool for managing and analyzing oligonucleotide sequences.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow


def main():
    """Initialize and run the Oligotools application."""
    # Create the application
    # Note: High DPI scaling is enabled by default in modern PySide6 versions
    app = QApplication(sys.argv)
    app.setApplicationName("Oligotools")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Oligotools")

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()