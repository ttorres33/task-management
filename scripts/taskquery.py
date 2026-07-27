#!/usr/bin/env python3
"""
Shared read-only queries over task files, in plain Python.

Replaces the shelled-out grep pipeline the generators used to run. That pipeline
interpolated paths into shell strings without quoting, so any tasks root containing
a space or an ampersand broke it -- likely in a shared vault, where sibling folders
are named for human convenience rather than shell safety.

Every function here is a faithful port, quirks included, because the generated views
are diffed against a baseline captured from the shell version. Where a quirk is
load-bearing it is called out in a comment.
"""

from datetime import datetime
from pathlib import Path

from config import get_folder, get_link_format

RESEARCH_TAGS = ("research-review", "research-summary-needed")


def md_files(directory):
    """
    The .md files in `directory`, in a stable order.

    Ordering reaches the generated files directly -- it is the order bullets appear
    under each day -- so it is pinned here rather than left to the filesystem.

    Codepoint order, which is what the shell glob this replaced produced. Glob
    expansion sorts by LC_COLLATE, and the environment these commands run in sets no
    locale, so collation falls back to C. Verified against the live vault: the shell
    glob and sorted() return identical order, including for capitalized filenames.

    Under an explicit en_US.UTF-8 locale the old glob would have sorted
    case-insensitively instead -- so the previous behavior was environment-dependent.
    Fixing it to one deterministic order is deliberate.

    Dotfiles are excluded, matching a shell glob without `dotglob`.
    """
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.glob("*.md") if not path.name.startswith(".")
    )


def _lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return []


# ------------------------------------------------------------------- field reading


def read_field(path, field):
    """
    Return the value of the first `field:` line, or None.

    Scans the whole file rather than just the frontmatter, matching the behavior of
    the code this replaces. Task files are user-authored, so this stays line-based
    on purpose -- a strict parser here would turn any unusual construct in someone's
    hand-written notes into a hard failure.
    """
    prefix = f"{field}:"
    for line in _lines(path):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def has_field(path, field, ignore_case=False):
    """True if any line starts with `field:`."""
    prefix = f"{field}:"
    if ignore_case:
        prefix_lower = prefix.lower()
        return any(line.lower().startswith(prefix_lower) for line in _lines(path))
    return any(line.startswith(prefix) for line in _lines(path))


def _has_line(path, predicate):
    return any(predicate(line) for line in _lines(path))


# ------------------------------------------------------------------------- queries


def is_research_task(path):
    """
    True if a file carries a research tag.

    Mirrors `grep -E '^tags:|^  - research'` followed by a substring test on the
    combined output: it catches both the inline form (`tags: [research-review]`) and
    the block form (`tags:` then `  - research-summary-needed`).
    """
    matched = [
        line for line in _lines(path)
        if line.startswith("tags:") or line.startswith("  - research")
    ]
    blob = "\n".join(matched)
    return any(tag in blob for tag in RESEARCH_TAGS)


def get_tasks_for_date(date):
    """Stems of tasks due exactly on `date`, excluding research tasks."""
    results = []
    for path in md_files(get_folder("tasks")):
        # Anchored at both ends, and requiring the space after the colon, exactly as
        # the original `grep -l '^due: {date}$'` did.
        if not _has_line(path, lambda line: line == f"due: {date}"):
            continue
        if is_research_task(path):
            continue
        results.append(path.stem)
    return results


def get_overdue_tasks(today):
    """(stem, due_date) pairs for tasks due before `today`, excluding research tasks."""
    today_date = datetime.strptime(today, "%Y-%m-%d")

    overdue = []
    for path in md_files(get_folder("tasks")):
        due_lines = [line for line in _lines(path) if line.startswith("due: ")]
        if not due_lines:
            continue
        if is_research_task(path):
            continue

        # The original joined grep's matching lines and split on 'due: ' with NO
        # maxsplit, so with two due lines element [1] is the text *between* the two
        # occurrences -- i.e. the first date, which parses. Adding a maxsplit here
        # would make element [1] run to the end of the blob, never parse, and
        # silently drop the task from Overdue. Preserved deliberately; `due_lines[0]`
        # would read better but is a different answer when a body line also starts
        # with "due: ".
        blob = "\n".join(due_lines).strip()
        due_str = blob.split("due: ")[1].strip()
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d")
        except ValueError:
            continue
        if due_date < today_date:
            overdue.append((path.stem, due_str))

    return overdue


def get_research_tasks():
    """
    Stems of tasks carrying a research tag.

    Matches anywhere in the file, not just the frontmatter -- the original grep was
    unanchored, so a task whose body merely mentions the tag is included.
    """
    results = []
    for path in md_files(get_folder("tasks")):
        text = "\n".join(_lines(path))
        if any(tag in text for tag in RESEARCH_TAGS):
            results.append(path.stem)
    return results


def get_ideas_by_status(status):
    """
    Stems of ideas with the given status.

    'in progress' matches both the spaced and hyphenated spellings, which is what
    the original `^status: in[ -]progress$` did. Both appear in real vaults.
    """
    if status == "in progress":
        def matches(line):
            return line in ("status: in progress", "status: in-progress")
    else:
        def matches(line):
            return line == f"status: {status}"

    return [path.stem for path in md_files(get_folder("ideas")) if _has_line(path, matches)]


def get_in_progress_ideas():
    """Stems of ideas with status 'in progress' or 'in-progress'."""
    return get_ideas_by_status("in progress")


# --------------------------------------------------------------------------- links


def format_link(filename, folder=None):
    """Format a link to a task file using the root's configured link format."""
    if get_link_format() == "markdown":
        if folder:
            return f"[{filename}]({folder}/{filename}.md)"
        return f"[{filename}]({filename}.md)"
    return f"[[{filename}]]"
