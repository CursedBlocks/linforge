"""
LinForge Test Suite - System Detector Unit Tests
"""

import os
import sys
import unittest

# Ensure src is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.detector import SystemDetector
from core.system_info import SystemMonitor


class TestSystemDetector(unittest.TestCase):
    def setUp(self):
        self.detector = SystemDetector()
        self.monitor = SystemMonitor()

    def test_distro_info_structure(self):
        info = self.detector.get_distro_info()
        self.assertIsInstance(info, dict)
        self.assertIn("id", info)
        self.assertIn("name", info)
        self.assertIn("pretty_name", info)
        self.assertIn("family", info)
        self.assertIn("kernel", info)
        self.assertIn("architecture", info)
        self.assertIn("is_kubuntu", info)
        self.assertIn("is_ubuntu_based", info)

    def test_desktop_environment_structure(self):
        de = self.detector.get_desktop_environment()
        self.assertIsInstance(de, dict)
        self.assertIn("name", de)
        self.assertIn("version", de)
        self.assertIn("session_type", de)
        self.assertIn("is_wayland", de)
        self.assertIn("is_x11", de)

    def test_package_managers_detection(self):
        pkgs = self.detector.get_package_managers()
        self.assertIsInstance(pkgs, dict)
        self.assertIn("apt", pkgs)
        self.assertIn("flatpak", pkgs)
        self.assertIn("snap", pkgs)

    def test_gpu_info_structure(self):
        gpus = self.detector.get_gpu_info()
        self.assertIsInstance(gpus, list)
        self.assertGreater(len(gpus), 0)
        self.assertIn("vendor", gpus[0])
        self.assertIn("driver", gpus[0])

    def test_audio_subsystem_structure(self):
        audio = self.detector.get_audio_subsystem()
        self.assertIsInstance(audio, dict)
        self.assertIn("primary", audio)

    def test_system_monitor_metrics(self):
        metrics = self.monitor.get_all_metrics()
        self.assertIn("cpu", metrics)
        self.assertIn("memory", metrics)
        self.assertIn("disks", metrics)
        self.assertIn("network", metrics)
        self.assertIn("uptime", metrics)


if __name__ == "__main__":
    unittest.main()
