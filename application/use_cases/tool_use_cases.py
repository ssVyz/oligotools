"""
Tool execution use cases for Oligotools
Handles running analysis tools and managing their outputs.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from domain.entities import Project, FileReference
from domain.tools import BaseTool, ToolResult, get_available_tools, get_tool_by_id
from domain import ToolError, ToolParameterError
from data.exceptions import DataError
from ..base_use_case import BaseUseCase
from ..exceptions import UseCaseError, ValidationError


@dataclass
class RunToolRequest:
    """Request to run an analysis tool."""
    project: Project
    tool_id: str
    input_files: List[FileReference]
    parameters: Dict[str, Any]
    output_to_project: bool = True  # Whether to import results back to project


@dataclass
class RunToolResponse:
    """Response from running a tool."""
    tool_result: ToolResult
    output_files_created: List[str]
    imported_files: List[FileReference] = None
    success_message: str = ""


@dataclass
class GetAvailableToolsRequest:
    """Request to get available tools."""
    project: Optional[Project] = None


@dataclass
class GetAvailableToolsResponse:
    """Response with available tools."""
    tools: Dict[str, Dict[str, Any]]


@dataclass
class GetProjectFastaFilesRequest:
    """Request to get FASTA files from project."""
    project: Project
    selected_files: Optional[List[str]] = None  # Pre-selected file names


@dataclass
class GetProjectFastaFilesResponse:
    """Response with project FASTA files."""
    fasta_files: List[FileReference]
    preselected_files: List[FileReference]


class RunToolUseCase(BaseUseCase[RunToolRequest, RunToolResponse]):
    """Use case for running analysis tools."""

    def validate_request(self, request: RunToolRequest) -> None:
        """Validate tool execution request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

        if not request.tool_id:
            raise ValidationError("Tool ID cannot be empty")

        if not request.input_files:
            raise ValidationError("Input files list cannot be empty")

        # Check if tool exists
        tool = get_tool_by_id(request.tool_id)
        if not tool:
            raise ValidationError(f"Tool '{request.tool_id}' not found")

    def execute(self, request: RunToolRequest) -> RunToolResponse:
        """Execute the analysis tool."""
        try:
            # Get tool instance
            tool = get_tool_by_id(request.tool_id)
            if not tool:
                raise UseCaseError(f"Tool '{request.tool_id}' not found")

            # Create output directory next to project file
            project_dir = Path(request.project.project_file_path).parent
            output_dir = project_dir / "output"
            output_dir.mkdir(exist_ok=True)

            # Create tool-specific output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tool_output_dir = output_dir / f"{tool.tool_id}_{timestamp}"
            tool_output_dir.mkdir(exist_ok=True)

            # Execute tool with file path resolution
            tool_result = self._execute_tool_with_resolved_paths(
                tool, request.input_files, request.parameters, str(tool_output_dir)
            )

            output_files_created = tool_result.output_files.copy()
            imported_files = []

            # Import results back to project if requested
            if request.output_to_project and tool_result.success:
                imported_files = self._import_results_to_project(
                    request.project, tool_result, str(tool_output_dir)
                )

            success_message = f"Tool '{tool.tool_name}' completed successfully"
            if tool_result.execution_time_seconds:
                success_message += f" in {tool_result.execution_time_seconds:.2f} seconds"

            return RunToolResponse(
                tool_result=tool_result,
                output_files_created=output_files_created,
                imported_files=imported_files,
                success_message=success_message
            )

        except ToolError as e:
            raise UseCaseError(f"Tool execution error: {e}")
        except DataError as e:
            raise UseCaseError(f"Data error: {e}")
        except Exception as e:
            raise UseCaseError(f"Unexpected error running tool: {e}")

    def _execute_tool_with_resolved_paths(self, tool: BaseTool, input_files: List[FileReference],
                                          parameters: Dict[str, Any], output_dir: str) -> ToolResult:
        """Execute tool with resolved file paths."""
        # For primer overlap tool, implement the actual analysis logic here
        if isinstance(tool, type(get_tool_by_id('primer_overlap'))):
            return self._execute_primer_overlap_tool(tool, input_files, parameters, output_dir)
        else:
            # For other tools, use generic execution
            return tool.execute(input_files, parameters, output_dir)

    def _execute_primer_overlap_tool(self, tool: BaseTool, input_files: List[FileReference],
                                     parameters: Dict[str, Any], output_dir: str) -> ToolResult:
        """Execute primer overlap analysis with actual BioPython implementation."""
        result = ToolResult(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            input_files=[f.name for f in input_files],
            parameters=parameters
        )

        try:
            # Import BioPython
            try:
                from Bio import SeqIO
                from Bio.Seq import Seq
            except ImportError:
                raise ToolError("BioPython is required for primer analysis. Please install with: pip install biopython")

            # Validate inputs and parameters
            tool.validate_inputs(input_files)
            validated_params = tool.validate_parameters(parameters)
            result.parameters = validated_params

            # Load sequences from all input files
            sequences = []
            for file_ref in input_files:
                try:
                    # Resolve file path through file manager
                    file_path = self.project_repository.file_manager.resolve_relative_path(file_ref.relative_path)
                    file_sequences = list(SeqIO.parse(file_path, "fasta"))
                    sequences.extend(file_sequences)
                    result.add_warning(f"Loaded {len(file_sequences)} sequences from {file_ref.name}")
                except Exception as e:
                    result.add_warning(f"Could not load sequences from {file_ref.name}: {str(e)}")

            if not sequences:
                raise ToolError("No valid sequences could be loaded from input files")

            # Run the primer overlap analysis
            analysis_results = self._run_primer_overlap_analysis(sequences, validated_params)

            # Generate output files
            output_files = self._generate_primer_overlap_outputs(
                analysis_results, sequences, validated_params, output_dir
            )

            result.output_files = output_files
            result.summary_statistics = {
                'total_sequences': len(sequences),
                'total_overlaps_found': len(analysis_results['overlaps']),
                'high_risk_overlaps': len([r for r in analysis_results['overlaps'] if r['risk_level'] == 'HIGH']),
                'analysis_parameters': validated_params
            }
            result.detailed_results = analysis_results['overlaps']

            result.mark_completed(success=True)

        except Exception as e:
            result.mark_completed(success=False, error_message=str(e))

        return result

    def _run_primer_overlap_analysis(self, sequences: List, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run the core primer overlap analysis (adapted from standalone script)."""
        min_overlap = parameters['min_overlap']
        max_overlap = parameters['max_overlap']
        max_mismatches = parameters['max_mismatches']
        include_self = parameters['include_self_comparison']

        overlaps = []

        # Analysis loop - adapted from standalone script
        for overlap_length in range(max_overlap, min_overlap - 1, -1):
            for mismatches in range(max_mismatches + 1):
                for i in range(len(sequences)):
                    start_j = i if include_self else i + 1
                    for j in range(start_j, len(sequences)):

                        # Get 3' ends
                        primer1_3end = self._get_last_n_bases(sequences[i], overlap_length)
                        primer2_3end_rc = self._get_last_n_bases_rc(sequences[j], overlap_length)

                        # Count mismatches
                        actual_mismatches = self._count_mismatches(primer1_3end, primer2_3end_rc)

                        if actual_mismatches == mismatches:
                            risk_level = self._get_risk_level(overlap_length, mismatches)
                            visualization = self._visualize_overlap(sequences[i], sequences[j], overlap_length)

                            overlap_result = {
                                'overlap_length': overlap_length,
                                'mismatches': mismatches,
                                'primer1_id': sequences[i].id,
                                'primer2_id': sequences[j].id,
                                'primer1_seq': str(sequences[i].seq),
                                'primer2_seq': str(sequences[j].seq),
                                'risk_level': risk_level,
                                'visualization': visualization,
                                'primer1_3end': primer1_3end,
                                'primer2_3end_rc': primer2_3end_rc
                            }

                            overlaps.append(overlap_result)

        return {
            'overlaps': overlaps,
            'total_sequences': len(sequences),
            'parameters': parameters
        }

    def _generate_primer_overlap_outputs(self, analysis_results: Dict[str, Any],
                                         sequences: List, parameters: Dict[str, Any],
                                         output_dir: str) -> List[str]:
        """Generate output files for primer overlap analysis."""
        output_files = []

        # Generate detailed text report
        report_file = os.path.join(output_dir, "primer_overlap_analysis.txt")
        with open(report_file, 'w') as f:
            f.write("qPCR Primer Compatibility Analysis Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total sequences: {len(sequences)}\n")
            f.write(f"Total overlaps found: {len(analysis_results['overlaps'])}\n")
            f.write(f"Parameters: {parameters}\n\n")

            # Group by overlap length and mismatches
            overlaps = analysis_results['overlaps']
            overlaps_sorted = sorted(overlaps, key=lambda x: (x['overlap_length'], x['mismatches']), reverse=True)

            current_overlap = None
            current_mismatches = None

            for result in overlaps_sorted:
                if (result['overlap_length'] != current_overlap or
                        result['mismatches'] != current_mismatches):
                    current_overlap = result['overlap_length']
                    current_mismatches = result['mismatches']

                    f.write(f"\n{'-' * 60}\n")
                    f.write(f"{current_overlap}-base overlaps with {current_mismatches} mismatch(es)\n")
                    f.write(f"{'-' * 60}\n\n")

                f.write(f"Overlap: {result['primer1_id']} vs {result['primer2_id']}\n")
                f.write(f"Risk Level: {result['risk_level']}\n")
                f.write(f"{result['visualization']}\n")

        output_files.append(report_file)

        # Generate CSV summary
        csv_file = os.path.join(output_dir, "primer_overlap_summary.csv")
        with open(csv_file, 'w') as f:
            f.write("Overlap_Length,Mismatches,Primer1_ID,Primer2_ID,Risk_Level,Primer1_3end,Primer2_3end_RC\n")
            for result in analysis_results['overlaps']:
                f.write(
                    f"{result['overlap_length']},{result['mismatches']},{result['primer1_id']},{result['primer2_id']},{result['risk_level']},{result['primer1_3end']},{result['primer2_3end_rc']}\n")

        output_files.append(csv_file)

        return output_files

    def _import_results_to_project(self, project: Project, tool_result: ToolResult,
                                   output_dir: str) -> List[FileReference]:
        """Import tool results back into the project."""
        imported_files = []

        # Ensure "Results" folder exists in project
        try:
            results_folder = project.get_folder_by_path("Root/Results")
        except:
            project.create_folder_at_path("Root", "Results")
            results_folder = project.get_folder_by_path("Root/Results")

        # Import each output file
        for output_file_path in tool_result.output_files:
            try:
                file_ref = self.project_repository.import_file_to_project(
                    project=project,
                    source_file_path=output_file_path,
                    target_folder_path="Root/Results",
                    copy_file=False  # Don't copy since it's already in our output dir
                )
                imported_files.append(file_ref)
            except Exception as e:
                tool_result.add_warning(f"Could not import {output_file_path}: {str(e)}")

        return imported_files

    # Helper methods adapted from standalone script
    def _get_last_n_bases(self, seq_record, n: int) -> str:
        """Get last n bases from 3' end."""
        return str(seq_record.seq[-n:]).upper()

    def _get_last_n_bases_rc(self, seq_record, n: int) -> str:
        """Get last n bases from 3' end and return reverse complement."""
        from Bio.Seq import Seq
        trimmed = seq_record.seq[-n:].upper()
        return str(trimmed.reverse_complement())

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

    def _visualize_overlap(self, seq1, seq2, overlap_length: int) -> str:
        """Create ASCII visualization of overlap."""
        primer1_full = str(seq1.seq)
        primer2_full = str(seq2.seq)

        # Calculate offset for primer2 alignment
        p2_offset = len(primer1_full) - overlap_length

        # Get the overlapping regions for comparison
        primer1_3end = self._get_last_n_bases(seq1, overlap_length)
        primer2_3end_rc = self._get_last_n_bases_rc(seq2, overlap_length)

        # Create alignment visualization
        lines = []
        lines.append(primer1_full)

        # Create match/mismatch line with proper offset
        match_line = " " * p2_offset
        for i, (a, b) in enumerate(zip(primer1_3end, primer2_3end_rc)):
            if a == b:
                match_line += "|"
            else:
                match_line += " "  # Space for mismatch

        lines.append(match_line)

        # Create primer2 line (reversed) with proper offset
        primer2_line = " " * p2_offset + primer2_full[::-1]
        lines.append(primer2_line)
        lines.append("")

        return "\n".join(lines)


class GetAvailableToolsUseCase(BaseUseCase[GetAvailableToolsRequest, GetAvailableToolsResponse]):
    """Use case for getting available analysis tools."""

    def execute(self, request: GetAvailableToolsRequest) -> GetAvailableToolsResponse:
        """Get list of available tools."""
        tools = get_available_tools()

        tools_info = {}
        for tool_id, tool in tools.items():
            tools_info[tool_id] = {
                'name': tool.tool_name,
                'description': tool.tool_description,
                'version': tool.tool_version,
                'parameters': [
                    {
                        'name': p.name,
                        'display_name': p.display_name,
                        'type': p.parameter_type,
                        'default_value': p.default_value,
                        'description': p.description
                    }
                    for p in tool.get_parameters()
                ],
                'input_requirements': [
                    {
                        'name': req.name,
                        'description': req.description,
                        'file_types': req.file_types,
                        'min_files': req.min_files,
                        'max_files': req.max_files
                    }
                    for req in tool.get_input_requirements()
                ]
            }

        return GetAvailableToolsResponse(tools=tools_info)


class GetProjectFastaFilesUseCase(BaseUseCase[GetProjectFastaFilesRequest, GetProjectFastaFilesResponse]):
    """Use case for getting FASTA files from a project."""

    def validate_request(self, request: GetProjectFastaFilesRequest) -> None:
        """Validate request."""
        super().validate_request(request)

        if not request.project:
            raise ValidationError("Project cannot be None")

    def execute(self, request: GetProjectFastaFilesRequest) -> GetProjectFastaFilesResponse:
        """Get FASTA files from project."""
        # Get all files from project
        all_files = request.project.get_all_file_references()

        # Filter for FASTA files
        fasta_extensions = ['fasta', 'fa', 'fas', 'fna', 'ffn', 'faa', 'frn']
        fasta_files = [
            file_ref for file_ref in all_files
            if file_ref.file_type.lower() in fasta_extensions
        ]

        # Find preselected files
        preselected_files = []
        if request.selected_files:
            selected_names = set(request.selected_files)
            preselected_files = [
                file_ref for file_ref in fasta_files
                if file_ref.name in selected_names
            ]

        return GetProjectFastaFilesResponse(
            fasta_files=fasta_files,
            preselected_files=preselected_files
        )