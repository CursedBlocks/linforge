#!/usr/bin/env python3
"""
LinForge - Master CLI & GUI Dispatcher
The Ultimate Linux Setup, Optimization, Hardware Troubleshooting, and System Maintenance Suite.
"""

import argparse
import os
import sys

# Ensure UTF-8 stdout/stderr encoding in all environments
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure local package path is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

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
from ui.webview_launcher import launch_gui
from ui.tui import run_tui


def print_cli_callback(stream_type: str, msg: str):
    if stream_type == "system":
        print(f"[LinForge] {msg}")
    elif stream_type == "stderr":
        print(f"[Error] {msg}", file=sys.stderr)
    else:
        print(f"  {msg}")


def main():
    parser = argparse.ArgumentParser(
        description="LinForge: The Ultimate Linux Setup & Maintenance Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  linforge                  Launch the sleek desktop GUI (or fallback to TUI)
  linforge --tui            Launch the interactive Terminal UI menu
  linforge --preset gaming  Apply the Ultimate Gaming Rig preset
  linforge --update-all     Update Native packages, Flatpaks, Snaps and Firmware
  linforge --clean          Run full deep system cleanup
  linforge --gaming         Apply recommended gaming kernel & memory map tweaks
  linforge --fix-audio      Reset and configure low-latency PipeWire audio stack
  linforge --fix-packages   Repair broken package database and stale APT locks
  linforge --info           Display live system telemetry and hardware summary
        """
    )

    parser.add_argument("--gui", action="store_true", help="Force launch Desktop GUI")
    parser.add_argument("--tui", action="store_true", help="Launch interactive Terminal User Interface (TUI)")
    parser.add_argument("--headless", action="store_true", help="Start backend server without opening a browser window")
    parser.add_argument("--port", type=int, default=8990, help="Custom port for embedded server (default: 8990)")

    # 1-Click Operations
    parser.add_argument("--preset", type=str, choices=["gaming", "developer", "debloat", "creator"], help="Apply a full system preset transformation profile")
    parser.add_argument("--update-all", action="store_true", help="Run Universal 1-Click System Update")
    parser.add_argument("--clean", action="store_true", help="Run Full Deep System Cleanup")
    parser.add_argument("--gaming", action="store_true", help="Apply recommended Gaming & Low Latency tweaks")
    parser.add_argument("--fix-audio", action="store_true", help="Reset & configure PipeWire low-latency audio stack")
    parser.add_argument("--fix-packages", action="store_true", help="Unlock APT and repair broken package dependencies")
    parser.add_argument("--info", action="store_true", help="Print live system telemetry and hardware summary")

    args = parser.parse_args()

    detector = SystemDetector()
    runner = CommandRunner()

    if args.info:
        monitor = SystemMonitor()
        summary = detector.get_full_summary()
        metrics = monitor.get_all_metrics()
        print("\n" + "="*50)
        print("⚡ LinForge Live System Telemetry")
        print("="*50)
        print(f"OS:          {summary['distro']['pretty_name']} ({summary['distro'].get('architecture', 'x86_64')})")
        print(f"Kernel:      {summary['distro']['kernel']}")
        print(f"Desktop:     {summary['desktop']['name']} {summary['desktop']['version']} ({summary['desktop']['session_type'].upper()})")
        print(f"CPU:         {metrics['cpu']['model']} ({metrics['cpu']['cores']} cores @ {metrics['cpu']['frequency_mhz']} MHz)")
        print(f"CPU Load:    {metrics['cpu']['usage_percent']}% (Temp: {metrics['cpu']['temperature_c'] or 'N/A'}°C)")
        print(f"Memory:      {metrics['memory']['used_mb']} MB / {metrics['memory']['total_mb']} MB ({metrics['memory']['percent']}%)")
        print(f"Swap:        {metrics['memory']['swap_used_mb']} MB / {metrics['memory']['swap_total_mb']} MB (Swappiness: {metrics['memory']['swappiness']})")
        print(f"Audio:       {summary['audio']['primary']}")
        for g in summary['gpus']:
            print(f"GPU:         {g['vendor']} - {g['description']} (Driver: {g['driver']})")
        for d in metrics['disks']:
            print(f"Disk [{d['mount']}]: {d['used']} / {d['total']} ({d['percent']}%) on {d['device']}")
        print("="*50 + "\n")
        return

    if args.preset:
        preset_map = {
            "gaming": "preset_gaming",
            "developer": "preset_developer",
            "debloat": "preset_debloat_privacy",
            "creator": "preset_creator"
        }
        target_preset = preset_map.get(args.preset)
        presets_mgr = PresetsManager(detector=detector, runner=runner)
        print(f"[LinForge] Applying preset: {args.preset}...")
        presets_mgr.apply_preset(target_preset, callback=print_cli_callback)
        return

    if args.update_all:
        maint = MaintenanceManager(detector=detector, runner=runner)
        print("[LinForge] Starting Universal 1-Click System Update...")
        maint.run_universal_update(callback=print_cli_callback)
        return

    if args.clean:
        cleaner = CleanupManager(detector=detector, runner=runner)
        print("[LinForge] Starting Full System Deep Cleanup...")
        cleaner.run_full_cleanup(callback=print_cli_callback)
        return

    if args.gaming:
        tweaks = TweaksManager(detector=detector, runner=runner)
        print("[LinForge] Applying Gaming & Low Latency Kernel Tweaks...")
        tweaks.apply_tweak("tweak_gaming_sysctl", callback=print_cli_callback)
        tweaks.apply_tweak("tweak_swappiness_10", callback=print_cli_callback)
        tweaks.apply_tweak("tweak_split_lock", callback=print_cli_callback)
        tweaks.apply_tweak("tweak_bbr_tcp", callback=print_cli_callback)
        return

    if args.fix_audio:
        drivers = DriverManager(detector=detector, runner=runner)
        print("[LinForge] Repairing PipeWire & WirePlumber Audio Stack...")
        drivers.setup_pipewire_audio(callback=print_cli_callback)
        return

    if args.fix_packages:
        trouble = TroubleshootManager(detector=detector, runner=runner)
        print("[LinForge] Fixing Package Manager Database & APT Locks...")
        trouble.run_fix("fix_apt_locks", callback=print_cli_callback)
        return

    if args.tui:
        run_tui()
        return

    # Check if graphical display session is active
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    if args.gui or has_display:
        try:
            launch_gui(port=args.port, open_browser=not args.headless)
        except Exception as e:
            print(f"[Notice] GUI launch failed ({e}), switching to interactive TUI...")
            run_tui()
    else:
        # Fallback to TUI if in pure SSH or headless terminal
        run_tui()


if __name__ == "__main__":
    main()
