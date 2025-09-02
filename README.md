# Oligotools

A bioinformatics application for managing and analyzing oligonucleotide sequences.

## Current Status

**Complete Bioinformatics Analysis Platform** - The application now features:

- ✅ **Complete Architecture** - All layers implemented (Domain, Data, Application, UI)
- ✅ **Project Management** - Create, save, load, and validate projects with JSON persistence
- ✅ **Advanced File Organization** - Hierarchical folder structure with file categorization system
- ✅ **File Import & Management** - Import, categorize, move, rename, and organize sequence files
- ✅ **Content Viewing** - Real-time display of file contents and project structure
- ✅ **Professional UI** - Intuitive interface with context menus, color coding, and error handling
- ✅ **Analysis Tools** - Modular tool system with category-aware primer overlap analysis
- ✅ **Enhanced File Management** - Right-click operations for comprehensive file control

## Features

### Project Management
- **Create New Projects** - Professional dialog for project setup with name, description, and location
- **Save/Load Projects** - JSON-based persistence with automatic backups
- **Project Validation** - Check file references and get recommendations
- **Change Tracking** - Visual indicators for unsaved changes

### Advanced File Management
- **Flexible Folder Structure** - Create unlimited nested folders to organize your files
- **File Categorization System** - Categorize FASTA files as Oligos, Reference Sequences, or Reference Sequence Lists
- **Visual Color Coding** - Green (Oligos), Blue (Reference Sequence), Purple (Reference Sequence List), Black (Uncategorized)
- **Context Menu Operations** - Right-click files and folders for quick actions:
  - Set file categories
  - Rename files within project
  - Move files between folders
  - Remove files from project (keeps original file on disk)
  - Create subfolders
  - Import files to specific locations
- **File Import** - Import FASTA, FASTQ, text files, and other bioinformatics formats
- **Format Detection** - Automatic detection of file types based on content and extension
- **Enhanced Tooltips** - Detailed file information including category, type, and size

### Analysis Tools
- **Category-Aware Tool System** - Tools automatically filter compatible file categories
- **Primer Overlap Analyzer** - Analyze 3'-end overlaps between primer sequences to predict dimer formation
  - **Selective Input** - Only accepts files categorized as "Oligos"
  - **Risk Assessment** - HIGH/MEDIUM/LOW risk classification
  - **Visual Overlaps** - ASCII diagrams showing primer interactions
  - **Comprehensive Reports** - Detailed text reports and CSV summaries
- **Background Processing** - Tools run in separate threads to maintain UI responsiveness
- **Automated Output Management** - Results saved to disk and automatically imported to project
- **Parameter Validation** - Type checking and range validation for all tool parameters

### User Interface
- **Two-Panel Design** - Project tree on left, content viewer on right
- **Interactive Project Tree** - Real-time display with color-coded files and context menus
- **Smart Menus** - Context-sensitive actions that adapt based on file type and project state
- **Professional Dialogs** - User-friendly forms for all operations
- **Tool Integration** - Access analysis tools through Tools → Analysis menu
- **Enhanced File Display** - Category information, color coding, and detailed tooltips
- **Automatic Refresh** - Project tree updates immediately after tool completion
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
│       ├── file_management_use_cases.py
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

## File Categorization System

### Supported Categories
- **Uncategorized** - Default state for all imported files (Black text)
- **Oligos** - Primer/oligonucleotide sequences for PCR, qPCR, etc. (Green text)
- **Reference Sequence** - Single reference sequences for alignment (Blue text)
- **Reference Sequence List** - Multiple reference sequences (Purple text)

### Setting Categories
1. Right-click any FASTA file in the project tree
2. Select "Set Category" from context menu
3. Choose appropriate category
4. File color updates immediately

### Category Benefits
- **Tool Compatibility** - Tools only show compatible file categories
- **Visual Organization** - Instant visual identification of file purposes
- **Error Prevention** - Prevents using wrong sequence types in analyses

