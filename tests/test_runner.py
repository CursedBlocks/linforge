"""
LinForge Test Suite - Command Runner & Execution Unit Tests
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


if __name__ == "__main__":
    unittest.main()
