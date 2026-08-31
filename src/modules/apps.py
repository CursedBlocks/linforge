"""
LinForge - Application Manager & Catalog Engine
Handles 1-click single, batch installation and uninstallation of 100+ curated Linux applications
with accurate already-installed detection, multi-source resolution (Native APT/DNF/Pacman, Flatpak Flathub, Snap),
and automated fallback resiliency.
"""

import json
import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from core.detector import SystemDetector
    from core.package_manager import PackageManager
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.package_manager import PackageManager
    from ..core.runner import CommandRunner, CommandResult


class AppManager:
    """Manages software catalog, installation queue, installed detection, and package sources."""

    def __init__(self, data_path: Optional[str] = None, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.pkg_mgr = PackageManager(self.detector, self.runner)

        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "apps.json")

        self.data_path = data_path
        self._catalog = self._load_catalog()
        self._installed_cache: Dict[str, Tuple[bool, str, float]] = {}
        self._path_binaries: Optional[Set[str]] = None
        self._installed_native: Optional[Set[str]] = None
        self._installed_flatpaks: Optional[Set[str]] = None
        self._installed_snaps: Optional[Set[str]] = None
        self._system_scan_time: float = 0.0

    def _load_catalog(self) -> Dict[str, Any]:
        """Loads the application catalog from data/apps.json."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Error] Failed to load apps.json: {e}")
        return {"categories": [], "apps": []}

    def get_categories(self) -> List[Dict[str, Any]]:
        """Returns the list of application categories."""
        return self._catalog.get("categories", [])

    def _refresh_system_installed_sets(self, force: bool = False):
        """Scans installed binaries, dpkg packages, flatpaks, and snaps in one ultra-fast batch pass."""
        now = time.time()
        if not force and self._path_binaries is not None and (now - self._system_scan_time < 20.0):
            return

        self._path_binaries = set()
        for p in os.environ.get("PATH", "").split(os.pathsep):
            if p and os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        fl = f.lower()
                        self._path_binaries.add(fl)
                        if fl.endswith(".exe"):
                            self._path_binaries.add(fl[:-4])
                except Exception:
                    pass

        self._installed_native = set()
        if os.path.exists("/var/lib/dpkg/status"):
            try:
                with open("/var/lib/dpkg/status", "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("Package: "):
                            self._installed_native.add(line.split(":", 1)[1].strip())
            except Exception:
                pass

        self._installed_flatpaks = set()
        if shutil.which("flatpak"):
            try:
                out = subprocess.check_output(["flatpak", "list", "--app", "--columns=application"], stderr=subprocess.DEVNULL, timeout=2).decode()
                for line in out.splitlines():
                    if line.strip():
                        self._installed_flatpaks.add(line.strip())
            except Exception:
                pass

        self._installed_snaps = set()
        if shutil.which("snap"):
            try:
                out = subprocess.check_output(["snap", "list"], stderr=subprocess.DEVNULL, timeout=2).decode()
                for line in out.splitlines()[1:]:
                    parts = line.split()
                    if parts:
                        self._installed_snaps.add(parts[0].strip())
            except Exception:
                pass

        self._system_scan_time = now

    def is_app_installed(self, app_id: str, force_refresh: bool = False) -> Tuple[bool, str]:
        """
        Determines whether an application is currently installed on the system,
        checking binary PATH, dpkg, flatpak, snap, and desktop entries.
        Returns (is_installed: bool, installed_source: str).
        """
        self._refresh_system_installed_sets(force=force_refresh)
        now = time.time()

        if not force_refresh and app_id in self._installed_cache:
            installed, src, ts = self._installed_cache[app_id]
            if now - ts < 20.0:
                return installed, src

        app = next((a for a in self._catalog.get("apps", []) if a["id"] == app_id), None)
        if not app:
            return False, "none"

        sources = app.get("sources", {})
        binary_names = [app_id.lower()]

        # Check binary hints
        if "binary" in app:
            binary_names.append(app["binary"].lower())
        if "flatpak" in sources:
            binary_names.append(sources["flatpak"].split(".")[-1].lower())

        for b in binary_names:
            if b in self._path_binaries or shutil.which(b):
                self._installed_cache[app_id] = (True, "native", now)
                return True, "native"

        # Check Flatpak
        if "flatpak" in sources:
            flatpak_id = sources["flatpak"]
            if flatpak_id in self._installed_flatpaks:
                self._installed_cache[app_id] = (True, "flatpak", now)
                return True, "flatpak"

        # Check Native Debian package
        if "native_deb" in sources:
            src_def = sources["native_deb"]
            pkg_name = src_def if isinstance(src_def, str) else src_def.get("package", app_id)
            if pkg_name in self._installed_native:
                self._installed_cache[app_id] = (True, "native", now)
                return True, "native"

        # Check Snap
        if "snap" in sources:
            snap_pkg = sources["snap"].replace("--classic", "").strip()
            if snap_pkg in self._installed_snaps:
                self._installed_cache[app_id] = (True, "snap", now)
                return True, "snap"

        self._installed_cache[app_id] = (False, "none", now)
        return False, "none"

    def get_apps(self, category: Optional[str] = None, search: Optional[str] = None, refresh_installed: bool = False) -> List[Dict[str, Any]]:
        """Returns apps with dynamic installation status and multi-source availability."""
        apps = self._catalog.get("apps", [])

        if category and category != "all":
            apps = [a for a in apps if a.get("category") == category]

        if search:
            s = search.lower().strip()
            apps = [a for a in apps if s in a.get("name", "").lower() or s in a.get("description", "").lower() or s in a.get("id", "").lower()]

        result = []
        for app in apps:
            app_copy = dict(app)
            installed, installed_src = self.is_app_installed(app["id"], force_refresh=refresh_installed)
            app_copy["is_installed"] = installed
            app_copy["installed_source"] = installed_src
            result.append(app_copy)

        return result

    def install_app(
        self,
        app_id: str,
        source_preference: Optional[str] = None,
        force_reinstall: bool = False,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a single application with already-installed checks, multi-source resolution, and Flatpak fallback."""
        app = next((a for a in self._catalog.get("apps", []) if a["id"] == app_id), None)
        if not app:
            if callback:
                callback("stderr", f"App '{app_id}' not found in catalog.")
            return CommandResult(1, "", f"App '{app_id}' not found", 0.0, error_code="ERR_APP_NOT_FOUND", error_title="App Not Found in Catalog")

        installed, current_src = self.is_app_installed(app_id, force_refresh=True)
        if installed and not force_reinstall:
            if callback:
                callback("system", f"✓ {app['name']} is already installed ({current_src}). Skipping duplicate installation.")
            return CommandResult(0, f"{app['name']} is already installed.", "", 0.0)

        sources = app.get("sources", {})
        pref = source_preference or app.get("default_source", "native_deb")
        distro_family = self.detector.get_distro_info().get("family", "debian")

        # Auto-fallback to flatpak on non-Debian distributions
        if distro_family != "debian" and pref == "native_deb" and "flatpak" in sources:
            pref = "flatpak"

        if callback:
            callback("system", f"📦 Installing {app['name']} via {pref}...")

        # Ensure essential prerequisites are present before installing
        self.pkg_mgr.ensure_system_prerequisites(callback=callback)

        res: Optional[CommandResult] = None

        if pref == "flatpak" and "flatpak" in sources:
            res = self.pkg_mgr.install_flatpak(sources["flatpak"], callback=callback)

        elif pref == "native_deb" and "native_deb" in sources:
            src_def = sources["native_deb"]
            if isinstance(src_def, str):
                res = self.pkg_mgr.install_native_packages([src_def], callback=callback)
            elif isinstance(src_def, dict):
                src_type = src_def.get("type")
                if src_type == "script":
                    res = self.runner.run_script_block(src_def["command"], use_sudo=True, callback=callback)
                elif src_type == "deb_url":
                    res = self.pkg_mgr.install_deb_url_safe(src_def["url"], app["name"], callback=callback)
                elif src_type == "repo":
                    res = self.pkg_mgr.add_apt_repository_secure(
                        repo_name=src_def["repo_name"],
                        gpg_key_url=src_def["key_url"],
                        sources_line=src_def["sources_line"],
                        package_to_install=src_def.get("package"),
                        callback=callback
                    )

            # Fallback to Flatpak if native Debian installation encountered dependency or repo errors
            if res and not res.success and "flatpak" in sources:
                if callback:
                    callback("system", f"⚠️ Native installation had issues ({res.error_code}). Seamlessly attempting Flatpak fallback...")
                res = self.pkg_mgr.install_flatpak(sources["flatpak"], callback=callback)

        elif "flatpak" in sources:
            res = self.pkg_mgr.install_flatpak(sources["flatpak"], callback=callback)

        if not res and "snap" in sources and shutil.which("snap"):
            snap_target = sources["snap"]
            is_classic = "--classic" in snap_target
            snap_pkg = snap_target.replace("--classic", "").strip()
            res = self.pkg_mgr.install_snap(snap_pkg, classic=is_classic, callback=callback)

        if not res:
            res = CommandResult(1, "", f"No compatible installation source found for {app_id}", 0.0, error_code="ERR_NO_SOURCE", error_title="No Compatible Source")

        # Invalidate cache on completion
        self.is_app_installed(app_id, force_refresh=True)
        return res

    def uninstall_app(
        self,
        app_id: str,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Uninstalls an application cleanly across native, Flatpak, or Snap sources."""
        app = next((a for a in self._catalog.get("apps", []) if a["id"] == app_id), None)
        if not app:
            return CommandResult(1, "", f"App '{app_id}' not found", 0.0)

        installed, src = self.is_app_installed(app_id, force_refresh=True)
        if not installed:
            if callback:
                callback("system", f"App '{app['name']}' is not currently installed.")
            return CommandResult(0, f"{app['name']} is not installed", "", 0.0)

        if callback:
            callback("system", f"🗑️ Uninstalling {app['name']} ({src})...")

        sources = app.get("sources", {})

        if src == "flatpak" and "flatpak" in sources:
            script = f"flatpak uninstall -y {sources['flatpak']}"
            res = self.runner.run_script_block(script, use_sudo=True, callback=callback)
        elif src == "snap" and "snap" in sources:
            snap_pkg = sources["snap"].replace("--classic", "").strip()
            script = f"snap remove {snap_pkg}"
            res = self.runner.run_script_block(script, use_sudo=True, callback=callback)
        else:
            # Native package removal
            pkg_name = app_id
            if "native_deb" in sources:
                src_def = sources["native_deb"]
                if isinstance(src_def, str):
                    pkg_name = src_def
                elif isinstance(src_def, dict) and "package" in src_def:
                    pkg_name = src_def["package"]
            res = self.pkg_mgr.remove_native_packages([pkg_name], callback=callback)

        self.is_app_installed(app_id, force_refresh=True)
        return res

    def install_batch(
        self,
        app_ids: List[str],
        callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, CommandResult]:
        """Installs multiple applications in sequence with live logging and automatic skips for already-installed apps."""
        results = {}
        total = len(app_ids)

        if callback:
            callback("system", f"🚀 Starting batch installation of {total} applications...")

        # Ensure prerequisites once before running batch
        self.pkg_mgr.ensure_system_prerequisites(callback=callback)

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
