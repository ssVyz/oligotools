"""
File Format Detection for Oligotools
Detects and validates common bioinformatics file formats.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List


class FormatDetector:
    """Detects and validates bioinformatics file formats."""

    # Common bioinformatics file extensions and their types
    KNOWN_EXTENSIONS = {
        '.fasta': 'fasta',
        '.fa': 'fasta',
        '.fas': 'fasta',
        '.fna': 'fasta',
        '.ffn': 'fasta',
        '.faa': 'fasta',
        '.frn': 'fasta',
        '.fastq': 'fastq',
        '.fq': 'fastq',
        '.txt': 'text',
        '.csv': 'csv',
        '.tsv': 'tsv',
        '.tab': 'tab',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.json': 'json',
        '.xml': 'xml',
        '.gb': 'genbank',
        '.gbk': 'genbank',
        '.embl': 'embl',
        '.aln': 'alignment',
        '.phy': 'phylip',
        '.nex': 'nexus',
        '.tre': 'newick'
    }

    @classmethod
    def detect_format_by_extension(cls, filename: str) -> str:
        """
        Detect file format based on file extension.

        Args:
            filename: Name of the file

        Returns:
            Detected format string, or 'unknown' if not recognized
        """
        extension = Path(filename).suffix.lower()
        return cls.KNOWN_EXTENSIONS.get(extension, 'unknown')

    @classmethod
    def detect_format_by_content(cls, file_path: str, max_lines: int = 10) -> Dict[str, Any]:
        """
        Detect file format by examining file content.

        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to examine

        Returns:
            Dictionary with format detection results
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline().strip() for _ in range(max_lines)]
                lines = [line for line in lines if line]  # Remove empty lines
        except Exception as e:
            return {
                'format': 'unknown',
                'confidence': 0.0,
                'error': str(e),
                'details': {}
            }

        if not lines:
            return {
                'format': 'empty',
                'confidence': 1.0,
                'details': {'reason': 'File is empty or contains only whitespace'}
            }

        # Check for FASTA format
        fasta_result = cls._check_fasta_format(lines)
        if fasta_result['confidence'] > 0.8:
            return fasta_result

        # Check for FASTQ format
        fastq_result = cls._check_fastq_format(lines)
        if fastq_result['confidence'] > 0.8:
            return fastq_result

        # Check for CSV/TSV format
        csv_result = cls._check_csv_format(lines)
        if csv_result['confidence'] > 0.7:
            return csv_result

        # Check for GenBank format
        genbank_result = cls._check_genbank_format(lines)
        if genbank_result['confidence'] > 0.8:
            return genbank_result

        # Default to text format
        return {
            'format': 'text',
            'confidence': 0.3,
            'details': {'reason': 'No specific format detected, treating as plain text'}
        }

    @classmethod
    def _check_fasta_format(cls, lines: List[str]) -> Dict[str, Any]:
        """Check if content matches FASTA format."""
        if not lines:
            return {'format': 'fasta', 'confidence': 0.0}

        # FASTA files start with > followed by sequence identifier
        if not lines[0].startswith('>'):
            return {'format': 'fasta', 'confidence': 0.0}

        sequence_lines = 0
        header_lines = 0
        invalid_chars = 0

        for line in lines[1:]:  # Skip first header line
            if line.startswith('>'):
                header_lines += 1
            elif line:
                sequence_lines += 1
                # Check for valid nucleotide/protein characters
                valid_chars = set('ATCGNUKSYMWRBDHV-atcgnuksymwrbdhv')  # DNA/RNA/Protein + ambiguous
                invalid_chars += sum(1 for char in line if char not in valid_chars)

        # Calculate confidence based on format compliance
        confidence = 0.9  # Start high if header format is correct

        if sequence_lines == 0:
            confidence *= 0.5  # Reduce if no sequence data

        if invalid_chars > (sequence_lines * 5):  # Allow some invalid chars
            confidence *= 0.3

        return {
            'format': 'fasta',
            'confidence': confidence,
            'details': {
                'header_lines': header_lines + 1,  # Include first line
                'sequence_lines': sequence_lines,
                'invalid_chars': invalid_chars
            }
        }

    @classmethod
    def _check_fastq_format(cls, lines: List[str]) -> Dict[str, Any]:
        """Check if content matches FASTQ format."""
        if len(lines) < 4:
            return {'format': 'fastq', 'confidence': 0.0}

        # FASTQ has 4-line repeating pattern: @header, sequence, +, quality
        if not lines[0].startswith('@'):
            return {'format': 'fastq', 'confidence': 0.0}

        confidence = 0.8

        # Check if we have the + line in the right position
        if len(lines) > 2 and not lines[2].startswith('+'):
            confidence *= 0.3

        # Check sequence and quality line lengths match (if we have both)
        if len(lines) >= 4:
            seq_length = len(lines[1])
            qual_length = len(lines[3])
            if seq_length != qual_length:
                confidence *= 0.5

        return {
            'format': 'fastq',
            'confidence': confidence,
            'details': {
                'pattern_match': lines[0].startswith('@') and (len(lines) < 3 or lines[2].startswith('+')),
                'examined_lines': len(lines)
            }
        }

    @classmethod
    def _check_csv_format(cls, lines: List[str]) -> Dict[str, Any]:
        """Check if content matches CSV/TSV format."""
        if not lines:
            return {'format': 'csv', 'confidence': 0.0}

        # Check for common separators
        separators = [',', '\t', ';', '|']
        best_separator = None
        best_score = 0

        for sep in separators:
            if sep in lines[0]:
                # Count columns consistency across lines
                first_cols = len(lines[0].split(sep))
                consistent_cols = sum(1 for line in lines[:5] if len(line.split(sep)) == first_cols)
                score = consistent_cols / min(len(lines), 5)

                if score > best_score:
                    best_score = score
                    best_separator = sep

        if best_separator:
            format_name = 'tsv' if best_separator == '\t' else 'csv'
            return {
                'format': format_name,
                'confidence': best_score,
                'details': {
                    'separator': best_separator,
                    'columns': len(lines[0].split(best_separator)),
                    'consistency_score': best_score
                }
            }

        return {'format': 'csv', 'confidence': 0.0}

    @classmethod
    def _check_genbank_format(cls, lines: List[str]) -> Dict[str, Any]:
        """Check if content matches GenBank format."""
        if not lines:
            return {'format': 'genbank', 'confidence': 0.0}

        # GenBank files typically start with LOCUS
        if not lines[0].startswith('LOCUS'):
            return {'format': 'genbank', 'confidence': 0.0}

        # Look for other GenBank keywords
        genbank_keywords = ['DEFINITION', 'ACCESSION', 'VERSION', 'SOURCE', 'FEATURES', 'ORIGIN']
        found_keywords = sum(1 for line in lines if any(line.startswith(kw) for kw in genbank_keywords))

        confidence = min(0.9, 0.3 + (found_keywords * 0.1))

        return {
            'format': 'genbank',
            'confidence': confidence,
            'details': {
                'found_keywords': found_keywords,
                'total_keywords': len(genbank_keywords)
            }
        }

    @classmethod
    def get_format_info(self, format_name: str) -> Dict[str, Any]:
        """
        Get information about a specific file format.

        Args:
            format_name: Name of the format

        Returns:
            Dictionary with format information
        """
        format_info = {
            'fasta': {
                'description': 'FASTA sequence format',
                'extensions': ['.fasta', '.fa', '.fas', '.fna', '.ffn', '.faa'],
                'type': 'sequence',
                'supports_multiple': True,
                'common_use': 'Storing nucleotide or protein sequences'
            },
            'fastq': {
                'description': 'FASTQ sequence format with quality scores',
                'extensions': ['.fastq', '.fq'],
                'type': 'sequence',
                'supports_multiple': True,
                'common_use': 'Raw sequencing data with quality information'
            },
            'genbank': {
                'description': 'GenBank flat file format',
                'extensions': ['.gb', '.gbk'],
                'type': 'annotated_sequence',
                'supports_multiple': True,
                'common_use': 'Annotated sequences with features and metadata'
            },
            'csv': {
                'description': 'Comma-separated values',
                'extensions': ['.csv'],
                'type': 'tabular',
                'supports_multiple': False,
                'common_use': 'Tabular data, analysis results'
            },
            'tsv': {
                'description': 'Tab-separated values',
                'extensions': ['.tsv', '.tab'],
                'type': 'tabular',
                'supports_multiple': False,
                'common_use': 'Tabular data, analysis results'
            }
        }

        return format_info.get(format_name, {
            'description': f'Unknown format: {format_name}',
            'extensions': [],
            'type': 'unknown',
            'supports_multiple': False,
            'common_use': 'Unknown file type'
        })