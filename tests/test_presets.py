"""
LinForge Test Suite - Presets Engine Tests
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from modules.presets import PresetsManager
from core.detector import SystemDetector
from core.runner import CommandRunner


class TestPresetsManager(unittest.TestCase):
    def setUp(self):
        self.detector = SystemDetector()
        self.runner = CommandRunner()
        self.presets_mgr = PresetsManager(detector=self.detector, runner=self.runner)

    def test_presets_catalog_loading(self):
        presets = self.presets_mgr.get_presets()
        self.assertIsInstance(presets, list)
        self.assertGreaterEqual(len(presets), 4)

        preset_ids = [p["id"] for p in presets]
        self.assertIn("preset_gaming", preset_ids)
        self.assertIn("preset_developer", preset_ids)
        self.assertIn("preset_debloat_privacy", preset_ids)
        self.assertIn("preset_creator", preset_ids)

    def test_preset_structure(self):
        presets = self.presets_mgr.get_presets()
        for p in presets:
            self.assertIn("id", p)
            self.assertIn("name", p)
            self.assertIn("tagline", p)
            self.assertIn("description", p)


if __name__ == "__main__":
    unittest.main()
