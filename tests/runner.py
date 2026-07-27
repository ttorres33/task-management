#!/usr/bin/env python3
"""
Runs the full generate-daily-files pipeline against a throwaway fixture and snapshots
the resulting tree. Used both to capture the committed baseline and to check the
refactored code against it.

Why this exists in this shape:

- The pipeline reads the clock. `get_week_dates` is patched on the loaded module so
  the fixture's dates and the code's idea of "today" agree forever.
- The pipeline reads $HOME. It is set before the plugin's `config` module is imported,
  because `config` resolves its paths at import time.
- `generate-daily-files.py` is hyphenated and therefore not importable by name, so it
  is loaded by path. That is itself one of the things 0.3.0 fixes, but the loader has
  to work against the old code too.

Stdout is deliberately not part of the snapshot. 0.3.0 adds a resolved-root line to
every script's output, so stdout is expected to differ; the tree is what must not.

Usage:
    python3 tests/runner.py --out <dir> [--hostile]
"""

import argparse
import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

sys.path.insert(0, str(TESTS_DIR))
import fixture  # noqa: E402


# Plugin modules that cache $HOME-derived state at import time. Dropped between runs
# so a second run in the same process does not inherit the first run's root.
PLUGIN_MODULES = [
    "config", "dates", "markerparse", "taskquery",
    "taskrender", "archiving", "normalize",
]


def _load_script(name):
    """Import one of the plugin's hyphenated scripts by path."""
    path = SCRIPTS_DIR / name
    spec = importlib.util.spec_from_file_location(f"_script_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    # Registering before exec lets the module import its own siblings normally.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _reset_plugin_modules():
    for name in PLUGIN_MODULES:
        sys.modules.pop(name, None)
    for name in list(sys.modules):
        if name.startswith("_script_"):
            del sys.modules[name]


def run_pipeline(dest, hostile=False, link_format="obsidian"):
    """
    Build a fixture under `dest`, run the pipeline, and return
    {"daily": <snapshot>, "imports": <snapshot>}.
    """
    home, tasks_root = fixture.build(dest, hostile=hostile, link_format=link_format)

    os.environ["HOME"] = str(home)
    # Guarantee any subprocess the pre-0.3.0 code spawns uses this very interpreter.
    # Without this, `python3` resolves through PATH to whichever pyenv version the
    # temp directory happens to select, which may lack PyYAML -- and the old code
    # prints that failure to stderr and carries on, silently producing a wrong tree.
    os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")
    os.environ.pop("TASK_MANAGEMENT_ROOT", None)

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    _reset_plugin_modules()

    pinned = fixture.reference_dates()

    daily = _load_script("generate-daily-files.py")
    daily.get_week_dates = lambda *a, **kw: pinned
    daily.main()

    snapshots = {"daily": fixture.snapshot(tasks_root)}

    cleaner = _load_script("clean-imports.py")
    cleaner.main()

    snapshots["imports"] = fixture.snapshot(tasks_root)
    return snapshots


def _assert_pipeline_really_ran(snapshot_text):
    """
    Guard against a half-executed pipeline being captured as truth.

    The old code runs normalization and archiving as subprocesses and only prints
    their stderr -- a crashed child does not fail the run. These two assertions are
    the cheapest proof that both actually did their work.
    """
    problems = []
    if "due: 2026-03-06" not in snapshot_text:
        problems.append("normalization did not run (overdue-beta.md still has a slash date)")
    if "=== FILE completed/completed-one-time.md" not in snapshot_text:
        problems.append("archiving did not run (completed-one-time.md is not in completed/)")
    if problems:
        raise SystemExit("Pipeline did not complete:\n  - " + "\n  - ".join(problems))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="directory to write snapshots into")
    parser.add_argument("--hostile", action="store_true",
                        help="use a root path with a space and an ampersand, and a "
                             "task filename with an apostrophe (R7)")
    parser.add_argument("--link-format", default="obsidian",
                        choices=["obsidian", "markdown"],
                        help="link format for the fixture's config")
    parser.add_argument("--keep", metavar="DIR",
                        help="build the fixture here instead of a temp dir, and keep it")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    options = {"hostile": args.hostile, "link_format": args.link_format}
    if args.keep:
        snapshots = run_pipeline(Path(args.keep), **options)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            snapshots = run_pipeline(Path(tmp) / "fixture", **options)

    _assert_pipeline_really_ran(snapshots["daily"])

    for name, text in snapshots.items():
        (out / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"wrote {out / (name + '.txt')} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
