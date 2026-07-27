#!/usr/bin/env python3
"""
The YAML-subset parser.

Two audiences with opposite requirements: marker files, which we write and want
parsed deterministically, and legacy global configs, which are already in the wild
and may contain anything PyYAML accepts. The split is what lets new installs need no
packages while existing installs keep working.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import markerparse  # noqa: E402
from markerparse import ParseError, parse, parse_lenient  # noqa: E402

try:
    import yaml  # noqa: F401
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False


class TestParse(unittest.TestCase):
    def test_flat_keys_and_types(self):
        parsed = parse(
            "name: work\n"
            "count: 7\n"
            "enabled: true\n"
            "disabled: false\n"
            "missing: null\n"
        )
        self.assertEqual(parsed, {
            "name": "work", "count": 7,
            "enabled": True, "disabled": False, "missing": None,
        })

    def test_one_level_of_nesting(self):
        parsed = parse("folders:\n  tasks: todo\n  ideas: ideas\nlinks:\n  format: obsidian\n")
        self.assertEqual(parsed, {
            "folders": {"tasks": "todo", "ideas": "ideas"},
            "links": {"format": "obsidian"},
        })

    def test_quoted_values_keep_their_contents(self):
        parsed = parse('a: "/path/with spaces"\nb: \'single\'\nc: "has: colon"\n')
        self.assertEqual(parsed["a"], "/path/with spaces")
        self.assertEqual(parsed["b"], "single")
        self.assertEqual(parsed["c"], "has: colon")

    def test_comments_are_stripped_but_not_inside_quotes(self):
        """The setup wizard writes quoted paths, and a path may contain a '#'."""
        parsed = parse('# leading\na: value  # trailing\nb: "/path/with#hash"\n')
        self.assertEqual(parsed["a"], "value")
        self.assertEqual(parsed["b"], "/path/with#hash")

    def test_lists_in_both_forms(self):
        block = parse("tags:\n  - one\n  - two\n")
        inline = parse("tags: [one, two]\n")
        self.assertEqual(block["tags"], ["one", "two"])
        self.assertEqual(inline["tags"], ["one", "two"])

    def test_braces_mid_value_are_ordinary_text(self):
        """The default research digest template is a path containing `{date}`."""
        parsed = parse("integrations:\n  research_digest_path: ../Research/x/{date}.md\n")
        self.assertEqual(parsed["integrations"]["research_digest_path"],
                         "../Research/x/{date}.md")

    def test_rejects_a_third_level_of_nesting(self):
        with self.assertRaises(ParseError):
            parse("a:\n  b:\n    c: d\n")

    def test_rejects_anchors_and_aliases(self):
        with self.assertRaises(ParseError):
            parse("a: &anchor value\n")

    def test_rejects_an_unterminated_list(self):
        with self.assertRaises(ParseError):
            parse("tags: [one, two\n")

    def test_rejects_unparseable_lines(self):
        with self.assertRaises(ParseError):
            parse("this is not yaml at all\n")


class TestParseLenient(unittest.TestCase):
    """The legacy global config path: strict first, PyYAML as a fallback."""

    def test_the_shape_the_setup_wizard_writes_needs_no_fallback(self):
        """
        Every config written by /setup must parse strictly, or R5 is not actually
        met for the users who followed the documented path.
        """
        text = (
            'paths:\n  tasks_root: "/Users/someone/Vaults/Work/Tasks"\n\n'
            'folders:\n  tasks: "tasks"\n  ideas: "ideas"\n\n'
            'links:\n  format: "obsidian"\n\n'
            'integrations:\n  research_system: true\n'
        )
        self.assertEqual(parse(text)["paths"]["tasks_root"],
                         "/Users/someone/Vaults/Work/Tasks")

    @unittest.skipUnless(HAS_PYYAML, "PyYAML not installed")
    def test_strict_rejects_but_pyyaml_accepts(self):
        """
        Erroring on a config that works today would break exactly the users
        backward compatibility exists to protect.
        """
        text = 'paths:\n  tasks_root: "/p"\ndeep:\n  a:\n    b: c\n'
        with self.assertRaises(ParseError):
            parse(text)
        self.assertEqual(parse_lenient(text)["paths"]["tasks_root"], "/p")

    def test_both_parsers_reject_names_both_attempts(self):
        text = 'paths:\n  tasks_root: [unterminated\n'
        with self.assertRaises(ParseError) as caught:
            parse_lenient(text, source="config.yaml")
        message = str(caught.exception)
        self.assertIn("config.yaml", message)
        if HAS_PYYAML:
            self.assertIn("built-in parser", message)
            self.assertIn("PyYAML", message)


class TestFrontmatter(unittest.TestCase):
    def test_split_frontmatter_preserves_a_body_containing_a_rule(self):
        text = "---\nname: x\n---\n# Title\n\n---\n\nmore\n"
        frontmatter, body = markerparse.split_frontmatter(text)
        self.assertEqual(frontmatter.strip(), "name: x")
        self.assertIn("---", body)

    def test_no_frontmatter_returns_none(self):
        frontmatter, body = markerparse.split_frontmatter("# Just a heading\n")
        self.assertIsNone(frontmatter)
        self.assertEqual(body, "# Just a heading\n")


if __name__ == "__main__":
    unittest.main()
