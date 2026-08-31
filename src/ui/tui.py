"""
LinForge - Interactive Terminal User Interface (TUI)
Provides a rich ANSI-colored interactive menu for headless servers, SSH sessions,
and minimal terminal-only environments.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

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


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
  ██╗     ██╗███╗   ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
  ██║     ██║████╗  ██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ██║     ██║██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
  ██║     ██║██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
  ███████╗██║██║ ╚████║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
  ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{Colors.RESET}
  {Colors.BOLD}LinForge - The Ultimate Linux Setup & Maintenance Suite{Colors.RESET}
  {Colors.DIM}Engineered for Kubuntu, Ubuntu, Debian, Fedora, Arch & openSUSE{Colors.RESET}
    """
    print(banner)


def tui_callback(stream_type: str, msg: str):
    if stream_type == "system":
        print(f"{Colors.BLUE}[LinForge]{Colors.RESET} {msg}")
    elif stream_type == "stderr":
        print(f"{Colors.RED}[Error]{Colors.RESET} {msg}")
    else:
        print(f"  {msg}")


def run_tui():
    """Runs the interactive terminal menu loop."""
    detector = SystemDetector()
    monitor = SystemMonitor()
    runner = CommandRunner()

    apps_mgr = AppManager(detector=detector, runner=runner)
    drivers_mgr = DriverManager(detector=detector, runner=runner)
    tweaks_mgr = TweaksManager(detector=detector, runner=runner)
    cleanup_mgr = CleanupManager(detector=detector, runner=runner)
    troubleshoot_mgr = TroubleshootManager(detector=detector, runner=runner)
    dev_mgr = DeveloperManager(detector=detector, runner=runner)
    maint_mgr = MaintenanceManager(detector=detector, runner=runner)
    presets_mgr = PresetsManager(
        detector=detector,
        runner=runner,
        apps_mgr=apps_mgr,
        drivers_mgr=drivers_mgr,
        tweaks_mgr=tweaks_mgr,
        cleanup_mgr=cleanup_mgr,
        dev_mgr=dev_mgr
    )

    distro = detector.get_distro_info()

    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print_banner()
        print(f"  {Colors.GREEN}System:{Colors.RESET} {distro['pretty_name']} | {Colors.GREEN}Kernel:{Colors.RESET} {distro['kernel']} | {Colors.GREEN}Host:{Colors.RESET} {distro['hostname']}\n")

        print(f"  {Colors.BOLD}Select an operation category:{Colors.RESET}")
        print(f"  {Colors.YELLOW}[P]{Colors.RESET} 🌟 1-Click System Presets (Gaming Rig, Dev Station, Debloat)")
        print(f"  {Colors.CYAN}[1]{Colors.RESET} 📦 App Store & Bulk Installer (100+ Apps)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET} ⚡ Performance & Gaming Tweaks (Memory Maps, Swappiness, ZRAM)")
        print(f"  {Colors.CYAN}[3]{Colors.RESET} 🔧 Driver Doctor & Hardware Enabler (NVIDIA, AMD, Wi-Fi, Audio)")
        print(f"  {Colors.CYAN}[4]{Colors.RESET} 🧹 Deep System Cleanup (Cache, Journals, Snaps, SSD TRIM)")
        print(f"  {Colors.CYAN}[5]{Colors.RESET} 🛠️ Emergency Troubleshooter & Repairs (APT locks, DNS, Perms)")
        print(f"  {Colors.CYAN}[6]{Colors.RESET} 💻 Developer Stacks & Modern Shell (Node, Python AI, Rust, Docker)")
        print(f"  {Colors.CYAN}[7]{Colors.RESET} 🔄 Universal 1-Click System Updater (APT+Flatpak+Snap+Firmware)")
        print(f"  {Colors.CYAN}[8]{Colors.RESET} 📊 Live Hardware Specs & Diagnostics")
        print(f"  {Colors.RED}[0]{Colors.RESET} 🚪 Exit LinForge\n")

        choice = input(f"  {Colors.BOLD}Enter choice [P, 0-8]: {Colors.RESET}").strip()

        if choice == "0":
            print(f"\n{Colors.GREEN}Thank you for using LinForge! Have a great day.{Colors.RESET}\n")
            break

        elif choice.upper() == "P":
            presets = presets_mgr.get_presets()
            print(f"\n{Colors.BOLD}Available System Transformation Presets:{Colors.RESET}")
            for idx, p in enumerate(presets, 1):
                print(f"  {idx}) {Colors.YELLOW}{p['name']}{Colors.RESET} - {p['tagline']}")
            print("  b) Back")

            sel = input("\nEnter choice [1-4]: ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(presets):
                    presets_mgr.apply_preset(presets[idx]["id"], callback=tui_callback)
                    input("\nPress Enter to continue...")

        elif choice == "1":
            apps = apps_mgr.get_apps()
            print(f"\n{Colors.BOLD}Available Applications ({len(apps)} total):{Colors.RESET}")
            for idx, a in enumerate(apps, 1):
                status = f"{Colors.GREEN}[Installed]{Colors.RESET}" if a.get("is_installed") else f"{Colors.DIM}[Not Installed]{Colors.RESET}"
                print(f"  {idx:2d}) {a['name']:<30} {status} - {a['description'][:45]}...")
            
            sel = input("\nEnter app numbers separated by commas (e.g. 1,3,7) or 'b' for back: ").strip()
            if sel.lower() != "b" and sel:
                indices = [int(i.strip()) - 1 for i in sel.split(",") if i.strip().isdigit()]
                chosen_ids = [apps[i]["id"] for i in indices if 0 <= i < len(apps)]
                if chosen_ids:
                    print(f"\nInstalling: {', '.join(chosen_ids)}")
                    apps_mgr.install_batch(chosen_ids, callback=tui_callback)
                    input("\nPress Enter to continue...")

        elif choice == "2":
            tweaks = tweaks_mgr.get_tweaks()
            print(f"\n{Colors.BOLD}Performance & System Tweaks:{Colors.RESET}")
            for idx, tw in enumerate(tweaks, 1):
                status = f"{Colors.GREEN}[Applied]{Colors.RESET}" if tw.get("is_applied") else f"{Colors.DIM}[Inactive]{Colors.RESET}"
                print(f"  {idx:2d}) {tw['name']:<45} {status}")
            
            sel = input("\nEnter tweak number to apply/revert (e.g. 1) or 'all' or 'b' for back: ").strip()
            if sel.lower() == "all":
                tweaks_mgr.apply_batch([t["id"] for t in tweaks], callback=tui_callback)
                input("\nPress Enter to continue...")
            elif sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(tweaks):
                    tw = tweaks[idx]
                    if tw.get("is_applied"):
                        tweaks_mgr.revert_tweak(tw["id"], callback=tui_callback)
                    else:
                        tweaks_mgr.apply_tweak(tw["id"], callback=tui_callback)
                    input("\nPress Enter to continue...")

        elif choice == "3":
            print(f"\n{Colors.BOLD}Driver Doctor & Hardware Enablers:{Colors.RESET}")
            print("  1) Install Recommended NVIDIA Drivers & Wayland Fixes")
            print("  2) Update to Kisak-Mesa Fresh PPA for AMD/Intel Vulkan")
            print("  3) Install Broadcom BCM43xx Wi-Fi Drivers")
            print("  4) Install Realtek Wireless & DKMS Drivers")
            print("  5) Configure Low-Latency PipeWire Audio Stack")
            print("  6) Setup Game Controllers (DualSense / Xbox) udev rules")
            print("  7) Configure OpenRGB Motherboard Lighting udev rules")
            print("  8) Install auto-cpufreq for Laptop Battery Life")
            print("  9) Install XanMod Gaming Kernel")
            print("  b) Back")

            sel = input("\nEnter choice [1-9]: ").strip()
            if sel == "1":
                drivers_mgr.install_nvidia_recommended(callback=tui_callback)
            elif sel == "2":
                drivers_mgr.install_amd_kisak_mesa(callback=tui_callback)
            elif sel == "3":
                drivers_mgr.install_broadcom_wifi(callback=tui_callback)
            elif sel == "4":
                drivers_mgr.install_realtek_wifi(callback=tui_callback)
            elif sel == "5":
                drivers_mgr.setup_pipewire_audio(callback=tui_callback)
            elif sel == "6":
                drivers_mgr.setup_game_controllers(callback=tui_callback)
            elif sel == "7":
                drivers_mgr.setup_openrgb_udev(callback=tui_callback)
            elif sel == "8":
                drivers_mgr.install_autocpufreq_battery(callback=tui_callback)
            elif sel == "9":
                drivers_mgr.install_xanmod_kernel(callback=tui_callback)
            if sel in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                input("\nPress Enter to continue...")

        elif choice == "4":
            print(f"\n{Colors.BOLD}System Cleanup Options:{Colors.RESET}")
            print("  1) Full System Deep Clean (All-in-one)")
            print("  2) Clean Package Caches (APT/DNF/Pacman) & Orphaned Packages")
            print("  3) Vacuum systemd journal logs to 100MB")
            print("  4) Remove unused Flatpak runtimes")
            print("  5) Purge disabled Snap revisions")
            print("  6) Clean thumbnail caches & crash logs")
            print("  7) Run SSD TRIM (fstrim -av)")
            print("  b) Back")

            sel = input("\nEnter choice [1-7]: ").strip()
            if sel == "1":
                cleanup_mgr.run_full_cleanup(callback=tui_callback)
            elif sel == "2":
                cleanup_mgr.clean_package_cache(callback=tui_callback)
            elif sel == "3":
                cleanup_mgr.vacuum_systemd_journal(callback=tui_callback)
            elif sel == "4":
                cleanup_mgr.clean_flatpak_unused(callback=tui_callback)
            elif sel == "5":
                cleanup_mgr.purge_snap_old_revisions(callback=tui_callback)
            elif sel == "6":
                cleanup_mgr.clean_user_caches(callback=tui_callback)
            elif sel == "7":
                cleanup_mgr.run_ssd_trim(callback=tui_callback)
            if sel in ["1", "2", "3", "4", "5", "6", "7"]:
                input("\nPress Enter to continue...")

        elif choice == "5":
            fixes = troubleshoot_mgr.get_troubleshooters()
            print(f"\n{Colors.BOLD}System Troubleshooter & Emergency Repairs:{Colors.RESET}")
            for idx, f in enumerate(fixes, 1):
                st = f"{Colors.RED}[Issue Detected]{Colors.RESET}" if f.get("status") == "detected" else f"{Colors.GREEN}[Healthy]{Colors.RESET}"
                print(f"  {idx:2d}) {f['name']:<50} {st}")
            
            print("  a) Run All Diagnostic Repairs")
            print("  b) Back")

            sel = input("\nEnter repair number or 'a': ").strip()
            if sel.lower() == "a":
                troubleshoot_mgr.run_all_fixes(callback=tui_callback)
                input("\nPress Enter to continue...")
            elif sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(fixes):
                    troubleshoot_mgr.run_fix(fixes[idx]["id"], callback=tui_callback)
                    input("\nPress Enter to continue...")

        elif choice == "6":
            print(f"\n{Colors.BOLD}Developer Stacks & Modern Shell Setup:{Colors.RESET}")
            print("  1) Web Dev Stack (Node.js LTS, Bun, Deno, pnpm)")
            print("  2) Python & AI Stack (uv package manager, Ollama LLM)")
            print("  3) Rust & C/C++ Systems Stack (rustup, build-essential, clang, cmake)")
            print("  4) DevOps Stack (Docker CE Engine, Compose, Kubectl, GitHub CLI)")
            print("  5) Modern CLI Tools (eza, bat, zoxide, fzf, ripgrep, Starship prompt)")
            print("  6) Zsh + Oh-My-Zsh with syntax highlighting & auto-suggestions")
            print("  b) Back")

            sel = input("\nEnter choice [1-6]: ").strip()
            if sel == "1":
                dev_mgr.install_web_stack(callback=tui_callback)
            elif sel == "2":
                dev_mgr.install_python_ai_stack(callback=tui_callback)
            elif sel == "3":
                dev_mgr.install_rust_systems_stack(callback=tui_callback)
            elif sel == "4":
                dev_mgr.install_devops_stack(callback=tui_callback)
            elif sel == "5":
                dev_mgr.install_modern_cli_tools(callback=tui_callback)
            elif sel == "6":
                dev_mgr.install_zsh_ohmyzsh(callback=tui_callback)
            if sel in ["1", "2", "3", "4", "5", "6"]:
                input("\nPress Enter to continue...")

        elif choice == "7":
            print(f"\n{Colors.BOLD}Universal Maintenance & Upgrades:{Colors.RESET}")
            print("  1) Run Universal 1-Click System Update (APT + Flatpak + Snap + Firmware)")
            print("  2) Create Timeshift System Restore Point")
            print("  3) Backup User Dotfiles (~/.bashrc, ~/.config, etc.)")
            print("  4) Clean Old Linux Kernels")
            print("  b) Back")

            sel = input("\nEnter choice [1-4]: ").strip()
            if sel == "1":
                maint_mgr.run_universal_update(callback=tui_callback)
            elif sel == "2":
                maint_mgr.create_timeshift_snapshot(callback=tui_callback)
            elif sel == "3":
                maint_mgr.backup_user_dotfiles(callback=tui_callback)
            elif sel == "4":
                maint_mgr.clean_old_kernels(callback=tui_callback)
            if sel in ["1", "2", "3", "4"]:
                input("\nPress Enter to continue...")

        elif choice == "8":
            metrics = monitor.get_all_metrics()
            summary = detector.get_full_summary()
            print(f"\n{Colors.BOLD}--- Live System Diagnostics ---{Colors.RESET}")
            print(f"  CPU:         {metrics['cpu']['model']} ({metrics['cpu']['cores']} cores @ {metrics['cpu']['frequency_mhz']} MHz)")
            print(f"  CPU Usage:   {metrics['cpu']['usage_percent']}% (Temp: {metrics['cpu']['temperature_c'] or 'N/A'}°C)")
            print(f"  Memory:      {metrics['memory']['used_mb']} MB / {metrics['memory']['total_mb']} MB ({metrics['memory']['percent']}%)")
            print(f"  Swap:        {metrics['memory']['swap_used_mb']} MB / {metrics['memory']['swap_total_mb']} MB (Swappiness: {metrics['memory']['swappiness']})")
            print(f"  Network:     ↓ {metrics['network']['down_kbs']} KB/s | ↑ {metrics['network']['up_kbs']} KB/s")
            print(f"  Desktop:     {summary['desktop']['name']} {summary['desktop']['version']} ({summary['desktop']['session_type'].upper()})")
            print(f"  Audio:       {summary['audio']['primary']}")
            for g in summary['gpus']:
                print(f"  GPU:         {g['vendor']} - {g['description']} (Driver: {g['driver']})")
            for d in metrics['disks']:
                print(f"  Disk [{d['mount']}]: {d['used']} / {d['total']} ({d['percent']}%) on {d['device']} ({d['fs_type']})")
            input("\nPress Enter to return to main menu...")
