#!/usr/bin/env python3
"""
Root and settings resolution.

The interesting cases are the ones where a wrong answer is silent: resolving to the
wrong task system, or inheriting settings from one root into another. Those write
files, so "it printed something odd" is not the failure mode -- "it wrote into the
wrong vault" is.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402
from support import marker, plugin_env, write  # noqa: E402

LEGACY_CONFIG = """paths:
  tasks_root: "{root}"

folders:
  tasks: "tasks"
  ideas: "ideas"
  templates: "templates"
  memories: "memories"
  bugs: "bugs"
  completed: "completed"
  import: "import"

links:
  format: "markdown"

integrations:
  research_system: true
"""


class ResolutionTestCase(unittest.TestCase):
    def setUp(self):
        # Resolved, because Path.cwd() resolves symlinks and /var is one on macOS.
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def make_root(self, path, with_marker=True, **marker_sections):
        root = self.tmp / path
        root.mkdir(parents=True, exist_ok=True)
        if with_marker:
            name = marker_sections.pop("name", "test-root")
            write(root / "task-management-root.md", marker(name, **marker_sections))
        return root

    def write_global_config(self, root, template=LEGACY_CONFIG):
        return write(
            self.home / ".claude" / "task-management-config" / "config.yaml",
            template.format(root=root),
        )


class TestRootResolution(ResolutionTestCase):
    def test_marker_upward_with_no_global_config(self):
        """R3/R8: a marker alone resolves, with nothing else installed."""
        root = self.make_root("vault/Tasks")
        deep = root / "tasks"
        deep.mkdir()

        with plugin_env(cwd=deep, home=self.home) as config:
            resolved, source = config.resolve_root()
            self.assertEqual(resolved, root)
            self.assertEqual(source, "marker")

    def test_marker_in_direct_child_from_vault_root(self):
        """
        R3: someone handed a shared vault opens Claude at the vault root, not inside
        the tasks folder. Upward search finds nothing there, so the downward probe is
        what makes a zero-configuration install work on the very first interaction.
        """
        vault = self.tmp / "vault"
        root = self.make_root("vault/Tasks")
        (vault / "Recipes").mkdir(parents=True, exist_ok=True)

        with plugin_env(cwd=vault, home=self.home) as config:
            resolved, source = config.resolve_root()
            self.assertEqual(resolved, root)
            self.assertEqual(source, "marker in child directory")

    def test_marker_named_file_with_unrelated_frontmatter_is_ignored(self):
        """
        A note that merely shares the marker's filename must not resolve, and must
        not error either. In an Obsidian vault this is an entirely plausible name for
        an ordinary note.
        """
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md",
              "---\ntags: [meta]\ncreated: 2026-01-01\n---\n# Notes on task management\n")

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(FileNotFoundError):
                config.resolve_root()

    def test_a_note_carrying_only_a_name_key_is_not_a_marker(self):
        """
        The reason validity keys on `task_management_root` rather than on `name`.

        `name:` is low-entropy enough to appear in an ordinary note by coincidence --
        including a note at ideas/task-management-root.md, which is exactly the
        collision the filename's `-root` suffix was chosen to make unlikely. Resolving
        there would make /today write three files into ideas/.
        """
        ideas = self.tmp / "vault" / "Tasks" / "ideas"
        ideas.mkdir(parents=True)
        write(ideas / "task-management-root.md",
              "---\nname: task management root\ntags: [meta]\n---\n"
              "# Thoughts on how I organize tasks\n")

        with plugin_env(cwd=ideas, home=self.home) as config:
            with self.assertRaises(FileNotFoundError):
                config.resolve_root()

    def test_a_near_miss_is_named_in_the_error(self):
        """
        Silently ignoring a would-be marker is right for resolution but unhelpful on
        failure. Someone who wrote the file by hand and omitted the key would
        otherwise get "no task system found" while staring at the file they just made.
        """
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md", "---\nname: my-tasks\n---\n# Root\n")

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(FileNotFoundError) as caught:
                config.resolve_root()

        message = str(caught.exception)
        self.assertIn(str(root / "task-management-root.md"), message)
        self.assertIn("task_management_root: true", message)

    def test_stray_marker_named_note_beside_a_real_marker(self):
        """
        A naming coincidence must not become an ambiguity error. Only two *valid*
        markers are genuinely ambiguous.
        """
        vault = self.tmp / "vault"
        real = self.make_root("vault/Tasks")
        stray = vault / "Notes"
        stray.mkdir(parents=True, exist_ok=True)
        write(stray / "task-management-root.md",
              "---\nname: notes\ntags: [meta]\n---\n# A note that shares the name\n")

        with plugin_env(cwd=vault, home=self.home) as config:
            resolved, _ = config.resolve_root()
            self.assertEqual(resolved, real)

    def test_the_marker_flag_accepts_quoted_spellings(self):
        """A marker written by hand should not fail on a detail nobody thinks about."""
        for index, spelling in enumerate(['true', '"true"', 'yes']):
            with self.subTest(spelling):
                root = self.tmp / "vault-{}".format(index) / "Tasks"
                root.mkdir(parents=True, exist_ok=True)
                write(root / "task-management-root.md",
                      f"---\ntask_management_root: {spelling}\n---\n")

                with plugin_env(cwd=root, home=self.home) as config:
                    self.assertEqual(config.resolve_root()[0], root)

    def test_the_marker_flag_set_false_is_not_a_marker(self):
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md",
              "---\ntask_management_root: false\nname: disabled\n---\n")

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(FileNotFoundError):
                config.resolve_root()

    def test_name_is_optional(self):
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md", "---\ntask_management_root: true\n---\n")

        with plugin_env(cwd=root, home=self.home) as config:
            self.assertEqual(config.resolve_root()[0], root)
            self.assertEqual(config.get_root_name(), "Tasks")  # falls back to folder

    def test_two_valid_markers_in_children_is_ambiguous(self):
        vault = self.tmp / "vault"
        self.make_root("vault/Work", name="work")
        self.make_root("vault/Household", name="household")

        with plugin_env(cwd=vault, home=self.home) as config:
            with self.assertRaises(RuntimeError) as caught:
                config.resolve_root()
            self.assertIn("TASK_MANAGEMENT_ROOT", str(caught.exception))

    def test_legacy_global_config_with_no_marker(self):
        """R4: an existing user's config keeps working, untouched."""
        root = self.make_root("vault/Tasks", with_marker=False)
        self.write_global_config(root)
        elsewhere = self.tmp / "some-code-project"
        elsewhere.mkdir()

        with plugin_env(cwd=elsewhere, home=self.home) as config:
            resolved, source = config.resolve_root()
            self.assertEqual(resolved, root)
            self.assertEqual(source, "global config")

    def test_default_root_router_key(self):
        """The reduced global config -- a router holding only default_root."""
        root = self.make_root("vault/Tasks", with_marker=False)
        self.write_global_config(root, 'default_root: "{root}"\n')
        elsewhere = self.tmp / "some-code-project"
        elsewhere.mkdir()

        with plugin_env(cwd=elsewhere, home=self.home) as config:
            self.assertEqual(config.resolve_root()[0], root)

    def test_env_override_wins(self):
        chosen = self.make_root("vault/Chosen", name="chosen")
        other = self.make_root("vault/Other", name="other")
        self.write_global_config(other)

        with plugin_env(cwd=other, home=self.home, root_override=chosen) as config:
            resolved, source = config.resolve_root()
            self.assertEqual(resolved, chosen)
            self.assertIn("TASK_MANAGEMENT_ROOT", source)

    def test_marker_beats_global_config_pointing_elsewhere(self):
        """
        Standing inside one vault while the global config names another must resolve
        to the one you are standing in -- otherwise a second task system silently
        writes into the first.
        """
        work = self.make_root("vault/Work", name="work")
        household = self.make_root("vault/Household", name="household")
        self.write_global_config(work)

        with plugin_env(cwd=household, home=self.home) as config:
            self.assertEqual(config.resolve_root()[0], household)

    def test_no_root_anywhere_gives_an_actionable_error(self):
        """
        The message has to stand on its own: on a second device there is no global
        config to enumerate known roots from.
        """
        nowhere = self.tmp / "unrelated-project"
        nowhere.mkdir()

        with plugin_env(cwd=nowhere, home=self.home) as config:
            with self.assertRaises(FileNotFoundError) as caught:
                config.resolve_root()

        message = str(caught.exception)
        self.assertIn("task-management-root.md", message)
        self.assertIn("/task-management:setup", message)
        self.assertIn("TASK_MANAGEMENT_ROOT", message)

    def test_tasks_subfolder_alone_does_not_resolve(self):
        """
        A bare tasks/ subfolder must NOT be treated as a root. `tasks/` is an
        ordinary directory name -- every Ansible role has one -- and the commands
        that would be "helped" by such a fallback all write files.
        """
        project = self.tmp / "some-ansible-role"
        (project / "tasks").mkdir(parents=True)

        with plugin_env(cwd=project, home=self.home) as config:
            with self.assertRaises(FileNotFoundError):
                config.resolve_root()


