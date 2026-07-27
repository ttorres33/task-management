#!/usr/bin/env python3
"""
A minimal YAML-subset parser, so the plugin runs on stock system Python 3 with no
packages installed.

Deliberately NOT named frontmatter.py: that shadows the PyPI `python-frontmatter`
package, whose import name is `frontmatter`. Harmless while every script runs as
`python3 scripts/foo.py` and sys.path[0] wins, but the test suite manipulates
sys.path by hand, and on a machine with the third-party package installed an
appended scripts/ would load the wrong module.

Scope is bounded on purpose:

- Marker files use the strict parser only. We write them, so determinism beats
  tolerance -- a silently misparsed root means writing into the wrong task system.
- The legacy global config uses the strict parser and falls back to PyYAML when it
  is importable, because those files are already in the wild and may contain
  anything PyYAML accepts.
- Task file frontmatter is not parsed here at all. Pointing a strict parser at
  user-authored files would turn any unrecognized construct into a hard failure on
  a file someone wrote by hand.

Supported: comments, `key: value`, one level of nesting, `- list` items, inline
`[a, b]` lists, single/double quoted strings, booleans, null, and integers.
Anything else raises ParseError rather than guessing.
"""

import re


class ParseError(ValueError):
    """Raised when the strict parser meets a construct it does not support."""


_KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:(?P<rest>.*)$")
_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<value>.*)$")


def _strip_comment(text):
    """
    Remove a trailing `#` comment, respecting quotes.

    A `#` inside a quoted value is data, not a comment -- which matters because the
    setup wizard writes quoted paths and a path may legitimately contain one.
    """
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            return text[:i]
    return text


def _parse_scalar(raw):
    """Convert one right-hand-side token into a Python value."""
    value = _strip_comment(raw).strip()

    if value == "":
        return ""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner

    if value.startswith("["):
        if not value.endswith("]"):
            raise ParseError(f"unterminated list: {value!r}")
        body = value[1:-1].strip()
        if not body:
            return []
        return [_parse_scalar(part) for part in _split_inline(body)]

    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if lowered in ("null", "~"):
        return None

    if re.fullmatch(r"-?\d+", value):
        return int(value)

    # YAML's indicator characters only carry meaning at the start of a plain scalar:
    # an anchor (&x), alias (*x), tag (!!x), block scalar (|, >), flow mapping ({),
    # or directive (%). Mid-value they are ordinary text -- which matters, because
    # the default research digest template is `.../{date}.md`.
    if value[0] in "{}&*!|>%@`":
        raise ParseError(f"unsupported YAML construct in value: {value!r}")

    return value


def _split_inline(body):
    """Split `a, b, "c, d"` on commas that are not inside quotes."""
    parts, current, quote = [], [], None
    for ch in body:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            current.append(ch)
        elif ch == ",":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p for p in (p.strip() for p in parts) if p]


def parse(text):
    """
    Parse a YAML subset into a dict. Raises ParseError on anything unsupported.
    """
    result = {}
    current_key = None      # the top-level key currently being filled
    current_map = None      # its nested dict, if it has one
    current_list = None     # its list, if it has one

    for lineno, raw_line in enumerate(text.split("\n"), start=1):
        line = raw_line.rstrip()
        stripped = _strip_comment(line).strip()
        if not stripped:
            continue

        item = _ITEM_RE.match(line)
        if item:
            if current_list is None:
                if current_key is None:
                    raise ParseError(f"line {lineno}: list item outside any key")
                current_list = []
                result[current_key] = current_list
                current_map = None
            current_list.append(_parse_scalar(item.group("value")))
            continue

        match = _KEY_RE.match(line)
        if not match:
            raise ParseError(f"line {lineno}: cannot parse {raw_line!r}")

        indent = len(match.group("indent").expandtabs(2))
        key = match.group("key")
        rest = match.group("rest")
        has_value = _strip_comment(rest).strip() != ""

        if indent == 0:
            current_key = key
            current_list = None
            if has_value:
                result[key] = _parse_scalar(rest)
                current_map = None
            else:
                current_map = {}
                result[key] = current_map
            continue

        # Indented: a child of the current top-level key.
        if current_map is None:
            raise ParseError(
                f"line {lineno}: {key!r} is indented but {current_key!r} has a value; "
                "only one level of nesting is supported"
            )
        if not has_value:
            raise ParseError(
                f"line {lineno}: {key!r} opens a third level of nesting, which is "
                "not supported"
            )
        current_map[key] = _parse_scalar(rest)

    return result


def parse_lenient(text, source=""):
    """
    Parse with the strict parser, falling back to PyYAML if it is importable.

    For the legacy global config only. Those files predate this parser and may use
    constructs it rejects; erroring on a config that works today would break exactly
    the users backward compatibility exists to protect.
    """
    try:
        return parse(text)
    except ParseError as strict_error:
        try:
            import yaml
        except ImportError:
            raise ParseError(
                f"Could not parse {source or 'config'}: {strict_error}\n"
                "The built-in parser supports a subset of YAML. Either simplify the "
                "file, or install PyYAML (pip3 install pyyaml) so the fallback parser "
                "can be used."
            ) from strict_error

        try:
            loaded = yaml.safe_load(text)
        except Exception as yaml_error:
            raise ParseError(
                f"Could not parse {source or 'config'}.\n"
                f"  built-in parser: {strict_error}\n"
                f"  PyYAML:          {yaml_error}"
            ) from yaml_error

        return loaded if isinstance(loaded, dict) else {}


def split_frontmatter(text):
    """
    Return (frontmatter_text, body) for a `---` delimited document.

    Returns (None, text) when there is no frontmatter. Used to read marker files;
    task files keep their own line-based handling.
    """
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]


def load_frontmatter(path):
    """
    Parse the frontmatter of a Markdown file. Returns {} when there is none.
    Raises ParseError if the frontmatter exists but does not parse.
    """
    text = path.read_text(encoding="utf-8")
    frontmatter, _ = split_frontmatter(text)
    if frontmatter is None:
        return {}
    return parse(frontmatter)
