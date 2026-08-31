"""
LinForge - Embedded Web & API Server
Lightweight zero-dependency HTTP server providing REST APIs, SSE real-time terminal log streaming,
and static frontend asset serving for the LinForge GUI.
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
    from core.runner import CommandRunner
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
    from ..core.runner import CommandRunner
    from ..modules.apps import AppManager
    from ..modules.drivers import DriverManager
    from ..modules.tweaks import TweaksManager
    from ..modules.cleanup import CleanupManager
    from ..modules.troubleshoot import TroubleshootManager
    from ..modules.developer import DeveloperManager
    from ..modules.maintenance import MaintenanceManager
    from ..modules.presets import PresetsManager


class LinForgeHandler(SimpleHTTPRequestHandler):
    """Custom HTTP Request Handler serving REST APIs, SSE logs, and static files."""

    server_instance = None

    def log_message(self, format, *args):
        pass

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len > 0:
                raw = self.rfile.read(content_len).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/system":
            summary = self.server_instance.detector.get_full_summary()
            metrics = self.server_instance.monitor.get_all_metrics()
            self._send_json({"summary": summary, "metrics": metrics})

        elif path == "/api/metrics":
            metrics = self.server_instance.monitor.get_all_metrics()
            self._send_json(metrics)

        elif path == "/api/presets":
            presets = self.server_instance.presets_mgr.get_presets()
            self._send_json({"presets": presets})

        elif path == "/api/apps":
            cat = query.get("category", [None])[0]
            search = query.get("search", [None])[0]
            categories = self.server_instance.apps_mgr.get_categories()
            apps = self.server_instance.apps_mgr.get_apps(category=cat, search=search)
            self._send_json({"categories": categories, "apps": apps})

        elif path == "/api/tweaks":
            cat = query.get("category", [None])[0]
            categories = self.server_instance.tweaks_mgr.get_categories()
            tweaks = self.server_instance.tweaks_mgr.get_tweaks(category=cat)
            self._send_json({"categories": categories, "tweaks": tweaks})

        elif path == "/api/drivers":
            status = self.server_instance.drivers_mgr.get_hardware_status()
            self._send_json(status)

        elif path == "/api/troubleshoot":
            items = self.server_instance.troubleshoot_mgr.get_troubleshooters()
            self._send_json({"troubleshooters": items})

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
            except (BrokenPipeError, ConnectionResetError):
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

        elif path == "/api/presets/apply":
            preset_id = body.get("preset_id")

            def run_job():
                if preset_id:
                    self.server_instance.presets_mgr.apply_preset(preset_id, callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/apps/install":
            app_id = body.get("app_id")
            source = body.get("source")
            batch = body.get("batch", [])

            def run_job():
                if batch:
                    self.server_instance.apps_mgr.install_batch(batch, callback=self.server_instance.broadcast_log)
                elif app_id:
                    self.server_instance.apps_mgr.install_app(app_id, source_preference=source, callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/tweaks/apply":
            tweak_id = body.get("tweak_id")
            batch = body.get("batch", [])

            def run_job():
                if batch:
                    self.server_instance.tweaks_mgr.apply_batch(batch, callback=self.server_instance.broadcast_log)
                elif tweak_id:
                    self.server_instance.tweaks_mgr.apply_tweak(tweak_id, callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/tweaks/revert":
            tweak_id = body.get("tweak_id")

            def run_job():
                if tweak_id:
                    self.server_instance.tweaks_mgr.revert_tweak(tweak_id, callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/drivers/action":
            action = body.get("action")

            def run_job():
                if action == "nvidia":
                    self.server_instance.drivers_mgr.install_nvidia_recommended(callback=self.server_instance.broadcast_log)
                elif action == "amd":
                    self.server_instance.drivers_mgr.install_amd_kisak_mesa(callback=self.server_instance.broadcast_log)
                elif action == "broadcom":
                    self.server_instance.drivers_mgr.install_broadcom_wifi(callback=self.server_instance.broadcast_log)
                elif action == "realtek":
                    self.server_instance.drivers_mgr.install_realtek_wifi(callback=self.server_instance.broadcast_log)
                elif action == "pipewire":
                    self.server_instance.drivers_mgr.setup_pipewire_audio(callback=self.server_instance.broadcast_log)
                elif action == "controllers":
                    self.server_instance.drivers_mgr.setup_game_controllers(callback=self.server_instance.broadcast_log)
                elif action == "openrgb":
                    self.server_instance.drivers_mgr.setup_openrgb_udev(callback=self.server_instance.broadcast_log)
                elif action == "autocpufreq":
                    self.server_instance.drivers_mgr.install_autocpufreq_battery(callback=self.server_instance.broadcast_log)
                elif action == "xanmod":
                    self.server_instance.drivers_mgr.install_xanmod_kernel(callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/cleanup/action":
            action = body.get("action")

            def run_job():
                if action == "all":
                    self.server_instance.cleanup_mgr.run_full_cleanup(callback=self.server_instance.broadcast_log)
                elif action == "packages":
                    self.server_instance.cleanup_mgr.clean_package_cache(callback=self.server_instance.broadcast_log)
                elif action == "journal":
                    self.server_instance.cleanup_mgr.vacuum_systemd_journal(callback=self.server_instance.broadcast_log)
                elif action == "flatpak":
                    self.server_instance.cleanup_mgr.clean_flatpak_unused(callback=self.server_instance.broadcast_log)
                elif action == "snap":
                    self.server_instance.cleanup_mgr.purge_snap_old_revisions(callback=self.server_instance.broadcast_log)
                elif action == "user_cache":
                    self.server_instance.cleanup_mgr.clean_user_caches(callback=self.server_instance.broadcast_log)
                elif action == "ssd_trim":
                    self.server_instance.cleanup_mgr.run_ssd_trim(callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/troubleshoot/run":
            fix_id = body.get("fix_id")
            action = body.get("action")

            def run_job():
                if action == "all":
                    self.server_instance.troubleshoot_mgr.run_all_fixes(callback=self.server_instance.broadcast_log)
                elif fix_id:
                    self.server_instance.troubleshoot_mgr.run_fix(fix_id, callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/developer/action":
            action = body.get("action")

            def run_job():
                if action == "web":
                    self.server_instance.dev_mgr.install_web_stack(callback=self.server_instance.broadcast_log)
                elif action == "python":
                    self.server_instance.dev_mgr.install_python_ai_stack(callback=self.server_instance.broadcast_log)
                elif action == "rust":
                    self.server_instance.dev_mgr.install_rust_systems_stack(callback=self.server_instance.broadcast_log)
                elif action == "devops":
                    self.server_instance.dev_mgr.install_devops_stack(callback=self.server_instance.broadcast_log)
                elif action == "cli":
                    self.server_instance.dev_mgr.install_modern_cli_tools(callback=self.server_instance.broadcast_log)
                elif action == "zsh":
                    self.server_instance.dev_mgr.install_zsh_ohmyzsh(callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        elif path == "/api/maintenance/action":
            action = body.get("action")

            def run_job():
                if action == "update_all":
                    self.server_instance.maint_mgr.run_universal_update(callback=self.server_instance.broadcast_log)
                elif action == "snapshot":
                    self.server_instance.maint_mgr.create_timeshift_snapshot(callback=self.server_instance.broadcast_log)
                elif action == "dotfiles":
                    self.server_instance.maint_mgr.backup_user_dotfiles(callback=self.server_instance.broadcast_log)
                elif action == "clean_kernels":
                    self.server_instance.maint_mgr.clean_old_kernels(callback=self.server_instance.broadcast_log)

            threading.Thread(target=run_job, daemon=True).start()
            self._send_json({"status": "started"})

        else:
            self.send_error(404, "Endpoint Not Found")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


class LinForgeServer:
    """Embedded LinForge Web Server manager."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8990):
        self.host = host
        self.port = port
        self._stopping = False
        self._listeners: List[queue.Queue] = []
        self._listeners_lock = threading.Lock()

        self.detector = SystemDetector()
        self.monitor = SystemMonitor()
        self.runner = CommandRunner()

        self.apps_mgr = AppManager(detector=self.detector, runner=self.runner)
        self.drivers_mgr = DriverManager(detector=self.detector, runner=self.runner)
        self.tweaks_mgr = TweaksManager(detector=self.detector, runner=self.runner)
        self.cleanup_mgr = CleanupManager(detector=self.detector, runner=self.runner)
        self.troubleshoot_mgr = TroubleshootManager(detector=self.detector, runner=self.runner)
        self.dev_mgr = DeveloperManager(detector=self.detector, runner=self.runner)
        self.maint_mgr = MaintenanceManager(detector=self.detector, runner=self.runner)
        self.presets_mgr = PresetsManager(
            detector=self.detector,
            runner=self.runner,
            apps_mgr=self.apps_mgr,
            drivers_mgr=self.drivers_mgr,
            tweaks_mgr=self.tweaks_mgr,
            cleanup_mgr=self.cleanup_mgr,
            dev_mgr=self.dev_mgr
        )

        self.web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

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
