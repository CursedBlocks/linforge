"""
LinForge - System & Gaming Tweaks Engine
Manages applying and reverting performance, gaming, KDE Plasma, GNOME, and privacy tweaks.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult


class TweaksManager:
    """Manages system tweaks, kernel parameters, and desktop enhancements."""

    def __init__(self, data_path: Optional[str] = None, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()

        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "tweaks.json")

        self.data_path = data_path
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Loads tweaks data from JSON."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"categories": [], "tweaks": []}

    def get_categories(self) -> List[Dict[str, str]]:
        """Returns tweak categories."""
        return self._data.get("categories", [])

    def get_tweaks(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of tweaks enriched with active applied status."""
        tweaks = self._data.get("tweaks", [])
        results = []

        for tw in tweaks:
            if category and tw.get("category") != category:
                continue
            item = dict(tw)
            item["is_applied"] = self.is_tweak_applied(tw)
            results.append(item)

        return results

    def is_tweak_applied(self, tweak_meta: Dict[str, Any]) -> bool:
        """Checks whether a tweak is currently applied on the system."""
        tweak_id = tweak_meta.get("id", "")

        if tweak_id == "tweak_gaming_sysctl":
            return os.path.exists("/etc/sysctl.d/99-linforge-gaming.conf")
        elif tweak_id == "tweak_swappiness_10":
            return os.path.exists("/etc/sysctl.d/99-linforge-swappiness.conf")
        elif tweak_id == "tweak_split_lock":
            return os.path.exists("/etc/sysctl.d/99-linforge-splitlock.conf")
        elif tweak_id == "tweak_zram":
            return os.path.exists("/etc/default/zramswap")
        elif tweak_id == "tweak_bbr_tcp":
            return os.path.exists("/etc/sysctl.d/99-linforge-bbr.conf")
        elif tweak_id == "tweak_secure_dns":
            return os.path.exists("/etc/systemd/resolved.conf.d/linforge-dns.conf")
        elif tweak_id == "tweak_disable_apport_telemetry":
            if os.path.exists("/etc/default/apport"):
                with open("/etc/default/apport", "r") as f:
                    return "enabled=0" in f.read()

        return False

    def apply_tweak(self, tweak_id: str, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Applies a single tweak by ID."""
        tweak = next((t for t in self._data.get("tweaks", []) if t["id"] == tweak_id), None)
        if not tweak:
            if callback:
                callback("stderr", f"Tweak '{tweak_id}' not found.")
            return CommandResult(1, "", f"Tweak '{tweak_id}' not found", 0.0)

        if callback:
            callback("system", f"⚡ Applying tweak: {tweak['name']}...")

        script = tweak.get("apply_script", "")
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def revert_tweak(self, tweak_id: str, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Reverts a single tweak by ID."""
        tweak = next((t for t in self._data.get("tweaks", []) if t["id"] == tweak_id), None)
        if not tweak:
            if callback:
                callback("stderr", f"Tweak '{tweak_id}' not found.")
            return CommandResult(1, "", f"Tweak '{tweak_id}' not found", 0.0)

        if callback:
            callback("system", f"🔄 Reverting tweak: {tweak['name']}...")

        script = tweak.get("revert_script", "")
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def apply_batch(self, tweak_ids: List[str], callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, CommandResult]:
        """Applies multiple tweaks in sequence."""
        results = {}
        for tw_id in tweak_ids:
            if self.runner._is_cancelled:
                break
            results[tw_id] = self.apply_tweak(tw_id, callback=callback)
        return results
