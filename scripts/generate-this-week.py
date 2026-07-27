#!/usr/bin/env python3
"""
CLI wrapper: generate this-week.md (tomorrow through Sunday).
"""

from config import describe_root, get_tasks_root
from dates import get_week_dates
from taskrender import render_this_week


def main():
    print(describe_root())
    content, total, days = render_this_week(get_week_dates())
    (get_tasks_root() / "this-week.md").write_text(content, encoding="utf-8")

    print("\nGenerated this-week.md")
    if days:
        print(f"  - {total} task(s) across {len(days)} day(s)")
    else:
        print("  - No days remaining this week")


if __name__ == "__main__":
    main()
