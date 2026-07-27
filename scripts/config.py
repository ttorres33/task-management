#!/usr/bin/env python3
"""
Root and settings resolution for the task-management plugin.

The plugin supports any number of task systems on one machine. Which one a command
acts on is decided entirely by the working directory -- there are no flags and no
arguments.

Root resolution, in order:

    1. $TASK_MANAGEMENT_ROOT                     explicit override; also pins tests
    2. a valid marker searching upward from CWD  its folder IS the root
    3. a valid marker in a direct child of CWD   exactly one match wins
    4. global config default_root                or legacy paths.tasks_root
    5. actionable error                          how to fix, not just what failed

Steps 1-3 need no global config at all, which is what lets a second device, or a
person you share a vault with, work with nothing installed but the plugin.

Settings resolution is two steps, and never merges across sources:

    1. Resolve the root, as above.
    2. Load settings from that root: its marker if it has one, else the global
       config, else built-in defaults.

Resolving the root first and then asking that root what it wants is one rule. Tying
settings to *how* the root was found would give a single root two possible setting
sources depending on which directory Claude was launched from.
"""

import os
from pathlib import Path

import markerparse

# The marker's name and location are a compatibility contract with every synced
# vault. The `-root` suffix makes collision with an ordinary note far less likely
# than plain `task-management.md`, which is a plausible name for a note *about* task
# management -- including one sitting in a task system's own ideas/ folder.
MARKER_FILENAME = "task-management-root.md"

# A file is a marker only if it parses AND declares this key true. A file that merely
# has the right name is ignored, silently. Without that rule a stray note could hijack
# resolution, or brick every command by failing to parse.
#
# A dedicated key rather than a general one: `name:` alone is low-entropy enough that
# an ordinary note could carry it by coincidence -- including a note at
# ideas/task-management-root.md, which is exactly the collision the filename's `-root`
# suffix was chosen to make unlikely. Resolving to the wrong folder writes files
# there, and printing the resolved root afterwards is no guard against a write that
# already happened. Nothing in a vault has `task_management_root: true` by accident.
MARKER_KEY = "task_management_root"

# The root's human label. Optional -- it names the root in command output and defaults
# to the folder name. It is deliberately NOT what makes the file a marker.
NAME_KEY = "name"

CONFIG_DIR = Path.home() / ".claude" / "task-management-config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_FOLDERS = {
    "tasks": "tasks",
    "ideas": "ideas",
    "templates": "templates",
    "memories": "memories",
    "bugs": "bugs",
    "completed": "completed",
    "import": "import",
}
DEFAULT_LINK_FORMAT = "obsidian"

# Root-relative, with a {date} placeholder. Matches what research-system composes
# from its own config (research_root / daily-digests / {date}.md) for a Tasks folder
# sitting beside a Research folder in the same vault.
DEFAULT_RESEARCH_DIGEST_PATH = "../Research/daily-digests/{date}.md"

_resolution_cache = None
_settings_cache = None


# --------------------------------------------------------------------------- markers


def _declares_marker_key(data):
    """
    True if the frontmatter declares `task_management_root` true.

    Accepts the quoted spellings as well as the bare boolean, so a marker written by
    hand does not fail on a detail nobody should have to think about.
    """
    value = data.get(MARKER_KEY)
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes")
    return False


def inspect_marker(path):
    """
    Classify a file occupying the marker filename. Returns (status, payload):

        "absent"        no such file
        "unreadable"    exists but did not parse; payload is the reason
        "not-a-marker"  parses, but does not declare task_management_root
        "valid"         payload is the parsed frontmatter

    The distinction matters twice over. During resolution, anything but "valid" simply
    means "keep looking" -- a note that happens to share the filename must never
    hijack resolution, and must never be an error either. But when nothing resolves at
    all, a near-miss is by far the most useful thing to put in the error message, so
    the reason is preserved rather than collapsed into a bare None.
    """
    try:
        if not path.is_file():
            return "absent", None
        data = markerparse.load_frontmatter(path)
    except (markerparse.ParseError, OSError, UnicodeDecodeError) as error:
        return "unreadable", str(error)

    if not isinstance(data, dict) or not _declares_marker_key(data):
        return "not-a-marker", None
    return "valid", data


