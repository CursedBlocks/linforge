"""
LinForge Test Suite - Embedded Server & REST API Tests
"""

import json
import os
import sys
import threading
import time
import unittest
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ui.server import LinForgeServer


class TestServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LinForgeServer(port=9095)
        cls.server.start(blocking=False)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def _get(self, path):
        url = f"{self.server.url}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def _post(self, path, body_dict):
        url = f"{self.server.url}{path}"
        data = json.dumps(body_dict).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def test_get_system(self):
        status, data = self._get("/api/system")
        self.assertEqual(status, 200)
        self.assertIn("summary", data)
        self.assertIn("metrics", data)

    def test_get_metrics(self):
        status, data = self._get("/api/metrics")
        self.assertEqual(status, 200)
        self.assertIn("cpu", data)
        self.assertIn("memory", data)

    def test_get_presets(self):
        status, data = self._get("/api/presets")
        self.assertEqual(status, 200)
        self.assertIn("presets", data)
        self.assertGreaterEqual(len(data["presets"]), 4)

    def test_get_apps(self):
        status, data = self._get("/api/apps")
        self.assertEqual(status, 200)
        self.assertIn("categories", data)
        self.assertIn("apps", data)

    def test_get_tweaks(self):
        status, data = self._get("/api/tweaks")
        self.assertEqual(status, 200)
        self.assertIn("categories", data)
        self.assertIn("tweaks", data)

    def test_get_drivers(self):
        status, data = self._get("/api/drivers")
        self.assertEqual(status, 200)
        self.assertIn("gpus", data)
        self.assertIn("audio", data)

    def test_get_troubleshoot(self):
        status, data = self._get("/api/troubleshoot")
        self.assertEqual(status, 200)
        self.assertIn("troubleshooters", data)

    def test_post_cancel(self):
        status, data = self._post("/api/cancel", {})
        self.assertEqual(status, 200)
        self.assertIn("cancelled", data)

    def test_serve_static_index(self):
        url = f"{self.server.url}/index.html"
        with urllib.request.urlopen(url, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("LinForge", content)


if __name__ == "__main__":
    unittest.main()
