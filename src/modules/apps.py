"""
LinForge - Application Manager & Catalog Engine
Handles 1-click single and batch installation of 100+ curated Linux applications
with multi-source resolution (Native APT/DNF/Pacman, Flatpak Flathub, Snap, Official Repos).
"""

import json
import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from core.detector import SystemDetector
    from core.package_manager import PackageManager
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.package_manager import PackageManager
    from ..core.runner import CommandRunner, CommandResult


class AppManager:
    """Manages software catalog, installation queue, and package sources."""

    def __init__(self, data_path: Optional[str] = None, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.pkg_mgr = PackageManager(self.detector, self.runner)

        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "apps.json")

        self.data_path = data_path
        self._catalog = self._load_catalog()
        self._path_binaries_cache: Optional[Set[str]] = None
        self._cache_timestamp = 0.0

    def _load_catalog(self) -> Dict[str, Any]:
        """Loads application catalog from JSON file."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"categories": [], "apps": []}

    def _get_path_binaries(self) -> Set[str]:
        """Cached fast lookup set of all executable names available on system PATH."""
        now = time.time()
        if self._path_binaries_cache is not None and (now - self._cache_timestamp) < 5.0:
            return self._path_binaries_cache

        bin_set = set()
        path_env = os.environ.get("PATH", "")
        for path_dir in path_env.split(os.pathsep):
            if path_dir and os.path.isdir(path_dir):
                try:
                    for fname in os.listdir(path_dir):
                        bin_set.add(fname.lower())
                        if fname.endswith(".exe"):
                            bin_set.add(fname[:-4].lower())
                except Exception:
                    pass

        self._path_binaries_cache = bin_set
        self._cache_timestamp = now
        return bin_set

    def get_categories(self) -> List[Dict[str, str]]:
        """Returns all application categories."""
        return self._catalog.get("categories", [])

    def get_apps(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns filtered applications enriched with real-time installation status."""
        apps = self._catalog.get("apps", [])
        results = []
        path_bins = self._get_path_binaries()

        for app in apps:
            if category and app.get("category") != category:
                continue
            if search:
                term = search.lower()
                name = app.get("name", "").lower()
                desc = app.get("description", "").lower()
                app_id = app.get("id", "").lower()
                if term not in name and term not in desc and term not in app_id:
                    continue

            app_data = dict(app)
            app_data["is_installed"] = self.is_app_installed(app, path_bins=path_bins)
            results.append(app_data)

        return results

    def is_app_installed(self, app_meta: Dict[str, Any], path_bins: Optional[Set[str]] = None) -> bool:
        """Determines if the application is currently installed using fast binary scan."""
        app_id = app_meta.get("id", "")
        binary_map = {
            "google-chrome": "google-chrome-stable",
            "brave-browser": "brave-browser",
            "firefox-native": "firefox",
            "vscode": "code",
            "vscodium": "codium",
            "docker-engine": "docker",
            "obs-studio": "obs",
            "libreoffice-fresh": "libreoffice",
            "timeshift": "timeshift",
            "fastfetch": "fastfetch",
            "btop": "btop",
            "gparted": "gparted",
            "discord": "discord",
            "spotify": "spotify",
            "telegram-desktop": "telegram-desktop"
        }
        bin_name = binary_map.get(app_id, app_id).lower()
        bins = path_bins if path_bins is not None else self._get_path_binaries()

        if bin_name in bins:
            return True

        sources = app_meta.get("sources", {})
        if "flatpak" in sources and "flatpak" in bins:
            flatpak_id = sources["flatpak"]
            if self.pkg_mgr.is_package_installed(flatpak_id, manager_type="flatpak"):
                return True

        if "native_deb" in sources:
            src = sources["native_deb"]
            if isinstance(src, str):
                if self.pkg_mgr.is_package_installed(src, manager_type="apt"):
                    return True
            elif isinstance(src, dict) and "package" in src:
                if self.pkg_mgr.is_package_installed(src["package"], manager_type="apt"):
                    return True

        return False

    def install_app(
        self,
        app_id: str,
        source_preference: Optional[str] = None,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a single application by ID using the specified or default source."""
        app = next((a for a in self._catalog.get("apps", []) if a["id"] == app_id), None)
        if not app:
            if callback:
                callback("stderr", f"App '{app_id}' not found in catalog.")
            return CommandResult(1, "", f"App '{app_id}' not found", 0.0)

        sources = app.get("sources", {})
        pref = source_preference or app.get("default_source", "native_deb")
        distro_family = self.detector.get_distro_info().get("family", "debian")

        # If on non-Debian (Fedora, Arch, openSUSE) and preference is native_deb, fallback to flatpak if available
        if distro_family != "debian" and pref == "native_deb" and "flatpak" in sources:
            pref = "flatpak"

        if callback:
            callback("system", f"📦 Installing {app['name']} via {pref}...")

        if pref == "flatpak" and "flatpak" in sources:
            return self.pkg_mgr.install_flatpak(sources["flatpak"], callback=callback)

        if pref == "native_deb" and "native_deb" in sources:
            src_def = sources["native_deb"]
            if isinstance(src_def, str):
                return self.pkg_mgr.install_native_packages([src_def], callback=callback)
            elif isinstance(src_def, dict):
                src_type = src_def.get("type")
                if src_type == "script":
                    return self.runner.run_script_block(src_def["command"], use_sudo=True, callback=callback)
                elif src_type == "repo":
                    return self.pkg_mgr.add_apt_repository_secure(
                        repo_name=src_def["repo_name"],
                        gpg_key_url=src_def["key_url"],
                        sources_line=src_def["sources_line"],
                        callback=callback
                    )
        elif "flatpak" in sources:
            return self.pkg_mgr.install_flatpak(sources["flatpak"], callback=callback)

        if "snap" in sources and shutil.which("snap"):
            snap_target = sources["snap"]
            is_classic = "--classic" in snap_target
            snap_pkg = snap_target.replace("--classic", "").strip()
            return self.pkg_mgr.install_snap(snap_pkg, classic=is_classic, callback=callback)

        return CommandResult(1, "", f"No compatible installation source found for {app_id}", 0.0)

    def install_batch(
        self,
        app_ids: List[str],
        callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, CommandResult]:
        """Installs multiple applications in sequence with live logging."""
        results = {}
        total = len(app_ids)

        if callback:
            callback("system", f"🚀 Starting batch installation of {total} applications...")

        for idx, app_id in enumerate(app_ids, 1):
            if self.runner._is_cancelled:
                if callback:
                    callback("system", "⏹️ Batch installation aborted by user.")
                break

            if callback:
                callback("system", f"[{idx}/{total}] Processing {app_id}...")

            res = self.install_app(app_id, callback=callback)
            results[app_id] = res

        if callback:
            success_count = sum(1 for r in results.values() if r.success)
            callback("system", f"🏁 Batch installation finished: {success_count}/{len(results)} successful.")

        return results
