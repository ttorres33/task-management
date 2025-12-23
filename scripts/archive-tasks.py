#!/usr/bin/env python3
"""
Archive completed one-time tasks from tasks/ to completed/.

Recurring tasks (those with recurrence: field) are never archived.
"""

import subprocess
from pathlib import Path

from config import get_tasks_root, get_folder


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


def archive_completed_tasks():
    """Archive completed one-time tasks to completed/ folder."""
    tasks_dir = get_folder("tasks")
    completed_dir = get_folder("completed")

    # Grep for files with completed: field
    stdout, stderr, code = run_command(
        f"grep -il '^completed:' {tasks_dir}/*.md 2>/dev/null || true"
    )

    if not stdout:
        print("No completed tasks to archive.")
        return

    completed_files = stdout.split('\n')
    archived = []
    skipped = []

    for file_path in completed_files:
        if not file_path:
            continue

        # Check if it has recurrence field (recurring tasks don't get archived)
        check_cmd = f"grep -q '^recurrence:' '{file_path}'"
        _, _, has_recurrence = run_command(check_cmd)

        if has_recurrence == 0:  # grep found recurrence field
            filename = Path(file_path).name
            skipped.append(filename)
            continue

        # Move to completed/
        filename = Path(file_path).name
        run_command(f"mv '{file_path}' '{completed_dir}/'")
        archived.append(filename)

    # Report results
    if archived:
        print(f"Archived {len(archived)} completed task(s):\n")
        print("Moved to completed/:")
        for f in archived:
            print(f"  - {f}")

    if skipped:
        print(f"\nSkipped {len(skipped)} recurring task(s):")
        for f in skipped:
            print(f"  - {f} (has recurrence field, stays in tasks/)")

    if archived:
        print("\nTasks folder is now clean!")
    elif not skipped:
        print("No completed tasks to archive.")


def main():
    print("=== Archiving Completed Tasks ===\n")
    archive_completed_tasks()


if __name__ == "__main__":
    main()
