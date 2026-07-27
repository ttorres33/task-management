#!/usr/bin/env python3
"""
Orchestrator for /today: normalize, archive, then generate today.md, this-week.md,
and next-week.md.

This filename and location are a compatibility contract -- a personalized /today
command locates this script by name across plugin versions. Do not rename or move it.

Every step is a function call. The previous version spawned normalize-dates.py and
archive-tasks.py as child processes with cwd set to the tasks root, and those
children re-resolved config from their own working directory. That happened to land
on the right answer with exactly one task system configured; with two it would not.
Those children only existed because both files are hyphenated and therefore cannot
be imported, so the fix was to extract the logic, not to manage child environments.
"""

from archiving import archive_completed_tasks, report as report_archiving
from config import describe_root, get_tasks_root
from dates import get_week_dates
from normalize import normalize_all, report as report_normalize
from taskrender import render_this_week, render_next_week, render_today


def main():
    print("=== Generating Daily Task Files ===\n")
    print(describe_root())

    base_dir = get_tasks_root()

    print("\nNormalizing dates...")
    report_normalize(normalize_all())

    print("\nCalculating week dates...")
    dates = get_week_dates()
    print(f"Today: {dates['today_weekday']}, {dates['today_formatted']} ({dates['today']})")
    print(f"This week: {dates['this_week_start']} to {dates['this_week_end']}")
    print(f"Next week: {dates['next_week_start']} to {dates['next_week_end']}")

    print("\nArchiving completed tasks...")
    report_archiving(*archive_completed_tasks())

    print("\nGenerating today.md...")
    content, counts = render_today(dates)
    (base_dir / "today.md").write_text(content, encoding="utf-8")
    print(f"  - {counts['overdue']} overdue task(s)")
    print(f"  - {counts['due_today']} task(s) due today")
    print(f"  - {counts['research']} research task(s)")
    print(f"  - {counts['ideas']} in-progress idea(s)")

    print("\nGenerating this-week.md...")
    content, total, days = render_this_week(dates)
    (base_dir / "this-week.md").write_text(content, encoding="utf-8")
    if days:
        print(f"  - {total} task(s) across {len(days)} day(s)")
    else:
        print("  - No days remaining this week")

    print("\nGenerating next-week.md...")
    content, total, days = render_next_week(dates)
    (base_dir / "next-week.md").write_text(content, encoding="utf-8")
    print(f"  - {total} task(s) across {len(days)} day(s)")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