## Analysis Tools

### Primer Overlap Analyzer

Analyzes 3'-end overlaps between primer sequences to predict primer-dimer formation risk.

**Category Requirement:** Only accepts files categorized as "Oligos"

**Features:**
- Configurable overlap length ranges (2-20 bases)
- Mismatch tolerance settings (0-5 mismatches)
- Self-dimer detection option
- Risk level assessment (HIGH/MEDIUM/LOW)
- ASCII visualization of overlaps
- Comprehensive reporting

**Usage:**
1. Import FASTA files containing primer sequences
2. **Categorize files as "Oligos"** using right-click menu
3. Go to **Tools → Analysis → Primer Overlap Analyzer**
4. Select input files (only "Oligos" category files will appear)
5. Configure parameters:
   - Minimum/Maximum overlap length
   - Maximum allowed mismatches  
   - Include self-comparisons
6. Click **Run Tool**
7. View results in generated reports

**Output Files:**
- `primer_overlap_analysis.txt` - Detailed analysis with visualizations
- `primer_overlap_summary.csv` - Spreadsheet-compatible summary
- Both files automatically saved to `project_directory/output/` and imported to project

### Risk Assessment Criteria
- **HIGH Risk**: ≥4 perfect base matches at 3'-ends
- **MEDIUM Risk**: 2-3 perfect matches OR ≥4 matches with 1 mismatch
- **LOW Risk**: All other combinations

## Enhanced File Operations

### Context Menu Operations

**For FASTA Files:**
- **Set Category** - Assign Oligos, Reference Sequence, or Reference Sequence List categories
- **Rename File** - Rename files within the project structure
- **Move to Folder** - Relocate files to different project folders
- **Remove from Project** - Remove file reference from project (keeps original file on disk)

**For Folders:**
- **Create Subfolder** - Add nested organizational folders
- **Import File Here** - Import files directly to specific folders

### File Management Workflow
1. **Import Files** - Use File → Import File or drag files to project tree
2. **Organize Structure** - Create folders to organize your files logically
3. **Categorize FASTA Files** - Right-click to assign appropriate categories
4. **Run Analysis** - Tools will automatically filter compatible files
5. **Manage Results** - Output files appear automatically in Results folder

## Architecture

The application follows **Clean Architecture** principles with clear separation of concerns:

### **Domain Layer** (`domain/`)
- **Core Entities**: `Project`, `Folder`, `FileReference` with file categorization
- **File Categories**: `FileCategory` enum with visual color coding
- **Analysis Tools**: `BaseTool`, `PrimerOverlapTool` with category-aware filtering
- **Business Logic**: File organization, validation, categorization rules
- **Domain Exceptions**: Specific error types for business rule violations

### **Data Layer** (`data/`)
- **ProjectRepository**: JSON persistence with atomic saves and backups
- **FileManager**: Cross-platform file operations and path resolution
- **FormatDetector**: Bioinformatics file format detection and validation

### **Application Layer** (`application/`)
- **ApplicationService**: Central coordinator providing unified API to UI
- **Use Cases**: Individual operations (CreateProject, ImportFile, RunTool, SetFileCategory, etc.)
- **File Management**: Enhanced operations for move, rename, categorize, remove
- **Tool Execution**: Background processing with category-aware file filtering
- **State Management**: Project lifecycle and change tracking

### **UI Layer** (`ui/`)
- **MainWindow**: Primary interface with color-coded project tree and context menus
- **Context Menus**: Right-click operations for files and folders
- **Tool Dialogs**: Professional parameter configuration with category filtering
- **Error Handling**: User-friendly messages and confirmations
- **Visual Feedback**: Color coding, tooltips, and status updates

## Usage Guide

### Creating Your First Project

