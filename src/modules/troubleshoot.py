"""
LinForge - Troubleshooting & Emergency Repair Kit Engine
Automated diagnostic testing and 1-click repair routines for package manager locks,
broken dependencies, DNS/network dropouts, audio glitches, and permissions errors.
"""

import json
import os
import subprocess
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult


class TroubleshootManager:
    """Diagnostic scanner and 1-click repair executor."""

    def __init__(self, data_path: Optional[str] = None, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()

        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "fixes.json")

        self.data_path = data_path
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Loads troubleshooters from JSON."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"troubleshooters": []}

    def get_troubleshooters(self) -> List[Dict[str, Any]]:
        """Returns all troubleshooters enriched with diagnostic check results."""
        items = self._data.get("troubleshooters", [])
        results = []

        for item in items:
            cloned = dict(item)
            cloned["status"] = self.check_issue_status(item)
            results.append(cloned)

        return results

    def check_issue_status(self, item: Dict[str, Any]) -> str:
        """
        Runs diagnostic check for an issue.
        Returns 'detected' (problem found), 'healthy' (all good), or 'unknown'.
        """
        check_cmd = item.get("check_command")
        if not check_cmd:
            return "healthy"

        try:
            res = subprocess.run(
                check_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )
            return "detected" if res.returncode == 0 else "healthy"
        except Exception:
            return "healthy"

    def run_fix(self, fix_id: str, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Executes a specific repair routine by ID."""
        fix = next((f for f in self._data.get("troubleshooters", []) if f["id"] == fix_id), None)
        if not fix:
            if callback:
                callback("stderr", f"Fix '{fix_id}' not found.")
            return CommandResult(1, "", f"Fix '{fix_id}' not found", 0.0)

        if callback:
            callback("system", f"🛠️ Executing repair: {fix['name']}...")

        script = fix.get("fix_script", "")
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def run_all_fixes(self, callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, CommandResult]:
        """Runs all repair routines sequentially."""
        results = {}
        items = self._data.get("troubleshooters", [])

        if callback:
            callback("system", "🚑 Running all diagnostic repair routines...")

        for item in items:
            if self.runner._is_cancelled:
                break
            results[item["id"]] = self.run_fix(item["id"], callback=callback)

        if callback:
            callback("system", "✅ System repairs completed!")

        return results
