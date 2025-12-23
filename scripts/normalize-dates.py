#!/usr/bin/env python3
"""
Normalize date formats in task frontmatter to YYYY-MM-DD.

Handles multiple input formats:
- M/D/YYYY or MM/DD/YYYY (e.g., 10/5/2025 or 9/5/2025)
- YYYY-M-D (e.g., 2025-10-5)
- YYYY-MM-DD (already correct)

Converts all to YYYY-MM-DD format.
"""

import re
import os
from pathlib import Path
from datetime import datetime

# Import config from same directory
from config import get_all_task_dirs

def parse_date(date_str):
    """
    Parse various date formats and return standardized YYYY-MM-DD string.

    Supports:
    - M/D/YYYY or MM/DD/YYYY
    - YYYY-M-D or YYYY-MM-DD
    """
    date_str = date_str.strip()

    # Try M/D/YYYY or MM/DD/YYYY format
    if '/' in date_str:
        try:
            dt = datetime.strptime(date_str, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            try:
                dt = datetime.strptime(date_str, '%m/%d/%y')
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

    # Try YYYY-M-D or YYYY-MM-DD format
    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            # Pad month and day with leading zeros if needed
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Return original if we can't parse it
    return date_str

def normalize_file_dates(file_path):
    """
    Normalize all date fields in a file's frontmatter.
    Returns True if file was modified, False otherwise.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file has frontmatter
    if not content.startswith('---'):
        return False

    # Split content into frontmatter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]
    body = parts[2]

    # Pattern to match date fields (due, completed, created, etc.)
    date_pattern = r'^(due|completed|created|updated):\s*(.+)$'

    modified = False
    new_lines = []

    for line in frontmatter.split('\n'):
        match = re.match(date_pattern, line)
        if match:
            field_name = match.group(1)
            date_value = match.group(2)

            # Skip empty date values
            if not date_value or date_value.strip() == '':
                new_lines.append(line)
                continue

            normalized_date = parse_date(date_value)

            if normalized_date != date_value:
                new_lines.append(f"{field_name}: {normalized_date}")
                modified = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified:
        new_frontmatter = '\n'.join(new_lines)
        new_content = f"---{new_frontmatter}---{body}"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    return False

def main():
    """Normalize dates in all task files."""
    modified_files = []

    for task_dir in get_all_task_dirs():
        if not task_dir.exists():
            continue

        for file_path in task_dir.glob('*.md'):
            if normalize_file_dates(file_path):
                modified_files.append(str(file_path))

    # Print results
    if modified_files:
        print(f"Normalized dates in {len(modified_files)} files:\n")
        for file_path in modified_files:
            print(f"  - {file_path}")
    else:
        print("No files needed date normalization.")

if __name__ == '__main__':
    main()
