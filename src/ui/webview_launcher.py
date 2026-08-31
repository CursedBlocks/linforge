"""
LinForge - Desktop Window & Webview Launcher
Launches LinForge as a standalone native desktop window using pywebview or Chrome App Mode,
with seamless fallback to the user's default browser.
"""

import os
import shutil
import subprocess
import sys
import time
import webbrowser
from typing import Optional

try:
    from ui.server import LinForgeServer
except (ImportError, ValueError):
    from .server import LinForgeServer


def launch_gui(port: int = 8990, open_browser: bool = True):
    """Initializes backend server and opens the desktop GUI window."""
    server = LinForgeServer(port=port)
    server.start(blocking=False)
    target_url = server.url

    print(f"\n✨ LinForge Server initialized at {target_url}")

    if not open_browser:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            return

    # Method 1: Try pywebview if installed
    try:
        import webview
        print("🖥️ Launching via native desktop webview...")
        webview.create_window(
            title="LinForge - Ultimate Linux Setup & Maintenance Suite",
            url=target_url,
            width=1280,
            height=850,
            min_size=(960, 600),
            background_color="#0d1117"
        )
        webview.start()
        server.stop()
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"pywebview notice: {e}")

    # Method 2: Launch in Chrome/Chromium App Mode (Dedicated clean window)
    app_browsers = [
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
        "brave-browser",
        "microsoft-edge",
        "vivaldi"
    ]

    launched_app = False
    for b_cmd in app_browsers:
        if shutil.which(b_cmd):
            try:
                print(f"🚀 Opening dedicated app window with {b_cmd}...")
                proc = subprocess.Popen([
                    b_cmd,
                    f"--app={target_url}",
                    f"--user-data-dir=/tmp/linforge_profile_{os.getuid() if hasattr(os, 'getuid') else 1000}",
                    "--no-first-run",
                    "--no-default-browser-check"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                launched_app = True
                proc.wait()
                server.stop()
                return
            except Exception:
                pass

    # Method 3: Fallback to default browser
    if not launched_app:
        print(f"🌐 Opening LinForge in your default web browser: {target_url}")
        webbrowser.open(target_url)

        try:
            print("\nPress Ctrl+C in terminal to stop LinForge.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping LinForge...")
            server.stop()
