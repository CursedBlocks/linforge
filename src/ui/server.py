"""
LinForge - Embedded Web & API Server
Lightweight zero-dependency HTTP server providing REST APIs, SSE real-time terminal log streaming,
task completion telemetry with structured error diagnostic codes, and static frontend asset serving.
"""

import json
import mimetypes
import os
import queue
import socketserver
import sys
import threading
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.system_info import SystemMonitor
    from core.runner import CommandRunner, CommandResult
    from modules.apps import AppManager
    from modules.drivers import DriverManager
    from modules.tweaks import TweaksManager
    from modules.cleanup import CleanupManager
    from modules.troubleshoot import TroubleshootManager
    from modules.developer import DeveloperManager
    from modules.maintenance import MaintenanceManager
    from modules.presets import PresetsManager
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.system_info import SystemMonitor
    from ..core.runner import CommandRunner, CommandResult
    from ..modules.apps import AppManager
    from ..modules.drivers import DriverManager
    from ..modules.tweaks import TweaksManager
    from ..modules.cleanup import CleanupManager
    from ..modules.troubleshoot import TroubleshootManager
    from ..modules.developer import DeveloperManager
    from ..modules.maintenance import MaintenanceManager
    from ..modules.presets import PresetsManager


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handles requests in separate threads for non-blocking execution."""
    daemon_threads = True
    allow_reuse_address = True


class LinForgeHandler(SimpleHTTPRequestHandler):
    """Custom request handler dispatching API endpoints and static assets."""
    server_instance: 'LinForgeServer' = None  # Injected on server initialization

    def log_message(self, format, *args):
        # Silence default request access logs in console
        pass

    def _send_json(self, data: Any, status: int = 200):
        try:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass

    def _read_json_body(self) -> Dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw = self.rfile.read(content_length).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/system":
            summary = self.server_instance.monitor.get_full_summary()
            self._send_json(summary)

        elif path == "/api/metrics":
            metrics = self.server_instance.monitor.get_live_metrics()
            self._send_json(metrics)

        elif path == "/api/presets":
            presets = self.server_instance.presets_mgr.get_presets()
            self._send_json({"presets": presets})

        elif path == "/api/apps":
            cat = query.get("category", ["all"])[0]
            search = query.get("search", [""])[0]
            refresh = query.get("refresh", ["false"])[0].lower() == "true"
            apps = self.server_instance.apps_mgr.get_apps(category=cat, search=search, refresh_installed=refresh)
            cats = self.server_instance.apps_mgr.get_categories()
            self._send_json({"categories": cats, "apps": apps})

        elif path == "/api/tweaks":
            tweaks = self.server_instance.tweaks_mgr.get_tweaks()
            cats = self.server_instance.tweaks_mgr.get_categories()
            self._send_json({"categories": cats, "tweaks": tweaks})

        elif path == "/api/drivers":
            status = self.server_instance.drivers_mgr.get_hardware_status()
            self._send_json(status)

        elif path == "/api/troubleshoot":
            fixes = self.server_instance.trouble_mgr.get_fixes()
            self._send_json({"fixes": fixes, "troubleshooters": fixes})

        elif path == "/api/logs/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            log_q = queue.Queue()
            self.server_instance.add_log_listener(log_q)

            try:
                self.wfile.write(b"data: {\"type\": \"connected\"}\n\n")
                self.wfile.flush()

                while not self.server_instance._stopping:
                    try:
                        msg = log_q.get(timeout=1.0)
                        payload = f"data: {json.dumps(msg)}\n\n".encode("utf-8")
                        self.wfile.write(payload)
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                pass
            finally:
                self.server_instance.remove_log_listener(log_q)

        else:
            self._serve_static(path)

    def _serve_static(self, req_path: str):
        if req_path == "/" or not req_path:
            req_path = "/index.html"

        rel_path = req_path.lstrip("/")
        full_path = os.path.join(self.server_instance.web_dir, rel_path)

        if not os.path.abspath(full_path).startswith(os.path.abspath(self.server_instance.web_dir)):
            self.send_error(403, "Forbidden")
            return

        if os.path.exists(full_path) and os.path.isfile(full_path):
            mime_type, _ = mimetypes.guess_type(full_path)
            if not mime_type:
                mime_type = "application/octet-stream"

            try:
                with open(full_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_error(500, "Error reading file")
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        if path == "/api/cancel":
            success = self.server_instance.runner.cancel_current()
            self._send_json({"cancelled": success})
            return

        # Guard mutating API endpoints against concurrent task collisions
        mutating_endpoints = [
            "/api/presets/apply", "/api/apps/install", "/api/apps/uninstall",
            "/api/tweaks/apply", "/api/tweaks/revert", "/api/drivers/action",
            "/api/cleanup/action", "/api/troubleshoot/run", "/api/developer/action",
            "/api/maintenance/action"
        ]
        if path in mutating_endpoints and self.server_instance.runner.is_running:
            self._send_json({
                "status": "error",
                "error_code": "ERR_TASK_ALREADY_RUNNING",
                "error_title": "Another Task is Currently Running",
                "error_suggestion": "Wait for the active task to finish, or click Cancel in the bottom terminal drawer."
            }, status=409)
            return

        if path == "/api/presets/apply":
            preset_id = body.get("preset_id")

            def run_job():
                if preset_id:
                    res = self.server_instance.presets_mgr.apply_preset(preset_id, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"Preset ({preset_id})", res)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/apps/install":
            app_id = body.get("app_id")
            source = body.get("source")
            force = body.get("force_reinstall", False)
            batch = body.get("batch", [])

            def run_job():
                if batch:
                    res_map = self.server_instance.apps_mgr.install_batch(batch, callback=self.server_instance.broadcast_log)
                    failed = [app for app, r in res_map.items() if not r.success]
                    overall_success = len(failed) == 0
                    summary_res = {
                        "success": overall_success,
                        "exit_code": 0 if overall_success else 1,
                        "error_code": "ERR_BATCH_PARTIAL_FAIL" if not overall_success else "SUCCESS",
                        "error_title": f"Batch Installation Completed ({len(batch) - len(failed)}/{len(batch)} successful)",
                        "error_suggestion": f"Failed apps: {', '.join(failed)}. Try installing them individually via Flatpak.",
                        "stdout": "",
                        "stderr": f"Failed on: {failed}" if failed else ""
                    }
                    self.server_instance.broadcast_task_result(f"Batch ({len(batch)} apps)", summary_res)
                elif app_id:
                    res = self.server_instance.apps_mgr.install_app(app_id, source_preference=source, force_reinstall=force, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"App Install: {app_id}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/apps/uninstall":
            app_id = body.get("app_id")

            def run_job():
                if app_id:
                    res = self.server_instance.apps_mgr.uninstall_app(app_id, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"App Uninstall: {app_id}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/tweaks/apply":
            tweak_id = body.get("tweak_id")
            batch = body.get("batch", [])

            def run_job():
                if batch:
                    res_map = self.server_instance.tweaks_mgr.apply_batch(batch, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result("Batch Tweaks", {"success": True, "exit_code": 0})
                elif tweak_id:
                    res = self.server_instance.tweaks_mgr.apply_tweak(tweak_id, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"Tweak: {tweak_id}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/tweaks/revert":
            tweak_id = body.get("tweak_id")

            def run_job():
                if tweak_id:
                    res = self.server_instance.tweaks_mgr.revert_tweak(tweak_id, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"Revert Tweak: {tweak_id}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/drivers/action":
            action = body.get("action")

            def run_job():
                res: Optional[CommandResult] = None
                if action == "nvidia":
                    res = self.server_instance.drivers_mgr.install_nvidia_recommended(callback=self.server_instance.broadcast_log)
                elif action == "amd":
                    res = self.server_instance.drivers_mgr.install_amd_kisak_mesa(callback=self.server_instance.broadcast_log)
                elif action == "broadcom":
                    res = self.server_instance.drivers_mgr.install_broadcom_wifi(callback=self.server_instance.broadcast_log)
                elif action == "realtek":
                    res = self.server_instance.drivers_mgr.install_realtek_wifi(callback=self.server_instance.broadcast_log)
                elif action == "pipewire":
                    res = self.server_instance.drivers_mgr.setup_pipewire_audio(callback=self.server_instance.broadcast_log)
                elif action == "controllers":
                    res = self.server_instance.drivers_mgr.setup_game_controllers(callback=self.server_instance.broadcast_log)
                elif action == "openrgb":
                    res = self.server_instance.drivers_mgr.setup_openrgb_udev(callback=self.server_instance.broadcast_log)
                elif action == "autocpufreq":
                    res = self.server_instance.drivers_mgr.install_autocpufreq_battery(callback=self.server_instance.broadcast_log)
                elif action == "xanmod":
                    res = self.server_instance.drivers_mgr.install_xanmod_kernel(callback=self.server_instance.broadcast_log)

                if res:
                    self.server_instance.broadcast_task_result(f"Driver Action: {action}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/cleanup/action":
            action = body.get("action", "all")

            def run_job():
                res: Optional[CommandResult] = None
                if action == "all":
                    res_map = self.server_instance.cleanup_mgr.run_full_cleanup(callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result("Full System Cleanup", {"success": True, "exit_code": 0})
                    return
                elif action in ["package_cache", "packages"]:
                    res = self.server_instance.cleanup_mgr.clean_package_cache(callback=self.server_instance.broadcast_log)
                elif action == "journal":
                    res = self.server_instance.cleanup_mgr.vacuum_systemd_journal(callback=self.server_instance.broadcast_log)
                elif action in ["old_kernels", "clean_kernels"]:
                    res = self.server_instance.maint_mgr.clean_old_kernels(callback=self.server_instance.broadcast_log)
                elif action in ["flatpak_unused", "flatpak"]:
                    res = self.server_instance.cleanup_mgr.clean_flatpak_unused(callback=self.server_instance.broadcast_log)
                elif action in ["snap_disabled", "snap_old_revisions", "snap"]:
                    res = self.server_instance.cleanup_mgr.purge_snap_old_revisions(callback=self.server_instance.broadcast_log)
                elif action in ["fstrim", "ssd_trim"]:
                    res = self.server_instance.cleanup_mgr.run_ssd_trim(callback=self.server_instance.broadcast_log)
                elif action in ["user_cache", "user_caches"]:
                    res = self.server_instance.cleanup_mgr.clean_user_caches(callback=self.server_instance.broadcast_log)

                if res:
                    self.server_instance.broadcast_task_result(f"Cleanup: {action}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/troubleshoot/run":
            fix_id = body.get("fix_id") or body.get("action")

            def run_job():
                if fix_id == "all":
                    res_map = self.server_instance.trouble_mgr.run_all_fixes(callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result("Full Diagnostics & Repairs", {"success": True, "exit_code": 0})
                elif fix_id:
                    res = self.server_instance.trouble_mgr.run_fix(fix_id, callback=self.server_instance.broadcast_log)
                    self.server_instance.broadcast_task_result(f"Troubleshoot: {fix_id}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/developer/action":
            action = body.get("action")

            def run_job():
                res: Optional[CommandResult] = None
                if action == "web":
                    res = self.server_instance.dev_mgr.install_web_stack(callback=self.server_instance.broadcast_log)
                elif action in ["python_ai", "python"]:
                    res = self.server_instance.dev_mgr.install_python_ai_stack(callback=self.server_instance.broadcast_log)
                elif action == "rust":
                    res = self.server_instance.dev_mgr.install_rust_systems_stack(callback=self.server_instance.broadcast_log)
                elif action in ["docker", "devops"]:
                    res = self.server_instance.dev_mgr.install_devops_stack(callback=self.server_instance.broadcast_log)
                elif action in ["modern_cli", "cli"]:
                    res = self.server_instance.dev_mgr.install_modern_cli_tools(callback=self.server_instance.broadcast_log)
                elif action == "zsh":
                    res = self.server_instance.dev_mgr.install_zsh_ohmyzsh(callback=self.server_instance.broadcast_log)

                if res:
                    self.server_instance.broadcast_task_result(f"Developer Stack: {action}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/maintenance/action":
            action = body.get("action")

            def run_job():
                res: Optional[CommandResult] = None
                if action in ["update_all", "full_update"]:
                    res = self.server_instance.maint_mgr.run_universal_update(callback=self.server_instance.broadcast_log)
                elif action in ["snapshot", "timeshift"]:
                    res = self.server_instance.maint_mgr.create_timeshift_snapshot(callback=self.server_instance.broadcast_log)
                elif action in ["clean_kernels", "old_kernels"]:
                    res = self.server_instance.maint_mgr.clean_old_kernels(callback=self.server_instance.broadcast_log)
                elif action in ["dotfiles", "backup_dotfiles"]:
                    res = self.server_instance.maint_mgr.backup_user_dotfiles(callback=self.server_instance.broadcast_log)

                if res:
                    self.server_instance.broadcast_task_result(f"Maintenance: {action}", res.to_dict())

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        else:
            self.send_error(404, "API Endpoint Not Found")


class LinForgeServer:
    """Embedded HTTP and SSE Web Server for the LinForge GUI."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8990, web_dir: Optional[str] = None):
        self.host = host
        self.port = port
        if not web_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            web_dir = os.path.join(base_dir, "web")
        self.web_dir = web_dir

        self.detector = SystemDetector()
        self.monitor = SystemMonitor(self.detector)
        self.runner = CommandRunner()

        self.apps_mgr = AppManager(detector=self.detector, runner=self.runner)
        self.drivers_mgr = DriverManager(detector=self.detector, runner=self.runner)
        self.tweaks_mgr = TweaksManager(detector=self.detector, runner=self.runner)
        self.cleanup_mgr = CleanupManager(detector=self.detector, runner=self.runner)
        self.trouble_mgr = TroubleshootManager(detector=self.detector, runner=self.runner)
        self.dev_mgr = DeveloperManager(detector=self.detector, runner=self.runner)
        self.maint_mgr = MaintenanceManager(detector=self.detector, runner=self.runner)
        self.presets_mgr = PresetsManager(detector=self.detector, runner=self.runner)

        self._listeners: List[queue.Queue] = []
        self._listeners_lock = threading.Lock()
        self._stopping = False

        LinForgeHandler.server_instance = self
        self.httpd: Optional[ThreadedHTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None

    def add_log_listener(self, q: queue.Queue):
        with self._listeners_lock:
            self._listeners.append(q)

    def remove_log_listener(self, q: queue.Queue):
        with self._listeners_lock:
            if q in self._listeners:
                self._listeners.remove(q)

    def broadcast_log(self, stream_type: str, message: str):
        entry = {
            "type": stream_type,
            "message": message,
            "timestamp": time.time()
        }
        with self._listeners_lock:
            for q in self._listeners:
                try:
                    q.put_nowait(entry)
                except Exception:
                    pass

    def broadcast_task_result(self, task_name: str, result_data: Any):
        """Broadcasts task completion event with detailed error/success payload."""
        payload = result_data if isinstance(result_data, dict) else (result_data.to_dict() if hasattr(result_data, "to_dict") else {"success": True})
        entry = {
            "type": "task_result",
            "task_name": task_name,
            "result": payload,
            "timestamp": time.time()
        }
        with self._listeners_lock:
            for q in self._listeners:
                try:
                    q.put_nowait(entry)
                except Exception:
                    pass

    def start(self, blocking: bool = False):
        for attempt_port in range(self.port, self.port + 50):
            try:
                self.httpd = ThreadedHTTPServer((self.host, attempt_port), LinForgeHandler)
                self.port = attempt_port
                break
            except OSError:
                continue

        if not self.httpd:
            raise RuntimeError("Unable to bind to an open local port.")

        if blocking:
            self.httpd.serve_forever()
        else:
            self._server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self._server_thread.start()

    def stop(self):
        self._stopping = True
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
