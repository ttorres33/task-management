#!/usr/bin/env python3
"""
Normalizing date fields in task frontmatter to YYYY-MM-DD.

Handles M/D/YYYY, MM/DD/YYYY, YYYY-M-D, and YYYY-MM-DD.

Extracted from normalize-dates.py so the /today orchestrator can call it directly
rather than shelling out to it.

This module is a *writer*, and deliberately does not use the shared field reader in
taskquery. It rewrites the lines it matches and passes every other line through
byte-for-byte, then rejoins frontmatter and body untouched. A reader returns values;
this needs lossless round-tripping of everything it does not touch. Routing it
through a shared parser is exactly how a refactor silently reformats a user's task
files -- including any `---` horizontal rule in a body, which the rejoin preserves
only because the body is never re-serialized.
"""

import re
from datetime import datetime

from config import get_all_task_dirs
from taskquery import md_files

DATE_FIELD_PATTERN = r'^(due|completed|created|updated):\s*(.+)$'


def parse_date(date_str):
    """
    Parse a date in any supported format and return it as YYYY-MM-DD.

    Returns the input unchanged if it cannot be parsed, so an unrecognized value is
    left alone rather than mangled.
    """
    date_str = date_str.strip()

    if '/' in date_str:
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%m/%d/%y').strftime('%Y-%m-%d')
            except ValueError:
                pass

    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return date_str


def normalize_file_dates(file_path):
    """
    Normalize date fields in one file. Returns True if the file was modified.

    An unreadable file is skipped rather than raised on. Normalizing used to run as
    a separate child process whose failure only printed to stderr, so /today carried
    on and still generated its files. Now that it is a direct call, one file that is
    not valid UTF-8 anywhere under tasks/ ideas/ bugs/ import/ would otherwise abort
    the whole run before anything was written.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    if not content.startswith('---'):
        return False

    parts = content.split('---', 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]
    body = parts[2]

    modified = False
    new_lines = []

    for line in frontmatter.split('\n'):
        match = re.match(DATE_FIELD_PATTERN, line)
        if not match:
            new_lines.append(line)
            continue

        field_name = match.group(1)
        date_value = match.group(2)

        if not date_value or date_value.strip() == '':
            new_lines.append(line)
            continue

        normalized_date = parse_date(date_value)
        if normalized_date != date_value:
            new_lines.append(f"{field_name}: {normalized_date}")
            modified = True
        else:
            new_lines.append(line)

    if not modified:
        return False

    new_frontmatter = '\n'.join(new_lines)
    # Rejoined exactly as split, so `body` -- including any `---` rule inside it --
    # is written back byte-for-byte.
    new_content = f"---{new_frontmatter}---{body}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def normalize_all():
    """Normalize every task file under the resolved root. Returns modified paths."""
    modified_files = []

    for task_dir in get_all_task_dirs():
        for file_path in md_files(task_dir):
            if normalize_file_dates(file_path):
                modified_files.append(str(file_path))

    return modified_files


def report(modified_files):
    """Print the normalization summary."""
    if modified_files:
        print(f"Normalized dates in {len(modified_files)} files:\n")
        for file_path in modified_files:
            print(f"  - {file_path}")
    else:
        print("No files needed date normalization.")
