"""
LinForge - Presets & Profile Orchestration Engine
Applies full-system 1-click profiles (Gaming, Developer, Debloat & Privacy, Creator Studio)
by coordinating apps, tweaks, drivers, and development stacks.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
    from modules.apps import AppManager
    from modules.drivers import DriverManager
    from modules.tweaks import TweaksManager
    from modules.cleanup import CleanupManager
    from modules.developer import DeveloperManager
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult
    from ..modules.apps import AppManager
    from ..modules.drivers import DriverManager
    from ..modules.tweaks import TweaksManager
    from ..modules.cleanup import CleanupManager
    from ..modules.developer import DeveloperManager


class PresetsManager:
    """Manages full system transformation presets."""

    def __init__(
        self,
        data_path: Optional[str] = None,
        detector: Optional[SystemDetector] = None,
        runner: Optional[CommandRunner] = None,
        apps_mgr: Optional[AppManager] = None,
        drivers_mgr: Optional[DriverManager] = None,
        tweaks_mgr: Optional[TweaksManager] = None,
        cleanup_mgr: Optional[CleanupManager] = None,
        dev_mgr: Optional[DeveloperManager] = None
    ):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.apps_mgr = apps_mgr or AppManager(detector=self.detector, runner=self.runner)
        self.drivers_mgr = drivers_mgr or DriverManager(detector=self.detector, runner=self.runner)
        self.tweaks_mgr = tweaks_mgr or TweaksManager(detector=self.detector, runner=self.runner)
        self.cleanup_mgr = cleanup_mgr or CleanupManager(detector=self.detector, runner=self.runner)
        self.dev_mgr = dev_mgr or DeveloperManager(detector=self.detector, runner=self.runner)

        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "presets.json")

        self.data_path = data_path
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"presets": []}

    def get_presets(self) -> List[Dict[str, Any]]:
        """Returns all preset profiles."""
        return self._data.get("presets", [])

    def apply_preset(self, preset_id: str, callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
        """Orchestrates applying a complete preset profile in coordinated order."""
        preset = next((p for p in self.get_presets() if p["id"] == preset_id), None)
        if not preset:
            if callback:
                callback("stderr", f"Preset '{preset_id}' not found.")
            return {"success": False, "error": f"Preset '{preset_id}' not found"}

        if callback:
            callback("system", f"🚀 Applying Preset Profile: {preset['name']}...")
            callback("system", f"ℹ️ {preset['description']}")

        results = {}

        # 1. Apply Tweaks
        tweaks = preset.get("tweaks", [])
        if tweaks:
            if callback:
                callback("system", f"⚡ Applying {len(tweaks)} system & kernel tweaks...")
            results["tweaks"] = self.tweaks_mgr.apply_batch(tweaks, callback=callback)

        # 2. Apply Driver Actions
        drivers = preset.get("driver_actions", [])
        for act in drivers:
            if self.runner._is_cancelled:
                break
            if act == "controllers":
                self.drivers_mgr.setup_game_controllers(callback=callback)
            elif act == "pipewire":
                self.drivers_mgr.setup_pipewire_audio(callback=callback)
            elif act == "nvidia":
                self.drivers_mgr.install_nvidia_recommended(callback=callback)
            elif act == "amd":
                self.drivers_mgr.install_amd_kisak_mesa(callback=callback)

        # 3. Apply Dev Stacks
        dev_stacks = preset.get("dev_stacks", [])
        for stack in dev_stacks:
            if self.runner._is_cancelled:
                break
            if stack == "web":
                self.dev_mgr.install_web_stack(callback=callback)
            elif stack == "python":
                self.dev_mgr.install_python_ai_stack(callback=callback)
            elif stack == "rust":
                self.dev_mgr.install_rust_systems_stack(callback=callback)
            elif stack == "cli":
                self.dev_mgr.install_modern_cli_tools(callback=callback)

        # 4. Install Preset Apps
        apps = preset.get("apps", [])
        if apps:
            if callback:
                callback("system", f"📦 Installing {len(apps)} curated applications...")
            results["apps"] = self.apps_mgr.install_batch(apps, callback=callback)

        # 5. Run Cleanup Actions
        cleanups = preset.get("cleanup_actions", [])
        if "all" in cleanups:
            self.cleanup_mgr.run_full_cleanup(callback=callback)

        if callback:
            callback("system", f"🎉 Preset Profile '{preset['name']}' has been fully applied!")

        return {"success": True, "preset_id": preset_id, "details": results}
