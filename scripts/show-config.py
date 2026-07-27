#!/usr/bin/env python3
"""
Print the resolved configuration: which task system a command would act on, and what
it is allowed to do.

This is the only place the research-integration capability table is evaluated. The
markdown command files read the lines printed here; they never probe the filesystem
and never re-derive the table themselves. An earlier design had the detection logic
"shared" between setup.md and today.md, which is not possible -- both are markdown
driven by Claude, with no shared layer between them, so in practice it would have
become the same bash snippet copy-pasted into two files.

Output is stable, one `key: value` per line, so a command can read a single line
without parsing the whole thing.

Usage:
    python3 show-config.py [--date YYYY-MM-DD]
    python3 show-config.py --detect-research
"""

import argparse
import sys

import config
from dates import get_week_dates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="date to resolve the research digest path for "
                                       "(defaults to today)")
    parser.add_argument("--detect-research", action="store_true",
                        help="report only whether the research-system plugin is "
                             "installed, without resolving a root. For /setup, which "
                             "runs before a root exists.")
    args = parser.parse_args()

    if args.detect_research:
        installed = config.research_system_installed()
        print(f"research_system_installed: {'yes' if installed else 'no'}")
        return 0

    try:
        root, source = config.resolve_root()
    except (FileNotFoundError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    date = args.date or get_week_dates()["today"]

    print(f"root: {root}")
    print(f"name: {config.get_root_name()}")
    print(f"source: {source}")
    print(f"settings: {config.describe_settings_source()}")
    print(f"link_format: {config.get_link_format()}")

    capability, notice = config.research_capability()
    print(f"research: {capability}")

    if capability != "off":
        digest = config.get_research_digest_path(date)
        print(f"research_digest: {digest}")
        print(f"research_digest_exists: {'yes' if digest.is_file() else 'no'}")

    if notice:
        print()
        print(notice)

    return 0


if __name__ == "__main__":
    sys.exit(main())