def read_marker(path):
    """Return a marker's parsed frontmatter, or None if `path` is not a valid marker."""
    status, payload = inspect_marker(path)
    return payload if status == "valid" else None


def _marker_in(directory, near_misses=None):
    """Return the marker data in `directory`, recording a near-miss if there is one."""
    path = directory / MARKER_FILENAME
    status, payload = inspect_marker(path)
    if status == "valid":
        return payload
    if near_misses is not None and status != "absent":
        near_misses.append((path, status, payload))
    return None


# ------------------------------------------------------------------------ resolution


def _resolve_from_env():
    raw = os.environ.get("TASK_MANAGEMENT_ROOT")
    if not raw:
        return None
    root = Path(raw).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(
            f"$TASK_MANAGEMENT_ROOT points at {root}, which is not a directory."
        )
    return root, "environment ($TASK_MANAGEMENT_ROOT)"


def _resolve_upward(start, near_misses=None):
    for directory in [start, *start.parents]:
        if _marker_in(directory, near_misses):
            return directory, "marker"
    return None


def _resolve_in_children(start, near_misses=None):
    """
    Look one level down for a marker.

    Upward search alone assumes Claude is launched inside the tasks folder. Someone
    opening Claude at their vault root instead would find nothing, which is the very
    first thing a person sharing a vault is likely to do. This must run before the
    global config, or standing in a second vault on a configured machine would
    resolve to the first vault.
    """
    try:
        children = sorted(p for p in start.iterdir() if p.is_dir())
    except OSError:
        return None

    matches = [child for child in children if _marker_in(child, near_misses)]
    if not matches:
        return None
    if len(matches) > 1:
        names = "\n".join(f"  - {m}" for m in matches)
        raise RuntimeError(
            f"{len(matches)} task systems found below {start}:\n{names}\n\n"
            "Run the command from inside the one you want, or set "
            "$TASK_MANAGEMENT_ROOT to choose."
        )
    return matches[0], "marker in child directory"


def _load_global_config():
    if not CONFIG_FILE.exists():
        return None
    text = CONFIG_FILE.read_text(encoding="utf-8")
    data = markerparse.parse_lenient(text, source=str(CONFIG_FILE))
    return data if isinstance(data, dict) else {}


def _resolve_from_global_config():
    data = _load_global_config()
    if not data:
        return None

    raw = data.get("default_root")
    if not raw:
        raw = (data.get("paths") or {}).get("tasks_root")
    if not raw:
        return None

    return Path(str(raw)).expanduser(), "global config"


def _no_root_error(start, near_misses=()):
    message = (
        "No task system found.\n\n"
        f"Searched for {MARKER_FILENAME} in {start} and every directory above it, "
        f"and in each of its immediate subdirectories.\n"
        f"Also checked {CONFIG_FILE}.\n"
    )

    if near_misses:
        message += "\nFound a file with that name, but it is not a marker:\n"
        for path, status, reason in near_misses:
            if status == "not-a-marker":
                message += (
                    f"  - {path}\n"
                    f"    Its frontmatter does not declare `{MARKER_KEY}: true`. Add "
                    "that line if\n    this really is a tasks root; otherwise ignore "
                    "this -- an ordinary note\n    sharing the filename is harmless.\n"
                )
            else:
                message += f"  - {path}\n    Could not be parsed: {reason}\n"

    message += (
        "\nTo fix this, do one of:\n"
        "  - Run /task-management:setup from inside your tasks folder.\n"
        f"  - Create {MARKER_FILENAME} in your tasks folder, containing at minimum:\n"
        "        ---\n"
        f"        {MARKER_KEY}: true\n"
        "        ---\n"
        "  - Set $TASK_MANAGEMENT_ROOT to your tasks folder for a one-off run.\n\n"
        "Or run the command from inside a tasks folder, or from the directory "
        "directly above one."
    )
    return FileNotFoundError(message)


