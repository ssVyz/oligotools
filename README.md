# Oligotools

A bioinformatics application for managing and analyzing oligonucleotide sequences.

## Current Status

**Fully Functional Core Application** - The application now has a complete working implementation with:

- ✅ **Complete Architecture** - All layers implemented (Domain, Data, Application, UI)
- ✅ **Project Management** - Create, save, load, and validate projects with JSON persistence
- ✅ **File Organization** - Hierarchical folder structure with unlimited nesting
- ✅ **File Import** - Import sequence files with automatic format detection
- ✅ **Content Viewing** - Real-time display of file contents and project structure
- ✅ **Professional UI** - Intuitive interface with dialogs, menus, and error handling

## Features

### Project Management
- **Create New Projects** - Professional dialog for project setup with name, description, and location
- **Save/Load Projects** - JSON-based persistence with automatic backups
- **Project Validation** - Check file references and get recommendations
- **Change Tracking** - Visual indicators for unsaved changes

### File Management
- **Flexible Folder Structure** - Create unlimited nested folders to organize your files
- **File Import** - Import FASTA, FASTQ, text files, and other bioinformatics formats
- **Format Detection** - Automatic detection of file types based on content and extension
- **File Referencing** - Option to copy files into project or reference external locations
- **Content Preview** - View file contents directly in the application

### User Interface
- **Two-Panel Design** - Project tree on left, content viewer on right
- **Interactive Project Tree** - Real-time display of your project structure
- **Smart Menus** - Context-sensitive actions that enable only when appropriate
- **Professional Dialogs** - User-friendly forms for all operations
- **Comprehensive Error Handling** - Clear error messages and warnings

## Installation

1. **Clone or download** the project files to your computer

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Required Files Structure**:
```
oligotools/
├── main.py
├── domain/
│   ├── __init__.py
│   ├── entities.py
│   └── exceptions.py
├── data/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── file_manager.py
│   ├── format_detector.py
│   └── project_repository.py
├── application/
│   ├── __init__.py
│   ├── application_service.py
│   ├── base_use_case.py
│   ├── exceptions.py
│   └── use_cases/
│       ├── __init__.py
│       ├── project_use_cases.py
│       └── file_use_cases.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   └── dialogs.py
├── requirements.txt
├── example_usage.py
└── README.md
```

## Running the Application

### Main Application
```bash
python main.py
```

### Command-Line Demo
```bash
python example_usage.py
```

## Architecture

The application follows **Clean Architecture** principles with clear separation of concerns:

### **Domain Layer** (`domain/`)
- **Core Entities**: `Project`, `Folder`, `FileReference` with business rules
- **Business Logic**: File organization, validation, project statistics
- **Domain Exceptions**: Specific error types for business rule violations

### **Data Layer** (`data/`)
- **ProjectRepository**: JSON persistence with atomic saves and backups
- **FileManager**: Cross-platform file operations and path resolution
- **FormatDetector**: Bioinformatics file format detection and validation

### **Application Layer** (`application/`)
- **ApplicationService**: Central coordinator providing unified API to UI
- **Use Cases**: Individual operations (CreateProject, ImportFile, etc.)
- **State Management**: Project lifecycle and change tracking

### **UI Layer** (`ui/`)
- **MainWindow**: Primary interface with project tree and content viewer
- **Dialogs**: Professional forms for user input
- **Error Handling**: User-friendly messages and confirmations

## Usage Guide

### Creating Your First Project

1. **Launch Oligotools**: Run `python main.py`
2. **New Project**: Go to File → New Project
3. **Fill Project Details**: Enter name, description, and choose save location
4. **Start Organizing**: Create folders using Tools → Create Folder

### Importing Files

1. **Select Target Folder**: Click on a folder in the project tree
2. **Import File**: Go to File → Import File (or use toolbar button)
3. **Choose File**: Select your sequence file (FASTA, FASTQ, etc.)
4. **View Content**: Click the imported file to see its contents

### Project Organization

- **Create Folders**: Use Tools → Create Folder to organize your files
- **Nested Structure**: Create folders within folders for complex projects
- **File Management**: Import, view, and organize all your sequence files
- **Project Validation**: Use Tools → Validate Project to check file integrity

## File Format Support

The application automatically detects and supports:

- **FASTA** (`.fasta`, `.fa`, `.fas`) - Sequence files
- **FASTQ** (`.fastq`, `.fq`) - Sequencing data with quality scores  
- **GenBank** (`.gb`, `.gbk`) - Annotated sequence files
- **Text Files** (`.txt`) - Analysis results and documentation
- **CSV/TSV** (`.csv`, `.tsv`) - Tabular data
- **Excel** (`.xlsx`, `.xls`) - Spreadsheet data

## Project File Structure

Projects are saved as `.oligoproj` files containing:
- Project metadata (name, description, dates)
- Complete folder hierarchy
- File references with relative paths
- Import history and file statistics

Example project structure:
```json
{
  "project_info": {
    "name": "PCR Analysis",
    "version": "1.0.0",
    "created_date": "2025-08-29T10:30:00"
  },
  "folder_structure": {
    "name": "Root",
    "subfolders": {
      "Sequences": { ... },
      "Results": { ... }
    }
  }
}
```

## Development

### Testing the Complete Workflow

The `example_usage.py` script demonstrates all functionality:
- Creates a project programmatically
- Sets up folder structure
- Imports sample files
- Performs various operations
- Shows validation and statistics

### Architecture Benefits

- **Modular Design**: Each layer has clear responsibilities
- **Testability**: Use cases can be tested independently
- **Extensibility**: Easy to add new file formats or analysis tools
- **Maintainability**: Clean separation between UI and business logic

## Planned Features

- **Analysis Tools**: BLAST searches, primer design, sequence alignment
- **Background Processing**: Long-running operations with progress tracking
- **Export Functionality**: Generate reports and export results
- **Advanced File Management**: Move, copy, rename operations
- **Plugin Architecture**: Support for custom analysis tools

## Troubleshooting

### Common Issues

- **Import Errors**: Ensure all required files are present in the project structure
- **File Not Found**: Check that imported files haven't been moved or deleted
- **Permission Errors**: Ensure write access to project directory

### Getting Help

- Check the application's built-in validation (Tools → Validate Project)
- Review error messages in dialog boxes
- Ensure file paths are accessible and files haven't been moved

---

**Oligotools** - Professional bioinformatics project management made simple.