#!/usr/bin/env python3
"""
CLI wrapper: generate today.md only.

/today runs the full pipeline via generate-daily-files.py. This exists for
regenerating a single view without re-normalizing or re-archiving.
"""

from config import describe_root, get_tasks_root
from dates import get_week_dates
from taskrender import render_today


def main():
    print(describe_root())
    content, counts = render_today(get_week_dates())
    (get_tasks_root() / "today.md").write_text(content, encoding="utf-8")

    print("\nGenerated today.md")
    print(f"  - {counts['overdue']} overdue task(s)")
    print(f"  - {counts['due_today']} task(s) due today")
    print(f"  - {counts['research']} research task(s)")
    print(f"  - {counts['ideas']} in-progress idea(s)")


if __name__ == "__main__":
    main()
