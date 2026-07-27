#!/usr/bin/env python3
"""
Builds the regression fixture: a fake HOME plus a tasks root that exercises every
code path in the generators, the normalizer, the archiver, and the import cleaner.

All dates are written relative to REFERENCE_TODAY rather than the real clock, so the
committed baseline stays valid forever. Callers pin the same date into the code under
test (see capture.py).

Two shapes, selected by `hostile`:

- hostile=False   a plain path and plain filenames. This is what the committed
                  baseline is captured from, because the pre-0.3.0 code cannot
                  survive the hostile shape at all.
- hostile=True    a vault directory containing a space and an ampersand, plus a task
                  filename containing an apostrophe. Exercises R7. Only the 0.3.0+
                  code is expected to pass.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

# A Wednesday. Mid-week matters: it means "rest of this week" is non-empty, which is
# the branch that distinguishes this-week.md from its empty-week fallback.
REFERENCE_TODAY = "2026-03-11"

PLAIN_VAULT_DIR = "Vault"
HOSTILE_VAULT_DIR = "Vault With Space & Ampersand"
TASKS_ROOT_NAME = "Tasks"

FOLDERS = ["tasks", "ideas", "templates", "memories", "bugs", "completed", "import"]

# An apostrophe in the filename. Archiving must move this without a shell quoting bug.
HOSTILE_FILENAME = "tasks/rick's completed errand.md"


def _d(offset):
    """A date `offset` days from REFERENCE_TODAY, as YYYY-MM-DD."""
    base = datetime.strptime(REFERENCE_TODAY, "%Y-%m-%d")
    return (base + timedelta(days=offset)).strftime("%Y-%m-%d")


def reference_dates():
    """The dates dict get_week_dates() would return on REFERENCE_TODAY."""
    today = datetime.strptime(REFERENCE_TODAY, "%Y-%m-%d").date()
    this_monday = today - timedelta(days=today.weekday())
    this_sunday = this_monday + timedelta(days=6)
    next_monday = this_sunday + timedelta(days=1)
    return {
        "today": str(today),
        "today_formatted": today.strftime("%B %-d"),
        "today_weekday": today.strftime("%A"),
        "tomorrow": str(today + timedelta(days=1)),
        "this_week_start": str(this_monday),
        "this_week_end": str(this_sunday),
        "next_week_start": str(next_monday),
        "next_week_end": str(next_monday + timedelta(days=6)),
    }


def _files():
    """(relative path, content) pairs, written verbatim."""
    return [
        # --- tasks: due-date coverage ---------------------------------------------
        ("tasks/overdue-alpha.md", f"""---
type: task
due: {_d(-3)}
---
# Overdue Alpha

Three days late.
"""),
        # Unnormalized M/D/YYYY. Normalizer rewrites it, then it reads as overdue.
        ("tasks/overdue-beta.md", """---
type: task
due: 3/6/2026
---
# Overdue Beta

Slash-format date.
"""),
        ("tasks/due-today-one.md", f"""---
type: task
due: {_d(0)}
---
# Due Today One
"""),
        # Unpadded YYYY-M-D. Normalizes to today.
        ("tasks/due-today-two.md", """---
type: task
due: 2026-3-11
---
# Due Today Two
"""),
        ("tasks/rest-of-week-thu.md", f"""---
type: task
due: {_d(1)}
---
# Thursday Task
"""),
        ("tasks/rest-of-week-sun.md", f"""---
type: task
due: {_d(4)}
---
# Sunday Task

Last day of this week.
"""),
        ("tasks/next-week-mon.md", f"""---
type: task
due: {_d(5)}
---
# Next Monday Task
"""),
        ("tasks/next-week-fri.md", f"""---
type: task
due: {_d(9)}
---
# Next Friday Task
"""),
        # Two tasks the same day, to prove ordering is stable.
        ("tasks/next-week-fri-also.md", f"""---
type: task
due: {_d(9)}
---
# Another Next Friday Task
"""),

        # --- tasks: research exclusion, both YAML tag shapes -----------------------
        ("tasks/research-single-line.md", f"""---
type: task
due: {_d(0)}
tags: [research-review, reading]
---
# Research Single Line

Tagged inline. Belongs under Research, not Due Today.
"""),
        ("tasks/research-multi-line.md", f"""---
type: task
due: {_d(-2)}
tags:
  - research-summary-needed
  - reading
---
# Research Multi Line

Tagged as a block. Overdue, but research tasks are excluded from Overdue.
"""),

        # --- tasks: archiving ------------------------------------------------------
        ("tasks/completed-one-time.md", f"""---
