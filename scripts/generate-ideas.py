#!/usr/bin/env python3
"""
CLI wrapper: generate ideas.md, grouping ideas by status.

Was previously a prose command that asked Claude to search the ideas/ folder --
which resolved relative to the working directory rather than to a configured root,
and could not say which config its link format came from.
"""

from config import describe_root, get_tasks_root
from taskrender import render_ideas


def main():
    print(describe_root())
    content, counts = render_ideas()
    (get_tasks_root() / "ideas.md").write_text(content, encoding="utf-8")

    print("\nGenerated ideas.md")
    print(f"  - {counts['in_progress']} in-progress idea(s)")
    print(f"  - {counts['noodling']} noodling idea(s)")


if __name__ == "__main__":
    main()
