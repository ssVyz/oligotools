"""
Example usage of the Oligotools Application Layer
Demonstrates how to use the application service for common operations.
"""

import os
import tempfile
from pathlib import Path

from application import ApplicationService


def demo_project_workflow():
    """Demonstrate a complete project workflow."""
    print("=== Oligotools Application Layer Demo ===\n")

    # Initialize the application service
    app = ApplicationService()

    # Create a temporary directory for our demo
    with tempfile.TemporaryDirectory() as temp_dir:
        project_file_path = os.path.join(temp_dir, "demo_project.oligoproj")

        print("1. Creating new project...")
        result = app.create_new_project(
            project_name="PCR Analysis Demo",
            project_file_path=project_file_path,
            description="Demo project showing application layer functionality"
        )

        if result.success:
            print(f"✓ Project created: {result.data.success_message}")
            print(f"  Project file: {result.data.project_file_path}")
        else:
            print(f"✗ Failed to create project: {result.error}")
            return

        print(f"\n2. Project status:")
        status = app.get_application_status()
        print(f"  Has project: {status['has_project']}")
        print(f"  Project name: {status.get('project_name', 'N/A')}")
        print(f"  Has unsaved changes: {status['has_unsaved_changes']}")

        print(f"\n3. Creating folder structure...")
        folders_to_create = [
            ("Root", "Sequences"),
            ("Root/Sequences", "Primers"),
            ("Root/Sequences", "References"),
            ("Root", "Results"),
            ("Root/Results", "BLAST_Output")
        ]

        for parent_path, folder_name in folders_to_create:
            result = app.create_folder(parent_path, folder_name)
            if result.success:
                print(f"  ✓ Created: {result.data.folder_path}")
            else:
                print(f"  ✗ Failed to create {folder_name}: {result.error}")

        print(f"\n4. Creating sample files...")
        # Create some sample files for demonstration
        sample_files = [
            ("forward_primers.fasta", ">Primer1\nATCGATCGATCG\n>Primer2\nGCTAGCTAGCTA"),
            ("reverse_primers.fasta", ">Primer1_R\nCGATCGATCGAT\n>Primer2_R\nTAGCTAGCTAGC"),
            ("reference_genome.fasta", ">Reference_Chr1\nATCGATCGATCGATCGATCGATCGATCG")
        ]

        file_paths = []
        for filename, content in sample_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            file_paths.append(file_path)
            print(f"  ✓ Created sample file: {filename}")

        print(f"\n5. Importing files...")
        import_operations = [
            (file_paths[0], "Root/Sequences/Primers"),
            (file_paths[1], "Root/Sequences/Primers"),
            (file_paths[2], "Root/Sequences/References")
        ]

        for file_path, target_folder in import_operations:
            result = app.import_file(
                source_file_path=file_path,
                target_folder_path=target_folder,
                copy_file=True,
                auto_detect_format=True
            )
            if result.success:
                print(f"  ✓ Imported: {result.data.success_message}")
                if result.data.detected_format:
                    format_info = result.data.detected_format['content_based']
                    print(f"    Detected format: {format_info['format']} (confidence: {format_info['confidence']:.2f})")
            else:
                print(f"  ✗ Failed to import {Path(file_path).name}: {result.error}")

        print(f"\n6. Project statistics:")
        stats = app.get_project_statistics()
        if stats:
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total folders: {stats['total_folders']}")
            print(f"  Total size: {stats['total_size_bytes']} bytes")
            print(f"  File types: {stats['file_types']}")

        print(f"\n7. Moving a file...")
        result = app.move_item(
            source_folder_path="Root/Sequences/Primers",
            item_name="forward_primers.fasta",
            destination_folder_path="Root/Results"
        )
        if result.success:
            print(f"  ✓ {result.data.success_message}")
        else:
            print(f"  ✗ Failed to move file: {result.error}")

        print(f"\n8. Copying a file...")
        result = app.copy_file(
            source_folder_path="Root/Sequences/Primers",
            file_name="reverse_primers.fasta",
            destination_folder_path="Root/Results/BLAST_Output",
            new_name="backup_reverse_primers.fasta"
        )
        if result.success:
            print(f"  ✓ {result.data.success_message}")
        else:
            print(f"  ✗ Failed to copy file: {result.error}")

        print(f"\n9. Validating project...")
        result = app.validate_current_project()
        if result.success:
            validation = result.data.validation_results
            print(f"  Project is valid: {result.data.is_valid}")
            print(f"  Valid files: {validation['valid_count']}/{validation['total_files']}")
            if result.data.recommendations:
                print(f"  Recommendations:")
                for rec in result.data.recommendations:
                    print(f"    - {rec}")
        else:
            print(f"  ✗ Validation failed: {result.error}")

        print(f"\n10. Saving project...")
        result = app.save_current_project(create_backup=True)
        if result.success:
            print(f"  ✓ {result.data.success_message}")
            print(f"  Backup created: {result.data.backup_created}")
        else:
            print(f"  ✗ Failed to save project: {result.error}")

        print(f"\n11. Final project status:")
        status = app.get_application_status()
        print(f"  Has unsaved changes: {status['has_unsaved_changes']}")

        print(f"\n12. Closing project...")
        result = app.close_project()
        if result.success:
            print(f"  ✓ {result.data}")
        else:
            print(f"  ✗ Failed to close project: {result.error}")

        print(f"\n13. Testing project reload...")
        result = app.load_project(project_file_path)
        if result.success:
            print(f"  ✓ Project reloaded successfully")
            if result.data.warnings:
                print(f"  Warnings: {result.data.warnings}")
        else:
            print(f"  ✗ Failed to reload project: {result.error}")

    print(f"\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_project_workflow()