type: task
due: {_d(-4)}
completed: {_d(-1)}
---
# Completed One Time

Archiving runs before generation, so this must not show up as overdue.
"""),
        ("tasks/completed-recurring.md", f"""---
type: task
due: {_d(0)}
completed: {_d(-7)}
recurrence: weekly
---
# Completed Recurring

Completed but recurring: stays in tasks/ forever.
"""),

        # --- tasks: parser hazards -------------------------------------------------
        # An unnormalized date forces a frontmatter rewrite, and the body contains a
        # horizontal rule. The rewrite must not swallow or reflow it.
        ("tasks/body-has-hr.md", """---
type: task
due: 3/9/2026
---
# Body Has Horizontal Rule

Section one.

---

Section two, after a `---` rule.

---
"""),
        ("tasks/no-due-date.md", """---
type: task
---
# No Due Date

Never appears in any generated view.
"""),

        # --- ideas: every status spelling -----------------------------------------
        ("ideas/idea-in-progress-space.md", """---
type: idea
status: in progress
---
# Idea With Space Spelling
"""),
        ("ideas/idea-in-progress-hyphen.md", """---
type: idea
status: in-progress
---
# Idea With Hyphen Spelling
"""),
        ("ideas/idea-noodling.md", """---
type: idea
status: noodling
---
# Noodling Idea
"""),
        ("ideas/idea-someday.md", """---
type: idea
status: someday
---
# Someday Idea

Excluded from every view.
"""),
        ("ideas/idea-unstatused.md", """---
type: idea
---
# Unstatused Idea

Excluded from every view.
"""),

        # --- bugs ------------------------------------------------------------------
        ("bugs/a-bug.md", """---
type: bug
created: 3/1/2026
---
# A Bug

Its `created:` date is unnormalized, proving the normalizer walks bugs/ too.
"""),

        # --- import ----------------------------------------------------------------
        ("import/import-task.md", f"""---
type: task
due: {_d(6)}
---
# Imported Task
"""),
        ("import/import-idea.md", """---
type: idea
status: noodling
---
# Imported Idea
"""),
        ("import/import-bug.md", """---
type: bug
---
# Imported Bug
"""),
        ("import/import-no-type.md", """---
due: 3/20/2026
---
# Imported With No Type

Stays in import/.
"""),
        ("import/import-unknown-type.md", """---
type: widget
---
# Imported Unknown Type

Stays in import/.
"""),
    ]


LEGACY_CONFIG = """paths:
  tasks_root: "{tasks_root}"

folders:
  tasks: "tasks"
  ideas: "ideas"
  templates: "templates"
  memories: "memories"
  bugs: "bugs"
  completed: "completed"
  import: "import"

links:
  format: "{link_format}"

integrations:
  research_system: false
"""


def build(dest, hostile=False, link_format="obsidian", write_global_config=True):
    """
    Create the fixture under `dest`. Returns (home, tasks_root).

    `dest` is wiped first, so this is safe to call repeatedly.
    """
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)

    home = dest / "home"
    vault_dir = HOSTILE_VAULT_DIR if hostile else PLAIN_VAULT_DIR
    tasks_root = dest / vault_dir / TASKS_ROOT_NAME

    for folder in FOLDERS:
        (tasks_root / folder).mkdir(parents=True, exist_ok=True)

    files = list(_files())
    if hostile:
        files.append((HOSTILE_FILENAME, f"""---
type: task
due: {_d(-2)}
completed: {_d(-1)}
---
# Rick's Completed Errand

Apostrophe and space in the filename.
"""))

    for rel, content in files:
        (tasks_root / rel).write_text(content, encoding="utf-8")

    home.mkdir(parents=True, exist_ok=True)
    if write_global_config:
        config_dir = home / ".claude" / "task-management-config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yaml").write_text(
            LEGACY_CONFIG.format(tasks_root=tasks_root, link_format=link_format),
            encoding="utf-8",
        )

    return home, tasks_root


def snapshot(tasks_root):
    """
    Render the whole tasks root as one deterministic string: every file's relative
    path and full contents, sorted. Diffing two snapshots proves whether a refactor
    changed behavior anywhere in the tree, not just in the generated views.
    """
    tasks_root = Path(tasks_root)
    lines = []
    for path in sorted(tasks_root.rglob("*"), key=lambda p: str(p.relative_to(tasks_root))):
        rel = path.relative_to(tasks_root)
        if path.is_dir():
            lines.append(f"=== DIR  {rel}/")
            continue
        lines.append(f"=== FILE {rel}")
        lines.append(path.read_text(encoding="utf-8"))
        lines.append("=== END")
    return "\n".join(lines) + "\n"
