#!/usr/bin/env python3
"""
Move reviewed files from import/ to appropriate folders based on type field.

Files with type: task → tasks/
Files with type: idea → ideas/
Files with type: template → templates/
Files with type: memory → memories/
Files with type: bug → bugs/
"""

import subprocess
from pathlib import Path

from config import get_tasks_root, get_folder, get_link_format


# Map type values to folder names
TYPE_TO_FOLDER = {
    "task": "tasks",
    "idea": "ideas",
    "template": "templates",
    "memory": "memories",
    "bug": "bugs",
}


def run_command(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=get_tasks_root(),
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def format_link(filename, folder):
    """Format a link based on the configured link format."""
    link_format = get_link_format()
    if link_format == "markdown":
        return f"[{filename}]({folder}/{filename}.md)"
    else:
        # Default to obsidian wiki-links
        return f"[[{filename}]]"


def clean_imports():
    """Move files from import/ to appropriate folders based on type field."""
    import_dir = get_folder("import")

    # Check if import folder exists and has .md files
    if not import_dir.exists():
        print("Import folder does not exist.")
        return

    md_files = list(import_dir.glob("*.md"))
    if not md_files:
        print("No files in import/ folder.")
        return

    moved = {}  # folder -> list of filenames
    skipped = []  # files without type field

    for file_path in md_files:
        # Read file and look for type field
        content = file_path.read_text()
        file_type = None

        for line in content.split('\n'):
            if line.startswith('type:'):
                file_type = line.split(':', 1)[1].strip()
                break

        if not file_type or file_type not in TYPE_TO_FOLDER:
            skipped.append(file_path.name)
            continue

        # Move to appropriate folder
        dest_folder_name = TYPE_TO_FOLDER[file_type]
        dest_folder = get_folder(dest_folder_name)

        # Ensure destination exists
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Move file
        dest_path = dest_folder / file_path.name
        file_path.rename(dest_path)

        if dest_folder_name not in moved:
            moved[dest_folder_name] = []
        moved[dest_folder_name].append(file_path.stem)

    # Report results
    total_moved = sum(len(files) for files in moved.values())

    if total_moved > 0:
        print(f"Moved {total_moved} file(s) from import/:\n")

        for folder_name in ["tasks", "ideas", "bugs", "memories", "templates"]:
            if folder_name in moved:
                files = moved[folder_name]
                print(f"{folder_name}/ ({len(files)} file{'s' if len(files) != 1 else ''}):")
                for f in files:
                    print(f"  - {format_link(f, folder_name)}")
                print()

    if skipped:
        print(f"Skipped {len(skipped)} file(s) (no type field):")
        for f in skipped:
            print(f"  - {f}")
        print()

    if total_moved > 0:
        print("Import cleanup complete!")
    elif not skipped:
        print("No files to process.")


def main():
    print("=== Cleaning Import Folder ===\n")
    clean_imports()


if __name__ == "__main__":
    main()
