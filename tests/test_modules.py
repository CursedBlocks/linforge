"""
LinForge Test Suite - Feature Modules Unit Tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.detector import SystemDetector
from core.runner import CommandRunner
from modules.apps import AppManager
from modules.drivers import DriverManager
from modules.tweaks import TweaksManager
from modules.cleanup import CleanupManager
from modules.troubleshoot import TroubleshootManager
from modules.developer import DeveloperManager
from modules.maintenance import MaintenanceManager


class TestFeatureModules(unittest.TestCase):
    def setUp(self):
        self.detector = SystemDetector()
        self.runner = CommandRunner()
        self.apps_mgr = AppManager(detector=self.detector, runner=self.runner)
        self.tweaks_mgr = TweaksManager(detector=self.detector, runner=self.runner)
        self.trouble_mgr = TroubleshootManager(detector=self.detector, runner=self.runner)
        self.drivers_mgr = DriverManager(detector=self.detector, runner=self.runner)
        self.cleanup_mgr = CleanupManager(detector=self.detector, runner=self.runner)
        self.dev_mgr = DeveloperManager(detector=self.detector, runner=self.runner)
        self.maint_mgr = MaintenanceManager(detector=self.detector, runner=self.runner)

    def test_app_manager_methods(self):
        categories = self.apps_mgr.get_categories()
        self.assertIsInstance(categories, list)
        self.assertGreater(len(categories), 0)

        all_apps = self.apps_mgr.get_apps()
        self.assertIsInstance(all_apps, list)
        self.assertGreater(len(all_apps), 0)

        # Test search
        searched = self.apps_mgr.get_apps(search="code")
        self.assertGreater(len(searched), 0)

        # Test category filter
        browsers = self.apps_mgr.get_apps(category="browsers")
        self.assertGreater(len(browsers), 0)

    def test_tweaks_manager_methods(self):
        categories = self.tweaks_mgr.get_categories()
        self.assertIsInstance(categories, list)
        self.assertGreater(len(categories), 0)

        tweaks = self.tweaks_mgr.get_tweaks()
        self.assertIsInstance(tweaks, list)
        self.assertGreater(len(tweaks), 0)

    def test_troubleshoot_manager_methods(self):
        troubleshooters = self.trouble_mgr.get_troubleshooters()
        self.assertIsInstance(troubleshooters, list)
        self.assertGreater(len(troubleshooters), 0)
        self.assertIn("status", troubleshooters[0])

    def test_drivers_manager_hardware_status(self):
        hw = self.drivers_mgr.get_hardware_status()
        self.assertIsInstance(hw, dict)
        self.assertIn("gpus", hw)
        self.assertIn("audio", hw)
        self.assertIn("wifi", hw)


if __name__ == "__main__":
    unittest.main()
