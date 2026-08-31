"""
LinForge Test Suite - Data Integrity & Schema Validation
Verifies apps.json, tweaks.json, and fixes.json structure, IDs, and categories.
"""

import json
import os
import unittest


class TestDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "src", "data")

    def test_apps_json_schema(self):
        path = os.path.join(self.data_dir, "apps.json")
        self.assertTrue(os.path.exists(path), "apps.json must exist")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("categories", data)
        self.assertIn("apps", data)
        self.assertGreater(len(data["categories"]), 0)
        self.assertGreater(len(data["apps"]), 0)

        category_ids = {c["id"] for c in data["categories"]}
        app_ids = set()

        for app in data["apps"]:
            self.assertIn("id", app)
            self.assertIn("name", app)
            self.assertIn("category", app)
            self.assertIn("description", app)
            self.assertIn("sources", app)
            self.assertIn(app["category"], category_ids, f"Category '{app['category']}' must exist in categories")
            self.assertNotIn(app["id"], app_ids, f"Duplicate app ID '{app['id']}' found")
            app_ids.add(app["id"])

    def test_tweaks_json_schema(self):
        path = os.path.join(self.data_dir, "tweaks.json")
        self.assertTrue(os.path.exists(path), "tweaks.json must exist")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("categories", data)
        self.assertIn("tweaks", data)

        cat_ids = {c["id"] for c in data["categories"]}
        tweak_ids = set()

        for tw in data["tweaks"]:
            self.assertIn("id", tw)
            self.assertIn("name", tw)
            self.assertIn("category", tw)
            self.assertIn("description", tw)
            self.assertIn("apply_script", tw)
            self.assertIn(tw["category"], cat_ids, f"Category '{tw['category']}' must exist in categories")
            self.assertNotIn(tw["id"], tweak_ids, f"Duplicate tweak ID '{tw['id']}' found")
            tweak_ids.add(tw["id"])

    def test_fixes_json_schema(self):
        path = os.path.join(self.data_dir, "fixes.json")
        self.assertTrue(os.path.exists(path), "fixes.json must exist")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("troubleshooters", data)
        fix_ids = set()

        for fix in data["troubleshooters"]:
            self.assertIn("id", fix)
            self.assertIn("name", fix)
            self.assertIn("description", fix)
            self.assertIn("fix_script", fix)
            self.assertNotIn(fix["id"], fix_ids, f"Duplicate fix ID '{fix['id']}' found")
            fix_ids.add(fix["id"])


if __name__ == "__main__":
    unittest.main()