def resolve_root():
    """Return (root_path, source_description). Cached for the life of the process."""
    global _resolution_cache
    if _resolution_cache is not None:
        return _resolution_cache

    start = Path.cwd()

    # Files that occupy the marker filename but are not markers. Collected only so a
    # failure can name them; they never affect resolution itself.
    near_misses = []

    resolved = (
        _resolve_from_env()
        or _resolve_upward(start, near_misses)
        or _resolve_in_children(start, near_misses)
        or _resolve_from_global_config()
    )
    if resolved is None:
        raise _no_root_error(start, near_misses)

    root, source = resolved
    if not root.is_dir():
        raise FileNotFoundError(
            f"Tasks root {root} does not exist (resolved from {source}).\n"
            "Create it, or update the source that points at it."
        )

    _resolution_cache = (root, source)
    return _resolution_cache


# -------------------------------------------------------------------------- settings


def _settings():
    """
    Return (settings_dict, settings_source) for the resolved root.

    Never merges. Whichever source wins supplies the whole set.
    """
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    root, _ = resolve_root()

    marker_path = root / MARKER_FILENAME
    status, payload = inspect_marker(marker_path)

    if status == "valid":
        _settings_cache = (payload, f"marker ({marker_path})")
        return _settings_cache

    if status == "unreadable":
        # Resolution tolerates an unparseable candidate, because there the question
        # is only "is this a marker?". Here we are committed to this root, and a
        # marker we cannot read would mean running with settings the user did not
        # choose -- so a parse failure is fatal and says so.
        raise markerparse.ParseError(
            f"{marker_path} could not be read as a marker file.\n"
            f"  {payload}\n\n"
            "Marker files support simple key/value pairs, one level of nesting, "
            "and lists. Fix the file, or delete it to fall back to the global "
            "config."
        )

    # "not-a-marker": it parses but does not declare task_management_root, so it is an
    # ordinary note that happens to share the filename. Fall through rather than fail
    # -- a note is not a broken marker.

    # A root with no marker falls back to the global config's settings even when
    # that config names a *different* root. This is the one path by which one root's
    # settings can reach another; the fix is to write the marker.
    global_config = _load_global_config()
    if global_config:
        _settings_cache = (global_config, f"global config ({CONFIG_FILE})")
        return _settings_cache

    _settings_cache = ({}, "built-in defaults")
    return _settings_cache


# ------------------------------------------------------------------------ public API


def get_tasks_root():
    """Return the resolved tasks root directory as a Path."""
    return resolve_root()[0]


