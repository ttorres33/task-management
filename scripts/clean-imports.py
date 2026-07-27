#!/usr/bin/env python3
"""
Move reviewed files from import/ to the folder matching their type field.

Files with type: task → tasks/
Files with type: idea → ideas/
Files with type: template → templates/
Files with type: memory → memories/
Files with type: bug → bugs/

Files with no type field, or an unrecognized one, stay in import/.
"""

from config import describe_root, get_folder
from taskquery import format_link, read_field

TYPE_TO_FOLDER = {
    "task": "tasks",
    "idea": "ideas",
    "template": "templates",
    "memory": "memories",
    "bug": "bugs",
}


def clean_imports():
    """
    Move files out of import/. Returns (status, moved_by_folder, skipped_names).

    `status` is "no-dir", "empty", or "ok" -- enough for the caller to tell the two
    do-nothing cases apart, which produce different messages.
    """
    import_dir = get_folder("import")

    moved = {}
    skipped = []

    if not import_dir.exists():
        return "no-dir", moved, skipped

    md_files = sorted(import_dir.glob("*.md"))
    if not md_files:
        return "empty", moved, skipped

    for file_path in md_files:
        file_type = read_field(file_path, "type")

        if not file_type or file_type not in TYPE_TO_FOLDER:
            skipped.append(file_path.name)
            continue

        dest_folder_name = TYPE_TO_FOLDER[file_type]
        dest_folder = get_folder(dest_folder_name)
        dest_folder.mkdir(parents=True, exist_ok=True)

        file_path.rename(dest_folder / file_path.name)
        moved.setdefault(dest_folder_name, []).append(file_path.stem)

    return "ok", moved, skipped


def report(status, moved, skipped):
    """Print the cleanup summary."""
    if status == "no-dir":
        print("Import folder does not exist.")
        return
    if status == "empty":
        print("No files in import/ folder.")
        return

    total_moved = sum(len(files) for files in moved.values())

    if total_moved:
        print(f"Moved {total_moved} file(s) from import/:\n")
        for folder_name in ["tasks", "ideas", "bugs", "memories", "templates"]:
            if folder_name not in moved:
                continue
            files = moved[folder_name]
            print(f"{folder_name}/ ({len(files)} file{'s' if len(files) != 1 else ''}):")
            for name in files:
                print(f"  - {format_link(name, folder_name)}")
            print()

    if skipped:
        print(f"Skipped {len(skipped)} file(s) (no type field):")
        for name in skipped:
            print(f"  - {name}")
        print()

    if total_moved:
        print("Import cleanup complete!")
    elif not skipped:
        print("No files to process.")


def main():
    print("=== Cleaning Import Folder ===\n")
    print(describe_root())
    print()
    report(*clean_imports())


if __name__ == "__main__":
    main()
