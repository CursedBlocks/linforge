"""
LinForge Test Suite - Command Runner & Error Classification Unit Tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.runner import CommandRunner, CommandResult


class TestCommandRunner(unittest.TestCase):
    def setUp(self):
        self.runner = CommandRunner()

    def test_run_simple_command(self):
        lines_received = []

        def cb(stream_type, msg):
            lines_received.append((stream_type, msg))

        # Use a portable python command
        res = self.runner.run_command(
            f'"{sys.executable}" -c "print(\'LinForge Test Output\')"',
            callback=cb
        )
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("LinForge Test Output", res.stdout)
        self.assertGreater(len(lines_received), 0)

    def test_command_result_to_dict(self):
        res = CommandResult(exit_code=0, stdout="hello", stderr="", duration=1.23, cancelled=False)
        d = res.to_dict()
        self.assertEqual(d["exit_code"], 0)
        self.assertTrue(d["success"])
        self.assertEqual(d["stdout"], "hello")
        self.assertEqual(d["duration"], 1.23)
        self.assertEqual(d["error_code"], "SUCCESS")

    def test_error_classification_dpkg_lock(self):
        res = CommandResult(
            exit_code=100,
            stdout="",
            stderr="E: Could not get lock /var/lib/dpkg/lock-frontend - open (11: Resource temporarily unavailable)",
            duration=0.5
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_DPKG_LOCKED")
        self.assertIn("Locked", res.error_title)
        self.assertIn("Troubleshooter", res.error_suggestion)

    def test_error_classification_unmet_deps(self):
        res = CommandResult(
            exit_code=1,
            stdout="",
            stderr="dpkg: dependency problems prevent configuration of discord:\n discord depends on libasound2 (>= 1.0.16); however: Package libasound2 is not installed.",
            duration=0.8
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_DEPENDENCY_MISSING")
        self.assertIn("Dependencies", res.error_title)

    def test_error_classification_fuse_missing(self):
        res = CommandResult(
            exit_code=127,
            stdout="",
            stderr="dlopen(): error loading libfuse.so.2: cannot open shared object file: No such file or directory",
            duration=0.2
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_FUSE_MISSING")
        self.assertIn("FUSE2", res.error_title)

    def test_error_classification_permission_denied(self):
        res = CommandResult(
            exit_code=1,
            stdout="",
            stderr="E: Could not open lock file /var/lib/dpkg/lock - open (13: Permission denied)\nE: Unable to lock the administration directory (/var/lib/dpkg/), are you root?",
            duration=0.1
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
