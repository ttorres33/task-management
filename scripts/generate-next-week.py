#!/usr/bin/env python3
"""
CLI wrapper: generate next-week.md (next Monday through Sunday).
"""

from config import describe_root, get_tasks_root
from dates import get_week_dates
from taskrender import render_next_week


def main():
    print(describe_root())
    content, total, days = render_next_week(get_week_dates())
    (get_tasks_root() / "next-week.md").write_text(content, encoding="utf-8")

    print("\nGenerated next-week.md")
    print(f"  - {total} task(s) across {len(days)} day(s)")


if __name__ == "__main__":
    main()
