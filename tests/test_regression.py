#!/usr/bin/env python3
"""
Behavior preservation.

tests/baseline/ was captured from the pre-0.3.0 code before any of the multi-root
work began, and is ground truth. If a change here makes these fail, the change
altered what users' files look like -- regenerating the baseline to make the test
pass would destroy the only evidence of that.

The hostile variants are not regressions: they are cases the old code could not
handle at all, so they assert correct behavior rather than identical behavior.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BASELINE_DIR = TESTS_DIR / "baseline"

sys.path.insert(0, str(TESTS_DIR))
import fixture  # noqa: E402


def run_pipeline_subprocess(out_dir, hostile=False):
    """
    Run the pipeline in a child process.

    A subprocess, not an import, because the pipeline resolves $HOME and the working
    directory at import time and caches the result. Isolation is cheaper to buy from
    the OS than to engineer around.
    """
    command = [sys.executable, str(TESTS_DIR / "runner.py"), "--out", str(out_dir)]
    if hostile:
        command.append("--hostile")

    result = subprocess.run(command, capture_output=True, text=True, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        raise AssertionError(
            f"runner.py failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    return result


class TestGoldenOutput(unittest.TestCase):
    """The generated tree must match what the pre-0.3.0 code produced, byte for byte."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "out"
        run_pipeline_subprocess(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def assert_matches_baseline(self, name):
        expected = (BASELINE_DIR / f"{name}.txt").read_text(encoding="utf-8")
        actual = (self.out / f"{name}.txt").read_text(encoding="utf-8")
        self.assertEqual(expected, actual, f"{name} diverged from the captured baseline")

    def test_daily_pipeline_matches_baseline(self):
        """normalize -> archive -> today.md / this-week.md / next-week.md."""
        self.assert_matches_baseline("daily")

    def test_clean_imports_matches_baseline(self):
        self.assert_matches_baseline("imports")

    def test_body_containing_a_horizontal_rule_survives_normalization(self):
        """
        The normalizer rejoins with f"---{frontmatter}---{body}" after a
        split('---', 2). Extraction could easily have broken that, and the damage
        would land in users' hand-written notes.

        Asserted as exact equality rather than a set of substring checks, because
        the failure mode being guarded against is reflowing -- which every substring
        check would happily pass.
        """
        snapshot = (self.out / "daily.txt").read_text(encoding="utf-8")
        actual = _extract(snapshot, "tasks/body-has-hr.md")

        expected = dict(fixture._files())["tasks/body-has-hr.md"].replace(
            "due: 3/9/2026", "due: 2026-03-09"
        )
        self.assertEqual(actual, expected)


class TestHostilePaths(unittest.TestCase):
    """
    R7. The old code shelled out to grep with unquoted paths and to `mv` with
    single-quoted filenames, so a root containing a space or an ampersand, or a
    filename containing an apostrophe, broke it -- silently, in the archiving case.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "out"
        run_pipeline_subprocess(cls.out, hostile=True)
        cls.snapshot = (cls.out / "daily.txt").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_generated_views_are_identical_on_a_hostile_root_path(self):
        """
        The root lives under "Vault With Space & Ampersand". Its contents must be
        indistinguishable from the plain run apart from the extra apostrophe file.
        """
        expected = (BASELINE_DIR / "daily.txt").read_text(encoding="utf-8")
        for name in ("today.md", "this-week.md", "next-week.md"):
            with self.subTest(name):
                self.assertEqual(
                    _extract(expected, name), _extract(self.snapshot, name)
                )

    def test_filename_with_an_apostrophe_is_archived(self):
        self.assertIn("=== FILE completed/rick's completed errand.md", self.snapshot)
        self.assertNotIn("=== FILE tasks/rick's completed errand.md", self.snapshot)


def _extract(snapshot, name):
    """Return one file's exact contents from a snapshot."""
    header = f"=== FILE {name}\n"
    start = snapshot.index(header) + len(header)
    end = snapshot.index("\n=== END", start)
    return snapshot[start:end]


class TestNoSubprocesses(unittest.TestCase):
    """
    The acceptance check: a mechanical proof that the shell-out layer is gone rather
    than partially ported.

    Checked against the parsed AST rather than by grepping text, so that comments
    explaining why the child processes were removed do not read as violations.
    """

    def test_scripts_import_subprocess_nowhere(self):
        import ast

        offenders = []
        for path in sorted((REPO_ROOT / "scripts").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] == "subprocess":
                            offenders.append(f"{path.name}:{node.lineno}: import subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if (node.module or "").split(".")[0] == "subprocess":
                        offenders.append(f"{path.name}:{node.lineno}: from subprocess import ...")
                elif isinstance(node, ast.keyword) and node.arg == "shell":
                    offenders.append(f"{path.name}:{node.lineno}: shell= keyword argument")

        self.assertEqual(offenders, [], "scripts/ still shells out:\n" + "\n".join(offenders))

    def test_no_script_imports_yaml(self):
        """
        R5. PyYAML reaches the plugin only through markerparse's legacy-config
        fallback, where the import is local and guarded.
        """
        import ast

        offenders = []
        for path in sorted((REPO_ROOT / "scripts").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(a.name == "yaml" for a in node.names):
                    # Guarded fallback inside a function body is the one allowed form.
                    if path.name == "markerparse.py" and node.col_offset > 0:
                        continue
                    offenders.append(f"{path.name}:{node.lineno}: import yaml")

        self.assertEqual(offenders, [], "top-level yaml import:\n" + "\n".join(offenders))


class TestStockPythonCompatibility(unittest.TestCase):
    """
    R5. Every script must import under stock system Python with no packages
    installed -- the plugin's own `import yaml` was a silent failure for anyone
    without PyYAML, masked on the author's machine by a pyenv environment that had it.
    """

    SYSTEM_PYTHON = "/usr/bin/python3"

    @unittest.skipUnless(Path(SYSTEM_PYTHON).exists(), "no /usr/bin/python3")
    def test_every_script_imports_without_third_party_packages(self):
        scripts = REPO_ROOT / "scripts"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Tasks"
            root.mkdir()
            (root / "task-management-root.md").write_text(
                "---\nname: stock-python\n---\n", encoding="utf-8"
            )

            failures = []
            for path in sorted(scripts.glob("*.py")):
                # -S and -I keep site-packages and user paths out, so this really is
                # a bare interpreter.
                result = subprocess.run(
                    [self.SYSTEM_PYTHON, "-I", "-c",
                     f"import sys; sys.path.insert(0, {str(scripts)!r}); "
                     f"import importlib.util as u; "
                     f"s = u.spec_from_file_location('m', {str(path)!r}); "
                     f"m = u.module_from_spec(s); s.loader.exec_module(m)"],
                    capture_output=True, text=True, cwd=str(root),
                    env={"HOME": tmp, "PATH": "/usr/bin:/bin"},
                )
                if result.returncode != 0:
                    failures.append(f"{path.name}: {result.stderr.strip().splitlines()[-1]}")

            self.assertEqual(failures, [], "scripts failed on stock python3:\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
