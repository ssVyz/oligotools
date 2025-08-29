# Oligotools

A bioinformatics application for managing and analyzing oligonucleotide sequences.

## Current Status

**Complete Bioinformatics Analysis Platform** - The application now features:

- ✅ **Complete Architecture** - All layers implemented (Domain, Data, Application, UI)
- ✅ **Project Management** - Create, save, load, and validate projects with JSON persistence
- ✅ **File Organization** - Hierarchical folder structure with unlimited nesting
- ✅ **File Import** - Import sequence files with automatic format detection
- ✅ **Content Viewing** - Real-time display of file contents and project structure
- ✅ **Professional UI** - Intuitive interface with dialogs, menus, and error handling
- ✅ **Analysis Tools** - Modular tool system with primer overlap analysis

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

### Analysis Tools
- **Modular Tool System** - Extensible framework for adding new analysis capabilities
- **Primer Overlap Analyzer** - Analyze 3'-end overlaps between primers to predict dimer formation
- **Background Processing** - Tools run in separate threads to maintain UI responsiveness
- **Automated Output Management** - Results saved to disk and automatically imported to project
- **Parameter Validation** - Type checking and range validation for all tool parameters

### User Interface
- **Two-Panel Design** - Project tree on left, content viewer on right
- **Interactive Project Tree** - Real-time display of your project structure
- **Smart Menus** - Context-sensitive actions that enable only when appropriate
- **Professional Dialogs** - User-friendly forms for all operations
- **Tool Integration** - Access analysis tools through Tools → Analysis menu
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
│   ├── exceptions.py
│   └── tools.py
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
│       ├── file_use_cases.py
│       └── tool_use_cases.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── dialogs.py
│   └── tool_dialogs.py
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

## Analysis Tools

### Primer Overlap Analyzer

Analyzes 3'-end overlaps between primer sequences to predict primer-dimer formation risk.

**Features:**
- Configurable overlap length ranges (2-20 bases)
- Mismatch tolerance settings (0-5 mismatches)
- Self-dimer detection option
- Risk level assessment (HIGH/MEDIUM/LOW)
- ASCII visualization of overlaps
- Comprehensive reporting

**Usage:**
1. Import FASTA files containing primer sequences
2. Go to **Tools → Analysis → Primer Overlap Analyzer**
3. Select input files (auto-detects FASTA files from project)
4. Configure parameters:
   - Minimum/Maximum overlap length
   - Maximum allowed mismatches  
   - Include self-comparisons
5. Click **Run Tool**
6. View results in generated reports

**Output Files:**
- `primer_overlap_analysis.txt` - Detailed analysis with visualizations
- `primer_overlap_summary.csv` - Spreadsheet-compatible summary
- Both files automatically saved to `project_directory/output/` and imported to project

### Risk Assessment Criteria
- **HIGH Risk**: ≥4 perfect base matches at 3'-ends
- **MEDIUM Risk**: 2-3 perfect matches OR ≥4 matches with 1 mismatch
- **LOW Risk**: All other combinations

## Architecture

The application follows **Clean Architecture** principles with clear separation of concerns:

### **Domain Layer** (`domain/`)
- **Core Entities**: `Project`, `Folder`, `FileReference` with business rules
- **Analysis Tools**: `BaseTool`, `PrimerOverlapTool` with extensible framework
- **Business Logic**: File organization, validation, tool execution
- **Domain Exceptions**: Specific error types for business rule violations

### **Data Layer** (`data/`)
- **ProjectRepository**: JSON persistence with atomic saves and backups
- **FileManager**: Cross-platform file operations and path resolution
- **FormatDetector**: Bioinformatics file format detection and validation

### **Application Layer** (`application/`)
- **ApplicationService**: Central coordinator providing unified API to UI
- **Use Cases**: Individual operations (CreateProject, ImportFile, RunTool, etc.)
- **Tool Execution**: Background processing with result management
- **State Management**: Project lifecycle and change tracking

### **UI Layer** (`ui/`)
- **MainWindow**: Primary interface with project tree and content viewer
- **Tool Dialogs**: Professional parameter configuration and execution interfaces
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

### Running Analysis Tools

1. **Import Primer Files**: Import FASTA files containing primer sequences
2. **Launch Tool**: Go to Tools → Analysis → Primer Overlap Analyzer
3. **Configure Analysis**:
   - Select input files from project
   - Set overlap length range (recommended: 3-10 bases)
   - Set maximum mismatches (recommended: 0-1)
   - Enable/disable self-dimer detection
4. **Run Analysis**: Click "Run Tool" and wait for completion
5. **View Results**: Check generated reports in project's Results folder

### Project Organization

- **Create Folders**: Use Tools → Create Folder to organize your files
- **Nested Structure**: Create folders within folders for complex projects
- **File Management**: Import, view, and organize all your sequence files
- **Output Management**: Tool results automatically organized in Results folder
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

Output files are organized as:
```
project_directory/
├── my_project.oligoproj
└── output/
    └── primer_overlap_20250829_143022/
        ├── primer_overlap_analysis.txt
        └── primer_overlap_summary.csv
```

## Development

### Adding New Analysis Tools

The modular tool system makes it easy to add new analysis capabilities:

1. **Create Tool Class**: Inherit from `BaseTool` in `domain/tools.py`
2. **Define Parameters**: Specify configurable parameters with validation
3. **Implement Logic**: Add analysis logic in `execute()` method
4. **Add Use Case**: Create tool-specific execution logic in application layer
5. **Create UI Dialog**: Extend `BaseToolDialog` for parameter configuration
6. **Register Tool**: Add to `AVAILABLE_TOOLS` registry

### Testing the Complete Workflow

The `example_usage.py` script demonstrates all functionality:
- Creates a project programmatically
- Sets up folder structure
- Imports sample files
- Performs various operations
- Shows validation and statistics

### Architecture Benefits

- **Modular Design**: Each layer has clear responsibilities
- **Tool Extensibility**: Easy to add new analysis capabilities
- **Testability**: Use cases can be tested independently
- **Maintainability**: Clean separation between UI and business logic
- **Background Processing**: Long-running analyses don't block the UI

## Requirements

- **Python 3.8+**
- **PySide6** - GUI framework
- **BioPython** - Sequence analysis (required for tools)
- **Standard Libraries** - json, pathlib, datetime, etc.

## Troubleshooting

### Common Issues

- **Tool Import Errors**: Ensure BioPython is installed (`pip install biopython`)
- **File Not Found**: Check that imported files haven't been moved or deleted
- **Permission Errors**: Ensure write access to project directory and output folder
- **Tool Execution Fails**: Check parameter values are within valid ranges

### Getting Help

- Check the application's built-in validation (Tools → Validate Project)
- Review error messages in dialog boxes
- Ensure file paths are accessible and files haven't been moved
- Check tool parameter ranges and requirements

---

**Oligotools** - Complete bioinformatics project management and analysis platform.