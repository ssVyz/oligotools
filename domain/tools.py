"""
Domain layer for Oligotools analysis tools
Contains base classes and specific tool implementations for sequence analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from .entities import FileReference
from .exceptions import DomainError


class ToolError(DomainError):
    """Raised when tool execution encounters errors."""
    pass


class ToolParameterError(DomainError):
    """Raised when tool parameters are invalid."""
    pass


@dataclass
class ToolParameter:
    """Represents a configurable parameter for a tool."""
    name: str
    display_name: str
    parameter_type: str  # 'int', 'float', 'str', 'bool', 'choice'
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[str]] = None
    description: str = ""
    required: bool = True

    def validate_value(self, value: Any) -> Any:
        """Validate and convert parameter value."""
        if self.required and value is None:
            raise ToolParameterError(f"Parameter '{self.name}' is required")

        if value is None:
            return self.default_value

        # Type conversion and validation
        if self.parameter_type == 'int':
            try:
                int_value = int(value)
                if self.min_value is not None and int_value < self.min_value:
                    raise ToolParameterError(f"Parameter '{self.name}' must be >= {self.min_value}")
                if self.max_value is not None and int_value > self.max_value:
                    raise ToolParameterError(f"Parameter '{self.name}' must be <= {self.max_value}")
                return int_value
            except (ValueError, TypeError):
                raise ToolParameterError(f"Parameter '{self.name}' must be an integer")

        elif self.parameter_type == 'float':
            try:
                float_value = float(value)
                if self.min_value is not None and float_value < self.min_value:
                    raise ToolParameterError(f"Parameter '{self.name}' must be >= {self.min_value}")
                if self.max_value is not None and float_value > self.max_value:
                    raise ToolParameterError(f"Parameter '{self.name}' must be <= {self.max_value}")
                return float_value
            except (ValueError, TypeError):
                raise ToolParameterError(f"Parameter '{self.name}' must be a number")

        elif self.parameter_type == 'bool':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)

        elif self.parameter_type == 'choice':
            if self.choices and value not in self.choices:
                raise ToolParameterError(f"Parameter '{self.name}' must be one of: {', '.join(self.choices)}")
            return value

        else:  # string or other
            return str(value)


@dataclass
class ToolResult:
    """Contains the results of tool execution."""
    tool_id: str
    tool_name: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None

    # Input information
    input_files: List[str] = field(default_factory=list)  # File names/IDs
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Output information
    output_files: List[str] = field(default_factory=list)  # Generated file paths
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)

    # Execution metadata
    execution_time_seconds: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def mark_completed(self, success: bool = True, error_message: Optional[str] = None):
        """Mark the tool execution as completed."""
        self.end_time = datetime.now()
        self.success = success
        self.error_message = error_message
        if self.start_time and self.end_time:
            self.execution_time_seconds = (self.end_time - self.start_time).total_seconds()

    def add_warning(self, warning: str):
        """Add a warning message to the results."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'tool_id': self.tool_id,
            'tool_name': self.tool_name,
            'execution_id': self.execution_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'success': self.success,
            'error_message': self.error_message,
            'input_files': self.input_files,
            'parameters': self.parameters,
            'output_files': self.output_files,
            'summary_statistics': self.summary_statistics,
            'detailed_results': self.detailed_results,
            'execution_time_seconds': self.execution_time_seconds,
            'warnings': self.warnings
        }


@dataclass
class ToolInputRequirement:
    """Defines input requirements for a tool."""
    name: str
    description: str
    file_types: List[str]  # e.g., ['fasta', 'fastq']
    min_files: int = 1
    max_files: Optional[int] = None
    required: bool = True


class BaseTool(ABC):
    """Abstract base class for all analysis tools."""

    def __init__(self):
        self.tool_id = self.__class__.__name__
        self.parameters = {}

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Human-readable name of the tool."""
        pass

    @property
    @abstractmethod
    def tool_description(self) -> str:
        """Description of what the tool does."""
        pass

    @property
    @abstractmethod
    def tool_version(self) -> str:
        """Version of the tool implementation."""
        pass

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Get list of configurable parameters for this tool."""
        pass

    @abstractmethod
    def get_input_requirements(self) -> List[ToolInputRequirement]:
        """Get input file requirements for this tool."""
        pass

    @abstractmethod
    def execute(self, input_files: List[FileReference],
                parameters: Dict[str, Any],
                output_directory: str) -> ToolResult:
        """
        Execute the tool with given inputs and parameters.

        Args:
            input_files: List of FileReference objects to analyze
            parameters: Dictionary of parameter values
            output_directory: Directory where output files should be created

        Returns:
            ToolResult containing execution results and output information
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parameters."""
        tool_params = {p.name: p for p in self.get_parameters()}
        validated = {}

        for param_name, param_def in tool_params.items():
            value = parameters.get(param_name)
            validated[param_name] = param_def.validate_value(value)

        return validated

    def validate_inputs(self, input_files: List[FileReference]) -> None:
        """Validate input files meet tool requirements."""
        requirements = self.get_input_requirements()

        for req in requirements:
            if req.required:
                # Find files matching this requirement
                matching_files = []
                for file_ref in input_files:
                    if file_ref.file_type in req.file_types:
                        matching_files.append(file_ref)

                if len(matching_files) < req.min_files:
                    raise ToolError(
                        f"Tool requires at least {req.min_files} {'/'.join(req.file_types)} files for '{req.name}', but only {len(matching_files)} provided")

                if req.max_files and len(matching_files) > req.max_files:
                    raise ToolError(
                        f"Tool accepts at most {req.max_files} {'/'.join(req.file_types)} files for '{req.name}', but {len(matching_files)} provided")