class TestSettingsResolution(ResolutionTestCase):
    def test_marker_folders_win_regardless_of_how_the_root_was_found(self):
        """
        Settings follow the root, not the resolution path. The same root must behave
        identically whether it was found by marker, by env var, or by config.
        """
        root = self.make_root(
            "vault/Tasks",
            folders={"tasks": "todo", "completed": "done"},
            links={"format": "obsidian"},
        )
        self.write_global_config(root)  # says markdown, and folders: tasks

        for description, kwargs in [
            ("resolved by marker", {"cwd": root}),
            ("resolved by env override", {"cwd": self.tmp, "root_override": root}),
        ]:
            with self.subTest(description):
                with plugin_env(home=self.home, **kwargs) as config:
                    self.assertEqual(config.get_folder("tasks"), root / "todo")
                    self.assertEqual(config.get_folder("completed"), root / "done")
                    self.assertEqual(config.get_link_format(), "obsidian")

    def test_marker_omitting_folders_uses_built_in_defaults_not_the_global_config(self):
        """Settings never merge: a marker with no `folders` block gets the defaults."""
        root = self.make_root("vault/Tasks", links={"format": "obsidian"})
        self.write_global_config(root)

        with plugin_env(cwd=root, home=self.home) as config:
            self.assertEqual(config.get_folder("tasks"), root / "tasks")
            self.assertEqual(config.get_link_format(), "obsidian")
            self.assertFalse(config.is_research_system_enabled())

    def test_markerless_root_inherits_the_global_config_naming_another_root(self):
        """
        The one documented cross-root case. A root with no marker falls back to the
        global config's settings even when that config names a different root. This
        is intended -- the global config is the settings fallback of last resort --
        but it is the single path by which one root's settings reach another, and the
        fix is to write the marker.
        """
        work = self.make_root("vault/Work", with_marker=False)
        household = self.make_root("vault/Household", with_marker=False)
        self.write_global_config(work)  # markdown links, research on, folders as named

        with plugin_env(cwd=self.tmp, home=self.home, root_override=household) as config:
            self.assertEqual(config.resolve_root()[0], household)
            self.assertEqual(config.get_link_format(), "markdown")
            self.assertTrue(config.is_research_system_enabled())

    def test_no_marker_and_no_global_config_uses_defaults(self):
        root = self.make_root("vault/Tasks", with_marker=False)

        with plugin_env(cwd=self.tmp, home=self.home, root_override=root) as config:
            self.assertEqual(config.get_link_format(), "obsidian")
            self.assertEqual(config.get_folder("ideas"), root / "ideas")
            self.assertEqual(config.describe_settings_source(), "built-in defaults")

    def test_unparseable_marker_at_a_resolved_root_is_fatal(self):
        """
        Silently ignoring it would mean running with settings the user did not
        choose -- and writing files accordingly.

        The root is pinned rather than discovered, because during *resolution* an
        unparseable file is simply not a marker and search moves on. The strict
        behavior applies once we are committed to a root.
        """
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md",
              "---\ntask_management_root: true\nfolders:\n  nested:\n    too: deep\n---\n")

        with plugin_env(cwd=self.tmp, home=self.home, root_override=root) as config:
            markerparse = support.import_plugin_module("markerparse")
            with self.assertRaises(markerparse.ParseError) as caught:
                config.get_link_format()
            self.assertIn("task-management-root.md", str(caught.exception))

    def test_marker_named_note_at_a_resolved_root_falls_through(self):
        """
        A file that parses but carries no `name:` key is an ordinary note that
        happens to share the filename, not a broken marker. It must not be fatal.
        """
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md", "---\ntags: [meta]\n---\n# A note\n")
        self.write_global_config(root)

        with plugin_env(cwd=self.tmp, home=self.home, root_override=root) as config:
            self.assertEqual(config.get_link_format(), "markdown")  # from global config

    def test_a_folder_name_escaping_the_root_is_rejected(self):
        """
        Markers arrive over sync from whoever else has the vault, so `folders` values
        are input from another machine. A value like "../../elsewhere" would make
        /archive move a collaborator's task files out of the vault entirely -- and
        clean-imports would mkdir the destination first. A typo does this as
        readily as malice.
        """
        root = self.make_root("vault/Tasks", folders={"completed": "../../../escaped"})

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(ValueError) as caught:
                config.get_folder("completed")
            self.assertIn("completed", str(caught.exception))

    def test_a_folder_name_that_is_a_subpath_is_rejected(self):
        root = self.make_root("vault/Tasks", folders={"tasks": "a/b"})

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(ValueError):
                config.get_folder("tasks")

    def test_an_unquoted_no_is_rejected_rather_than_becoming_a_boolean(self):
        """
        YAML reads bare `no` as False, which would otherwise reach `root / False` and
        surface as a bare TypeError instead of a message naming the key.
        """
        root = self.make_root("vault/Tasks", with_marker=False)
        write(root / "task-management-root.md",
              "---\ntask_management_root: true\nfolders:\n  tasks: no\n---\n")

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(ValueError) as caught:
                config.get_folder("tasks")
            self.assertIn("tasks", str(caught.exception))

    def test_an_unknown_digest_placeholder_names_the_key(self):
        root = self.make_root(
            "vault/Tasks",
            integrations={"research_system": True,
                          "research_digest_path": "../R/{year}/{date}.md"},
        )

        with plugin_env(cwd=root, home=self.home) as config:
            with self.assertRaises(ValueError) as caught:
                config.get_research_digest_path("2026-03-11")
            self.assertIn("research_digest_path", str(caught.exception))

    def test_research_digest_path_resolves_relative_to_the_root(self):
        root = self.make_root(
            "vault/Tasks",
            integrations={"research_system": True,
                          "research_digest_path": "../Research/daily-digests/{date}.md"},
        )

        with plugin_env(cwd=root, home=self.home) as config:
            digest = config.get_research_digest_path("2026-03-11")
            self.assertEqual(digest, root.parent / "Research/daily-digests/2026-03-11.md")
            self.assertNotIn("..", str(digest))


if __name__ == "__main__":
    unittest.main()
