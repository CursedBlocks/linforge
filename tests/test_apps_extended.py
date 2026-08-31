"""
LinForge Test Suite - App Manager Extended Tests (Installed Check & Fallbacks)
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from modules.apps import AppManager
from core.detector import SystemDetector
from core.runner import CommandRunner


class TestAppsExtended(unittest.TestCase):
    def setUp(self):
        self.detector = SystemDetector()
        self.runner = CommandRunner()
        self.apps_mgr = AppManager(detector=self.detector, runner=self.runner)

    def test_catalog_loading_and_categories(self):
        cats = self.apps_mgr.get_categories()
        self.assertIsInstance(cats, list)
        self.assertGreater(len(cats), 0)

        apps = self.apps_mgr.get_apps()
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 50)

    def test_installed_state_properties(self):
        apps = self.apps_mgr.get_apps()
        for app in apps:
            self.assertIn("is_installed", app)
            self.assertIn("installed_source", app)
            self.assertIsInstance(app["is_installed"], bool)
            self.assertIsInstance(app["installed_source"], str)

    def test_python3_installed_detection(self):
        # Python should be detected as binary or native
        installed, src = self.apps_mgr.pkg_mgr.is_package_installed("python3")
        # On all developer machines, python3 or python executable is in PATH
        self.assertTrue(installed)

    def test_unknown_app_install(self):
        res = self.apps_mgr.install_app("non_existent_app_12345")
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_APP_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
