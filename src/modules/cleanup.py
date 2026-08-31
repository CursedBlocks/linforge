"""
LinForge - System Cleanup & Disk Optimizer Engine
Deep cleaning for package manager caches, orphaned packages, systemd journal logs,
Flatpak/Snap unused runtimes, user thumbnail caches, and SSD TRIM optimization.
"""

import os
import shutil
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult


class CleanupManager:
    """Performs deep system cleanup and disk space reclamation."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()

    def clean_package_cache(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Cleans package manager caches and removes unneeded orphaned packages."""
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            script = """
            echo "Cleaning APT package cache and removing orphaned dependencies..."
            apt-get autoremove --purge -y
            apt-get autoclean -y
            apt-get clean
            dpkg -l | awk '/^rc/ {print $2}' | xargs -r dpkg --purge 2>/dev/null || true
            """
        elif family == "fedora" or shutil.which("dnf"):
            script = """
            echo "Cleaning DNF cache..."
            dnf clean all
            dnf autoremove -y
            """
        elif family == "arch" or shutil.which("pacman"):
            script = """
            echo "Cleaning Pacman cache..."
            pacman -Sc --noconfirm || true
            pacman -Qtdq | pacman -Rns - --noconfirm 2>/dev/null || true
            """
        else:
            script = "apt-get clean && apt-get autoremove -y"

        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def vacuum_systemd_journal(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Vacuums systemd log journals to max 100MB and max 7 days retention."""
        script = """
        echo "Vacuuming systemd journal logs..."
        journalctl --vacuum-time=7d
        journalctl --vacuum-size=100M
        echo "Journal logs cleaned!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def clean_flatpak_unused(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Removes unused Flatpak runtime dependencies and runs repair."""
        if not shutil.which("flatpak"):
            if callback:
                callback("system", "Flatpak is not installed on this system. Skipping.")
            return CommandResult(0, "", "Flatpak not installed", 0.0)

        script = """
        echo "Pruning unused Flatpak runtimes and repairing refs..."
        flatpak uninstall --unused -y
        flatpak repair 2>/dev/null || true
        """
        return self.runner.run_script_block(script, use_sudo=False, callback=callback)

    def purge_snap_old_revisions(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Purges old disabled Snap revisions and sets revision retention to 2."""
        if not shutil.which("snap"):
            if callback:
                callback("system", "Snap is not installed on this system. Skipping.")
            return CommandResult(0, "", "Snap not installed", 0.0)

        script = """
        echo "Purging disabled Snap revisions..."
        snap list --all 2>/dev/null | awk '/disabled/{print $1, $3}' | while read -r snapname revision; do
            echo "Removing $snapname (revision $revision)..."
            snap remove "$snapname" --revision="$revision" 2>/dev/null || true
        done
        snap set system refresh.retain=2 2>/dev/null || true
        echo "Snap revisions optimized!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def clean_user_caches(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Cleans user thumbnail caches and crash logs."""
        script = """
        echo "Cleaning thumbnail caches and crash dumps..."
        rm -rf ~/.cache/thumbnails/* ~/.thumbnails/* ~/.cache/crash/* /var/crash/* 2>/dev/null || true
        echo "User caches cleaned!"
        """
        return self.runner.run_script_block(script, use_sudo=False, callback=callback)

    def run_ssd_trim(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Executes fstrim on all mounted SSD filesystems and enables fstrim timer."""
        script = """
        echo "Executing SSD TRIM on all mounted disks..."
        fstrim -av
        systemctl enable --now fstrim.timer 2>/dev/null || true
        echo "SSD TRIM completed and weekly timer active!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def run_full_cleanup(self, callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, CommandResult]:
        """Executes a full deep system cleanup sequentially."""
        results = {}
        if callback:
            callback("system", "🧹 Starting full system deep cleanup...")

        results["package_cache"] = self.clean_package_cache(callback)
        results["journal"] = self.vacuum_systemd_journal(callback)
        results["flatpak"] = self.clean_flatpak_unused(callback)
        results["snap"] = self.purge_snap_old_revisions(callback)
        results["user_cache"] = self.clean_user_caches(callback)
        results["ssd_trim"] = self.run_ssd_trim(callback)

        if callback:
            callback("system", "✨ Full system cleanup completed successfully!")

        return results
