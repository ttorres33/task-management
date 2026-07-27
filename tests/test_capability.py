#!/usr/bin/env python3
"""
The research-integration capability table, and the detection it rests on.

Detection is exercised against a real directory layout rather than a stubbed
function, because the bug this replaces was precisely a probe that looked at paths
plugins are not installed to. Mocking the probe would have let that bug survive.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import install_fake_research_system, marker, plugin_env, write  # noqa: E402


class TestResearchCapability(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def make_root(self, research_system):
        root = self.tmp / "vault" / "Tasks"
        root.mkdir(parents=True, exist_ok=True)
        write(root / "task-management-root.md",
              marker("test-root", integrations={"research_system": research_system}))
        return root

    def test_flag_on_and_plugin_installed_generates(self):
        root = self.make_root(True)
        install_fake_research_system(self.home)

        with plugin_env(cwd=root, home=self.home) as config:
            capability, notice = config.research_capability()
            self.assertEqual(capability, "generate")
            self.assertIsNone(notice)

    def test_flag_on_and_plugin_absent_links_only_and_warns(self):
        """
        The second device: the digest arrives by sync, so it can still be linked,
        but nothing regenerates it.

        The notice is the point. A false negative here would otherwise mean linking
        a stale digest every morning with no sign anything is wrong -- invisible
        precisely because the output still looks correct.
        """
        root = self.make_root(True)

        with plugin_env(cwd=root, home=self.home) as config:
            capability, notice = config.research_capability()
            self.assertEqual(capability, "link-only")
            self.assertIsNotNone(notice)
            self.assertIn("research-system", notice)

    def test_flag_off_is_off_even_with_the_plugin_installed(self):
        """
        Gating the link on file existence alone would surface a digest link for
        users who deliberately turned the integration off.
        """
        root = self.make_root(False)
        install_fake_research_system(self.home)

        with plugin_env(cwd=root, home=self.home) as config:
            capability, notice = config.research_capability()
            self.assertEqual(capability, "off")
            self.assertIsNone(notice)


class TestDetection(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.root = self.tmp / "vault" / "Tasks"
        self.root.mkdir(parents=True)
        write(self.root / "task-management-root.md", marker())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def detect(self):
        with plugin_env(cwd=self.root, home=self.home) as config:
            return config.research_system_installed()

    def test_marketplace_cache_path_is_found(self):
        """
        The real install path. The pre-0.3.0 heuristic checked
        ~/.claude/plugins/research-system and ~/*/cc-plugins/research-system --
        neither of which matches this, so it silently reported "not installed" for
        every user who installed the plugin the documented way.
        """
        install_fake_research_system(self.home, marketplace="teresa-torres-plugins")
        self.assertTrue(self.detect())

    def test_nothing_installed_is_not_found(self):
        self.assertFalse(self.detect())

    def test_an_unrelated_plugin_is_not_mistaken_for_it(self):
        (self.home / ".claude" / "plugins" / "cache" / "some-marketplace" / "other-plugin"
         ).mkdir(parents=True)
        self.assertFalse(self.detect())

    def test_source_checkout_fallback_for_development(self):
        (self.home / "Code" / "cc-plugins" / "research-system").mkdir(parents=True)
        self.assertTrue(self.detect())


if __name__ == "__main__":
    unittest.main()