class PrimerOverlapTool(BaseTool):
    """Tool for analyzing primer 3'-end overlaps to predict dimer formation."""

    @property
    def tool_name(self) -> str:
        return "Primer Overlap Analyzer"

    @property
    def tool_description(self) -> str:
        return "Analyzes 3'-end overlaps between primer sequences to predict primer-dimer formation risk"

    @property
    def tool_version(self) -> str:
        return "1.0.0"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="min_overlap",
                display_name="Minimum Overlap Length",
                parameter_type="int",
                default_value=3,
                min_value=2,
                max_value=15,
                description="Minimum number of bases to consider for overlap analysis"
            ),
            ToolParameter(
                name="max_overlap",
                display_name="Maximum Overlap Length",
                parameter_type="int",
                default_value=10,
                min_value=3,
                max_value=20,
                description="Maximum number of bases to consider for overlap analysis"
            ),
            ToolParameter(
                name="max_mismatches",
                display_name="Maximum Mismatches",
                parameter_type="int",
                default_value=1,
                min_value=0,
                max_value=5,
                description="Maximum number of mismatches allowed in overlaps (0 = perfect matches only)"
            ),
            ToolParameter(
                name="include_self_comparison",
                display_name="Include Self-Comparisons",
                parameter_type="bool",
                default_value=True,
                description="Include comparisons of each primer with itself (self-dimer detection)"
            )
        ]

    def get_input_requirements(self) -> List[ToolInputRequirement]:
        return [
            ToolInputRequirement(
                name="primers",
                description="FASTA files containing primer sequences",
                file_types=["fasta", "fa", "fas"],
                min_files=1,
                max_files=None,
                required=True
            )
        ]

    def execute(self, input_files: List[FileReference],
                parameters: Dict[str, Any],
                output_directory: str) -> ToolResult:
        """Execute primer overlap analysis."""
        # Initialize result
        result = ToolResult(
            tool_id=self.tool_id,
            tool_name=self.tool_name,
            input_files=[f.name for f in input_files],
            parameters=parameters
        )

        try:
            # Validate inputs and parameters
            self.validate_inputs(input_files)
            validated_params = self.validate_parameters(parameters)
            result.parameters = validated_params

            # Import BioPython here so it's only required when tools are used
            try:
                from Bio import SeqIO
                from Bio.Seq import Seq
            except ImportError:
                raise ToolError("BioPython is required for primer analysis. Please install with: pip install biopython")

            # Load sequences from all input files
            sequences = []
            for file_ref in input_files:
                try:
                    # This will be handled by the application layer to resolve paths
                    file_path = file_ref.relative_path  # Placeholder - app layer will resolve
                    # For now, we'll pass the path info and let the application layer handle file access
                    sequences.append({
                        'file_ref': file_ref,
                        'file_path': file_path
                    })
                except Exception as e:
                    result.add_warning(f"Could not load sequences from {file_ref.name}: {str(e)}")

            if not sequences:
                raise ToolError("No valid sequences could be loaded from input files")

            # Store sequence info for application layer to handle
            # The actual BioPython processing will be done in the application layer
            result.detailed_results = sequences
            result.summary_statistics = {
                'input_files_count': len(input_files),
                'parameters': validated_params
            }

            result.mark_completed(success=True)

        except Exception as e:
            result.mark_completed(success=False, error_message=str(e))

        return result

    def _analyze_sequences(self, sequences: List, parameters: Dict[str, Any],
                           output_directory: str) -> Dict[str, Any]:
        """
        Core analysis logic - this will be moved to application layer.
        Keeping this as a placeholder for the actual BioPython analysis.
        """
        # This method contains the core analysis logic from the standalone script
        # It will be implemented in the application layer to handle file I/O
        pass

    def _count_mismatches(self, seq1: str, seq2: str) -> int:
        """Count mismatches between two sequences of equal length."""
        return sum(1 for a, b in zip(seq1, seq2) if a != b)

    def _get_risk_level(self, overlap_length: int, mismatches: int) -> str:
        """Determine risk level based on overlap length and mismatches."""
        if mismatches == 0:
            if overlap_length >= 4:
                return "HIGH"
            elif overlap_length >= 2:
                return "MEDIUM"
            else:
                return "LOW"
        elif mismatches == 1 and overlap_length >= 4:
            return "MEDIUM"
        else:
            return "LOW"


# Tool registry for easy discovery
AVAILABLE_TOOLS = {
    'primer_overlap': PrimerOverlapTool
}


def get_available_tools() -> Dict[str, BaseTool]:
    """Get dictionary of all available tools."""
    return {key: tool_class() for key, tool_class in AVAILABLE_TOOLS.items()}


def get_tool_by_id(tool_id: str) -> Optional[BaseTool]:
    """Get a tool instance by its ID."""
    tool_class = AVAILABLE_TOOLS.get(tool_id)
    if tool_class:
        return tool_class()
    return None