def _validate_folder_name(key, value, source):
    """
    Check that a configured folder name is a plain name inside the root.

    This exists because of where markers come from. Before 0.3.0 every setting lived
    in ~/.claude/, owned by the user running the command. A marker file arrives over
    Obsidian Sync from whoever else has the vault -- that is the entire point of the
    sharing feature -- so `folders` values are now input from another machine.

    An entry like `completed: "../../../elsewhere"` would make /archive move a
    collaborator's task files out of the vault entirely, and clean-imports would
    happily mkdir the destination first. Far more likely than malice is a typo or a
    well-meant edit, and both fail the same way.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"folders.{key} in {source} must be a folder name, got {value!r}.\n"
            "Quote it if it looks like something else -- YAML reads bare `no` and "
            "`yes` as booleans."
        )
    if value != Path(value).name or value in (".", ".."):
        raise ValueError(
            f"folders.{key} in {source} must be a single folder name inside the "
            f"tasks root, not a path: {value!r}"
        )
    return value


def get_folder(name):
    """Return the path to a named folder within the tasks root."""
    settings, source = _settings()
    folders = settings.get("folders")
    if folders is None:
        folders = {}
    elif not isinstance(folders, dict):
        raise ValueError(
            f"`folders` in {source} must be a block of name/value pairs, "
            f"got {type(folders).__name__}."
        )

    if name in folders:
        folder_name = _validate_folder_name(name, folders[name], source)
    else:
        folder_name = DEFAULT_FOLDERS.get(name, name)

    return get_tasks_root() / folder_name


def get_all_task_dirs():
    """Return the directories that may contain task files."""
    return [get_folder(name) for name in ("tasks", "ideas", "bugs", "import")]


def get_link_format():
    """Return the link format: 'obsidian' or 'markdown'."""
    settings, _ = _settings()
    return (settings.get("links") or {}).get("format", DEFAULT_LINK_FORMAT)


def is_research_system_enabled():
    """Return True if research-system integration is enabled for this root."""
    settings, _ = _settings()
    return bool((settings.get("integrations") or {}).get("research_system", False))


def get_research_digest_path(date):
    """
    Return the digest path for `date`, resolved against the tasks root.

    The template deliberately escapes the root via `..`. It is used for an existence
    check and to build a link -- never written to, never created, never used to
    resolve a folder the plugin manages.
    """
    settings, source = _settings()
    template = (settings.get("integrations") or {}).get(
        "research_digest_path", DEFAULT_RESEARCH_DIGEST_PATH
    )
    try:
        relative = str(template).format(date=date)
    except (KeyError, IndexError) as error:
        raise ValueError(
            f"integrations.research_digest_path in {source} uses a placeholder this "
            f"plugin does not provide: {error}.\n"
            f"The only supported placeholder is {{date}}. Got: {template!r}"
        ) from error
    return Path(os.path.normpath(get_tasks_root() / relative))


def get_root_name():
    """
    Return this root's label, from its marker's `name`, or the folder name.

    `name` is optional: what makes a file a marker is MARKER_KEY, not this.
    """
    settings, _ = _settings()
    name = settings.get(NAME_KEY)
    return str(name) if name else get_tasks_root().name


def describe_root():
    """
    One line naming the resolved root and how it was found.

    Every script prints this before writing anything. With more than one task system
    on a machine, "which one did that just touch?" must never be a question.
    """
    root, source = resolve_root()
    return f"Tasks root: {root}  [{get_root_name()}, via {source}]"


def describe_settings_source():
    """Where this root's settings came from: its marker, the global config, or defaults."""
    return _settings()[1]


# ------------------------------------------------------- research-system capability


def research_system_installed():
    """
    True if the research-system plugin is available.

    Probes the real marketplace install path first. The pre-0.3.0 heuristic checked
    ~/.claude/plugins/research-system and ~/*/cc-plugins/research-system, neither of
    which matches how plugins are actually installed -- it only ever passed on a
    machine that happened to have a source checkout.
    """
    home = Path.home()
    candidates = [
        home / ".claude" / "plugins" / "cache",   # marketplace installs
        home / ".claude" / "plugins",             # older layout
    ]
    for base in candidates:
        if not base.is_dir():
            continue
        if (base / "research-system").is_dir():
            return True
        try:
            if any(base.glob("*/research-system")):
                return True
        except OSError:
            pass

    # Development fallback: a source checkout.
    try:
        return any(home.glob("*/cc-plugins/research-system"))
    except OSError:
        return False


def research_capability():
    """
    Resolve what /today should do about the research digest.

    Returns (capability, notice) where capability is one of:

        generate    the flag is on and research-system is installed
        link-only   the flag is on but research-system is not installed; a digest
                    that arrived by sync can still be linked
        off         the flag is off

    The flag gates both behaviors. Only the *generate* condition is capability
    derived. Gating the link on file existence alone would surface a digest link for
    users who set research_system: false.

    `notice` is a warning to print, or None. A false negative on detection would
    otherwise mean linking a stale digest every morning with no sign anything is
    wrong -- a failure mode that is invisible precisely because the output still
    looks right.
    """
    if not is_research_system_enabled():
        return "off", None

    if research_system_installed():
        return "generate", None

    return "link-only", (
        "NOTICE: integrations.research_system is true, but the research-system "
        "plugin was not found. An existing digest will still be linked, but no new "
        "one will be generated. If this machine does have research-system "
        "installed, this is a detection bug worth reporting."
    )
