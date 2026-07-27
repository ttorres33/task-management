#!/usr/bin/env python3
"""
show-config.py's printed output.

This is the only contract between the Python side and the markdown command files.
`commands/today.md` reads the `research:` line; `commands/setup.md` reads
`research_system_installed:`. Nothing enforces those names at runtime, so renaming a
key or reordering the output would silently stop every command working while the rest
of the suite stayed green.

These tests run the script as a subprocess and assert the exact key names, for that
reason. Testing config.research_capability() directly -- which test_capability.py
does -- proves the values are right but says nothing about what the commands read.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = TESTS_DIR.parent / "scripts" / "show-config.py"

sys.path.insert(0, str(TESTS_DIR))
from support import install_fake_research_system, marker, write  # noqa: E402


def run_show_config(cwd, home, *args):
    """Run show-config.py with a controlled environment. Returns (rc, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=str(cwd),
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )
    return result.returncode, result.stdout, result.stderr


def parse_lines(stdout):
    """Parse the `key: value` lines into a dict, ignoring the notice block."""
    fields = {}
    for line in stdout.split("\n"):
        if line.startswith("NOTICE:") or not line.strip():
            continue
        if ": " in line:
            key, value = line.split(": ", 1)
            fields[key] = value
    return fields


class ShowConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir(parents=True)
        self.root = self.tmp / "vault" / "Tasks"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write_marker(self, **integrations):
        write(self.root / "task-management-root.md",
              marker("test-root", integrations=integrations) if integrations
              else marker("test-root"))


class TestResolvedRootOutput(ShowConfigTestCase):
    def test_reports_root_name_source_and_link_format(self):
        self.write_marker()
        rc, stdout, stderr = run_show_config(self.root, self.home)

        self.assertEqual(rc, 0, stderr)
        fields = parse_lines(stdout)
        self.assertEqual(fields["root"], str(self.root))
        self.assertEqual(fields["name"], "test-root")
        self.assertEqual(fields["source"], "marker")
        self.assertEqual(fields["link_format"], "obsidian")
        self.assertIn("settings", fields)

    def test_no_root_exits_nonzero_with_an_actionable_message(self):
        rc, stdout, stderr = run_show_config(self.tmp / "home", self.home)

        self.assertNotEqual(rc, 0)
        self.assertIn("task-management-root.md", stderr)
        self.assertIn("/task-management:setup", stderr)


class TestResearchLine(ShowConfigTestCase):
    """The three values commands/today.md branches on."""

    def test_off(self):
        self.write_marker(research_system=False)
        _, stdout, _ = run_show_config(self.root, self.home)

        fields = parse_lines(stdout)
        self.assertEqual(fields["research"], "off")
        # Nothing to link, so no digest keys at all.
        self.assertNotIn("research_digest", fields)
        self.assertNotIn("NOTICE:", stdout)

    def test_generate_when_the_plugin_is_installed(self):
        self.write_marker(research_system=True)
        install_fake_research_system(self.home)
        _, stdout, _ = run_show_config(self.root, self.home, "--date", "2026-03-11")

        fields = parse_lines(stdout)
        self.assertEqual(fields["research"], "generate")
        self.assertTrue(fields["research_digest"].endswith("2026-03-11.md"))
        self.assertEqual(fields["research_digest_exists"], "no")
        self.assertNotIn("NOTICE:", stdout)

    def test_link_only_and_a_notice_when_the_plugin_is_missing(self):
        self.write_marker(research_system=True)
        _, stdout, _ = run_show_config(self.root, self.home, "--date", "2026-03-11")

        fields = parse_lines(stdout)
        self.assertEqual(fields["research"], "link-only")
        self.assertIn("NOTICE:", stdout)

    def test_digest_existence_is_reported(self):
        self.write_marker(research_system=True)
        digest = self.root.parent / "Research" / "daily-digests" / "2026-03-11.md"
        write(digest, "# Digest\n")
        _, stdout, _ = run_show_config(self.root, self.home, "--date", "2026-03-11")

        fields = parse_lines(stdout)
        self.assertEqual(fields["research_digest"], str(digest))
        self.assertEqual(fields["research_digest_exists"], "yes")


class TestDetectResearchFlag(ShowConfigTestCase):
    """Read by commands/setup.md, which runs before any root exists."""

    def test_reports_yes_when_installed(self):
        install_fake_research_system(self.home)
        rc, stdout, _ = run_show_config(self.tmp, self.home, "--detect-research")

        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "research_system_installed: yes")

    def test_reports_no_when_not_installed(self):
        rc, stdout, _ = run_show_config(self.tmp, self.home, "--detect-research")

        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), "research_system_installed: no")

    def test_succeeds_with_no_resolvable_root(self):
        """
        /setup runs this before the root exists, so it must not depend on
        resolution succeeding.
        """
        rc, stdout, stderr = run_show_config(self.tmp, self.home, "--detect-research")

        self.assertEqual(rc, 0, stderr)
        self.assertIn("research_system_installed", stdout)


if __name__ == "__main__":
    unittest.main()
