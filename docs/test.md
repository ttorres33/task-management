# Tests

Plain `unittest` from the standard library. Not pytest — this release exists partly to
remove a package dependency, so adding one back for the tests would be odd.

## Running

From the repo root:

```bash
python3 -m unittest discover -s tests -t . -p "test_*.py"
```

One file:

```bash
python3 -m unittest tests.test_resolution
```

One case:

```bash
python3 -m unittest tests.test_resolution.TestRootResolution.test_env_override_wins
```

The suite takes a couple of seconds and touches nothing outside temporary
directories.

## Layout

| File | Covers |
|---|---|
| `fixture.py` | Builds the throwaway tasks root every test runs against |
| `runner.py` | Runs the full `/today` pipeline against a fixture and snapshots the tree |
| `support.py` | Imports the plugin against a controlled `$HOME` / cwd / env |
| `baseline/` | Golden output captured from the pre-0.3.0 code |
| `test_regression.py` | Behavior preservation, hostile paths, acceptance checks |
| `test_resolution.py` | Root and settings resolution, marker validation |
| `test_markerparse.py` | The YAML-subset parser |
| `test_taskquery.py` | Query edge cases the fixture's filenames do not reach |
| `test_capability.py` | Research capability values and plugin detection |
| `test_showconfig.py` | `show-config.py`'s printed output — the Python↔markdown contract |

## The baseline is ground truth

`tests/baseline/` was captured from the code as it stood **before** any of the
multi-root work began, and committed in its own commit for that reason. It is the
evidence that the refactor did not change what users' files look like.

There are four baseline files: `daily.txt` / `imports.txt` in obsidian link format,
and `daily-markdown.txt` / `imports-markdown.txt` in markdown. Markdown gets its own
pair because `format_link` used to exist in three places with two different
signatures, and in obsidian mode all of them produced identical output — so only the
markdown baseline can prove the consolidation was faithful.

If a change makes `test_regression.py` fail, that change altered generated output or
altered users' task files. **Regenerating the baseline to make the test pass destroys
the only record of that.** Either fix the change, or — if the new behavior is
genuinely intended — regenerate deliberately and say so in the commit message:

```bash
python3 tests/runner.py --out tests/baseline
python3 tests/runner.py --out /tmp/md --link-format markdown   # then copy in, renamed
```

The markdown pair was captured from the pre-0.3.0 code the same way the obsidian
pair was: `git worktree add <dir> 384e3b8`, copy the current `tests/runner.py` and
`tests/fixture.py` into it (the harness is ours; the code under test is the
worktree's `scripts/`), and run it there.

## Why the fixture pins its own date

The generators read the clock, so a baseline captured against "today" would go stale
overnight. `fixture.REFERENCE_TODAY` fixes a date (a Wednesday, so "rest of this week"
is non-empty), writes every task's due date relative to it, and `runner.py` patches
the same date into the code under test. The committed baseline stays valid
indefinitely.

To inspect a fixture by hand instead of letting it evaporate:

```bash
python3 tests/runner.py --out /tmp/out --keep /tmp/fixture
python3 tests/runner.py --out /tmp/out --keep /tmp/fixture --hostile
```

## Why `runner.py` looks the way it does

Three constraints, all of which come from the code being tested rather than from the
tests:

- **`$HOME` is read at import time.** `config` resolves its paths when the module
  loads, so `$HOME` has to be set before the import, not before the call.
- **`generate-daily-files.py` is hyphenated** and therefore cannot be imported by
  name, so it is loaded by path. Fixing that is out of scope: the filename is a
  compatibility contract with personalized `/today` commands that locate it by name.
- **The pre-0.3.0 code spawned children.** `runner.py` prepends the running
  interpreter's directory to `$PATH` so `python3` in a child resolves to the same
  interpreter. Without it, a child could pick a Python without PyYAML, print the
  failure to stderr, and carry on — silently capturing a half-executed baseline as
  truth. `_assert_pipeline_really_ran` is the backstop for that.

Stdout is deliberately not part of the snapshot: 0.3.0 adds a resolved-root line to
every script, so stdout is *expected* to differ. The tree is what must not.

## The hostile fixture

`--hostile` puts the tasks root under `Vault With Space & Ampersand` and adds a task
file named `rick's completed errand.md`. Both broke the pre-0.3.0 code — archiving
silently did nothing, which matters because archiving moves files.

These are not regression cases. There is no baseline for them, because the old code
could not produce one.

## sys.path

`support.py` **prepends** `scripts/` to `sys.path`. It must never append it.

The parser module is named `markerparse.py` rather than `frontmatter.py` because the
latter is the import name of the PyPI `python-frontmatter` package. Prepending is what
guarantees our modules win on a machine that has third-party packages installed.

## Acceptance checks

Two tests exist to prove the cleanup is finished rather than partially done:

- `TestNoSubprocesses` — parses each script's AST and fails on any `import
  subprocess` or `shell=` keyword. AST rather than grep, so comments explaining why
  the child processes were removed do not read as violations.
- `TestStockPythonCompatibility` — imports every script under `/usr/bin/python3` with
  user site-packages disabled. This is the one that would have caught the original
  `import yaml`, which worked on the author's machine only because `python3` resolved
  through pyenv to an environment that happened to have PyYAML.
