#!/usr/bin/env python3
"""
CLI wrapper: archive completed one-time tasks from tasks/ to completed/.

Logic lives in archiving.py so it can be imported. Recurring tasks are never
archived.
"""

from archiving import archive_completed_tasks, report
from config import describe_root


def main():
    print("=== Archiving Completed Tasks ===\n")
    print(describe_root())
    print()
    report(*archive_completed_tasks())


if __name__ == "__main__":
    main()
