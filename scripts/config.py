#!/usr/bin/env python3
"""
Configuration loading utility for task-management plugin.

Loads config from ~/.claude/task-management-config/config.yaml
"""

import yaml
from pathlib import Path

CONFIG_DIR = Path.home() / ".claude" / "task-management-config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def get_config():
    """Load and return the configuration dictionary."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration not found at {CONFIG_FILE}\n"
            "Run /task-management:setup to configure the plugin."
        )
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def get_tasks_root():
    """Return the tasks root directory as a Path."""
    return Path(get_config()["paths"]["tasks_root"])


def get_folder(name):
    """Return the path to a specific folder within tasks root."""
    config = get_config()
    folder_name = config["folders"].get(name, name)
    return get_tasks_root() / folder_name


def get_all_task_dirs():
    """Return list of directories that may contain task files."""
    return [
        get_folder("tasks"),
        get_folder("ideas"),
        get_folder("bugs"),
        get_folder("import"),
    ]
