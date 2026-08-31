"""
LinForge - Maintenance, Backups & Universal Updater Engine
Coordinates universal 1-click updates across all package ecosystems (APT, Flatpak, Snap, Firmware),
Timeshift / Btrfs snapshot creation, dotfile backups, and safe kernel management.
"""

import os
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult


class MaintenanceManager:
    """Manages system updates, snapshots, backups, and kernel lifecycle."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()

    def run_universal_update(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Runs universal updates across Native, Flatpak, Snap, and Firmware LVFS."""
        commands = []
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            commands.append("echo '=== Updating Native APT Packages ==='")
            commands.append("apt-get update && apt-get dist-upgrade -y && apt-get autoremove -y")
        elif family == "fedora" or shutil.which("dnf"):
            commands.append("echo '=== Updating Fedora DNF Packages ==='")
            commands.append("dnf upgrade --refresh -y && dnf autoremove -y")
        elif family == "arch" or shutil.which("pacman"):
            commands.append("echo '=== Updating Arch Pacman Packages ==='")
            commands.append("pacman -Syu --noconfirm")

        if shutil.which("flatpak"):
            commands.append("echo '=== Updating Flatpak Apps & Runtimes ==='")
            commands.append("flatpak update -y")

        if shutil.which("snap"):
            commands.append("echo '=== Refreshing Snap Packages ==='")
            commands.append("snap refresh")

        if shutil.which("fwupdtool") or shutil.which("fwupdmgr"):
            commands.append("echo '=== Checking Hardware Firmware (LVFS) ==='")
            commands.append("fwupdmgr refresh --force 2>/dev/null && fwupdmgr update -y 2>/dev/null || true")

        script = "\n".join(commands)
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def create_timeshift_snapshot(self, comment: str = "LinForge Backup", callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Creates an immediate Timeshift system restore point."""
        if not shutil.which("timeshift"):
            if callback:
                callback("system", "Timeshift is not installed. Installing timeshift...")
            self.runner.run_command("apt-get update && apt-get install -y timeshift", use_sudo=True, callback=callback)

        script = f"""
        echo "Creating system restore point with Timeshift..."
        timeshift --create --comments "{comment}" --tags D
        echo "Timeshift snapshot created successfully!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def backup_user_dotfiles(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Creates a timestamped tar.gz archive of user configurations and shell profiles."""
        script = """
        BACKUP_DIR="$HOME/LinForge-Backups"
        TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
        ARCHIVE="$BACKUP_DIR/dotfiles_backup_$TIMESTAMP.tar.gz"
        mkdir -p "$BACKUP_DIR"

        echo "Archiving dotfiles to $ARCHIVE..."
        tar -czf "$ARCHIVE" -C "$HOME" \
            .bashrc .zshrc .profile .gitconfig .config/MangoHud .config/pipewire .config/wireplumber 2>/dev/null || true

        echo "Backup completed: $ARCHIVE"
        """
        return self.runner.run_script_block(script, use_sudo=False, callback=callback)

    def clean_old_kernels(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Safely removes old unused Linux kernels keeping current and previous backup kernel."""
        script = """
        echo "Checking installed Linux kernel versions..."
        CURRENT_KERNEL=$(uname -r)
        echo "Active kernel in use: $CURRENT_KERNEL"
        apt-get --purge autoremove -y
        update-grub 2>/dev/null || grub-mkconfig -o /boot/grub/grub.cfg 2>/dev/null || true
        echo "Kernel cleanup complete!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)