1. **Launch Oligotools**: Run `python main.py`
2. **New Project**: Go to File → New Project
3. **Fill Project Details**: Enter name, description, and choose save location
4. **Start Organizing**: Create folders using right-click context menus

### Importing and Categorizing Files

1. **Import Files**: Go to File → Import File or right-click folders
2. **Choose Files**: Select your sequence files (FASTA, FASTQ, etc.)
3. **Categorize FASTA Files**: Right-click imported FASTA files
4. **Set Categories**: Choose Oligos, Reference Sequence, or Reference Sequence List
5. **Visual Confirmation**: Files display in appropriate colors

### Running Analysis Tools

1. **Prepare Files**: Ensure FASTA files are properly categorized
2. **Launch Tool**: Go to Tools → Analysis → Primer Overlap Analyzer
3. **Automatic Filtering**: Only compatible files (e.g., "Oligos") will appear
4. **Configure Analysis**: Set parameters and select files
5. **Run Analysis**: Click "Run Tool" and wait for completion
6. **View Results**: Check generated reports in project's Results folder

### Advanced File Management

- **Move Files**: Right-click → Move to Folder → Select destination
- **Rename Files**: Right-click → Rename File → Enter new name
- **Remove from Project**: Right-click → Remove from Project (keeps original file)
- **Create Organization**: Right-click folders → Create Subfolder
- **Direct Import**: Right-click folders → Import File Here

## File Format Support

The application automatically detects and supports:

- **FASTA** (`.fasta`, `.fa`, `.fas`) - Sequence files with categorization support
- **FASTQ** (`.fastq`, `.fq`) - Sequencing data with quality scores  
- **GenBank** (`.gb`, `.gbk`) - Annotated sequence files
- **Text Files** (`.txt`) - Analysis results and documentation
- **CSV/TSV** (`.csv`, `.tsv`) - Tabular data
- **Excel** (`.xlsx`, `.xls`) - Spreadsheet data

## Project File Structure

Projects are saved as `.oligoproj` files containing:
- Project metadata (name, description, dates)
- Complete folder hierarchy with file categories
- File references with relative paths and categorization
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
3. **Set Category Requirements**: Specify required file categories in `get_input_requirements()`
4. **Implement Logic**: Add analysis logic in `execute()` method
5. **Add Use Case**: Create tool-specific execution logic in application layer
6. **Create UI Dialog**: Extend `BaseToolDialog` for parameter configuration
7. **Register Tool**: Add to `AVAILABLE_TOOLS` registry

### Adding New File Categories

To add new file categories:

1. **Extend FileCategory Enum**: Add new category to `domain/entities.py`
2. **Add Display Properties**: Define display name and color in enum methods
3. **Update Tools**: Specify category requirements in tool definitions
4. **Test Integration**: Ensure UI properly displays new categories

### Testing the Complete Workflow

The `example_usage.py` script demonstrates all functionality:
- Creates a project programmatically
- Sets up folder structure
- Imports sample files
- Performs various operations
- Shows validation and statistics

### Architecture Benefits

- **Modular Design**: Each layer has clear responsibilities
- **Category System**: Prevents incompatible file usage in tools
- **Tool Extensibility**: Easy to add new analysis capabilities with category awareness
- **Enhanced UX**: Right-click operations and visual feedback improve usability
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
- **Category Issues**: Ensure FASTA files are properly categorized before running tools
- **Tool Compatibility**: Only files with compatible categories will appear in tool dialogs
- **Permission Errors**: Ensure write access to project directory and output folder
- **Context Menu Not Working**: Ensure you're right-clicking directly on file/folder items

### Getting Help

- Check the application's built-in validation (Tools → Validate Project)
- Review error messages in dialog boxes
- Verify file categories match tool requirements
- Ensure file paths are accessible and files haven't been moved
- Check tool parameter ranges and requirements
- Use right-click context menus for file management operations

---

**Oligotools** - Complete bioinformatics project management and analysis platform with advanced file categorization and management capabilities.