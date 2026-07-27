#!/usr/bin/env python3
"""
Archiving completed one-time tasks from tasks/ to completed/.

Extracted from archive-tasks.py so the /today orchestrator can call it directly
instead of spawning a child that re-resolved its own root from its own working
directory -- which worked only by coincidence, and would pick the wrong task system
outright once more than one exists.

The port also fixes two shell-quoting bugs inherited from the previous version: an
unquoted glob that broke on any root containing a space, and `mv '{path}'` that
broke on any filename containing an apostrophe. Both are on the hot path, because
archiving runs inside /today.
"""

import shutil

from config import get_folder
from taskquery import has_field, md_files


def archive_completed_tasks():
    """
    Move completed one-time tasks to completed/. Returns (archived, skipped) names.

    Recurring tasks are never archived: a weekly task that was completed this week
    is still due next week.
    """
    tasks_dir = get_folder("tasks")
    completed_dir = get_folder("completed")

    archived = []
    skipped = []

    for path in md_files(tasks_dir):
        # Case-insensitive, matching the original `grep -il '^completed:'`.
        if not has_field(path, "completed", ignore_case=True):
            continue
        if has_field(path, "recurrence"):
            skipped.append(path.name)
            continue

        completed_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(completed_dir / path.name))
        archived.append(path.name)

    return archived, skipped


def report(archived, skipped):
    """Print the archiving summary."""
    if archived:
        print(f"Archived {len(archived)} completed task(s):\n")
        print("Moved to completed/:")
        for name in archived:
            print(f"  - {name}")

    if skipped:
        print(f"\nSkipped {len(skipped)} recurring task(s):")
        for name in skipped:
            print(f"  - {name} (has recurrence field, stays in tasks/)")

    if archived:
        print("\nTasks folder is now clean!")
    elif not skipped:
        print("No completed tasks to archive.")
