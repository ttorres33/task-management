#!/usr/bin/env python3
"""
Test helpers for loading the plugin's modules against a controlled environment.

Root resolution reads $HOME, the working directory, and $TASK_MANAGEMENT_ROOT, and
`config` caches what it finds. Each case therefore needs a genuinely fresh import
against a fresh environment, which `plugin_env` provides.

scripts/ is PREPENDED to sys.path, never appended. markerparse.py was named to avoid
shadowing the PyPI `python-frontmatter` package, but that only holds if our directory
wins; appending would let an installed third-party package take precedence.
"""

import contextlib
import importlib
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

PLUGIN_MODULES = [
    "config", "dates", "markerparse", "taskquery",
    "taskrender", "archiving", "normalize",
]


def _drop_plugin_modules():
    for name in PLUGIN_MODULES:
        sys.modules.pop(name, None)


@contextlib.contextmanager
def plugin_env(cwd, home=None, root_override=None):
    """
    Import the plugin fresh with $HOME, the working directory, and
    $TASK_MANAGEMENT_ROOT set as given. Yields the freshly imported `config` module.

    Everything is restored on exit, so cases cannot leak into each other.
    """
    saved_cwd = os.getcwd()
    saved_env = dict(os.environ)
    saved_path = list(sys.path)
    saved_modules = {name: sys.modules[name] for name in PLUGIN_MODULES if name in sys.modules}

    try:
        if home is not None:
            os.environ["HOME"] = str(home)
        if root_override is None:
            os.environ.pop("TASK_MANAGEMENT_ROOT", None)
        else:
            os.environ["TASK_MANAGEMENT_ROOT"] = str(root_override)

        os.chdir(str(cwd))

        sys.path.insert(0, str(SCRIPTS_DIR))
        _drop_plugin_modules()

        yield importlib.import_module("config")
    finally:
        _drop_plugin_modules()
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path
        os.environ.clear()
        os.environ.update(saved_env)
        os.chdir(saved_cwd)


def import_plugin_module(name):
    """Import a plugin module inside an active plugin_env block."""
    return importlib.import_module(name)


def write(path, text):
    """Write `text` to `path`, creating parent directories."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def marker(name="test-root", **sections):
    """
    Build marker file text.

    `sections` become nested blocks, e.g. folders={"tasks": "t"} renders as
    a `folders:` block with `  tasks: t` beneath it.

    `task_management_root: true` is what makes the file a marker; `name` is only a
    label. Pass name=None to build a marker without one.
    """
    lines = ["---", "task_management_root: true"]
    if name is not None:
        lines.append(f"name: {name}")
    for key, value in sections.items():
        lines.append(f"{key}:")
        for subkey, subvalue in value.items():
            if isinstance(subvalue, bool):
                subvalue = "true" if subvalue else "false"
            lines.append(f"  {subkey}: {subvalue}")
    lines += ["---", "# Task Management Root", ""]
    return "\n".join(lines)


def install_fake_research_system(home, marketplace="some-marketplace"):
    """Create the directory layout a marketplace install of research-system produces."""
    path = Path(home) / ".claude" / "plugins" / "cache" / marketplace / "research-system" / "0.3.0"
    path.mkdir(parents=True, exist_ok=True)
    return path
