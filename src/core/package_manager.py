"""
LinForge - Universal Package Manager Abstraction Layer
Provides unified interface across APT, DNF, Pacman, Zypper, Flatpak, Snap, and Native Repositories.
"""

import os
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from .detector import SystemDetector
    from .runner import CommandRunner, CommandResult


class PackageManager:
    """Universal package manager abstraction layer."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.distro_info = self.detector.get_distro_info()
        self.family = self.distro_info.get("family", "debian")

    def get_primary_native_manager(self) -> str:
        """Returns the primary native package manager (apt, dnf, pacman, zypper)."""
        if self.family == "debian" or shutil.which("apt"):
            return "apt"
        elif self.family == "fedora" or shutil.which("dnf"):
            return "dnf"
        elif self.family == "arch" or shutil.which("pacman"):
            return "pacman"
        elif self.family == "suse" or shutil.which("zypper"):
            return "zypper"
        return "apt"

    def is_package_installed(self, package_name: str, manager_type: str = "auto") -> bool:
        """Checks if a given package or binary is installed on the system."""
        if shutil.which(package_name):
            return True

        mgr = self.get_primary_native_manager() if manager_type == "auto" else manager_type

        try:
            if mgr == "apt" and shutil.which("dpkg"):
                res = subprocess.run(["dpkg", "-s", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            elif mgr == "dnf" and shutil.which("rpm"):
                res = subprocess.run(["rpm", "-q", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            elif mgr == "pacman" and shutil.which("pacman"):
                res = subprocess.run(["pacman", "-Q", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            elif mgr == "flatpak" and shutil.which("flatpak"):
                res = subprocess.run(["flatpak", "info", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
            elif mgr == "snap" and shutil.which("snap"):
                res = subprocess.run(["snap", "list", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return res.returncode == 0
        except Exception:
            pass

        return False

    def install_native_packages(
        self,
        packages: List[str],
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs native distribution packages with auto-yes flags."""
        if not packages:
            return CommandResult(0, "No packages specified", "", 0.0)

        mgr = self.get_primary_native_manager()
        pkg_str = " ".join(packages)

        if mgr == "apt":
            cmd = f"apt-get update -qq && apt-get install -y --no-install-recommends {pkg_str}"
        elif mgr == "dnf":
            cmd = f"dnf install -y {pkg_str}"
        elif mgr == "pacman":
            cmd = f"pacman -S --needed --noconfirm {pkg_str}"
        elif mgr == "zypper":
            cmd = f"zypper --non-interactive --auto-agree-with-licenses install {pkg_str}"
        else:
            cmd = f"apt-get install -y {pkg_str}"

        return self.runner.run_script_block(cmd, use_sudo=True, callback=callback)

    def remove_native_packages(
        self,
        packages: List[str],
        purge: bool = True,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Removes native packages."""
        if not packages:
            return CommandResult(0, "No packages specified", "", 0.0)

        mgr = self.get_primary_native_manager()
        pkg_str = " ".join(packages)

        if mgr == "apt":
            flag = "--purge" if purge else ""
            cmd = f"apt-get remove -y {flag} {pkg_str}"
        elif mgr == "dnf":
            cmd = f"dnf remove -y {pkg_str}"
        elif mgr == "pacman":
            cmd = f"pacman -Rns --noconfirm {pkg_str}"
        elif mgr == "zypper":
            cmd = f"zypper --non-interactive remove {pkg_str}"
        else:
            cmd = f"apt-get remove -y {pkg_str}"

        return self.runner.run_script_block(cmd, use_sudo=True, callback=callback)

    def install_flatpak(
        self,
        flatpak_id: str,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a Flatpak from Flathub."""
        script = f"""
        if ! command -v flatpak >/dev/null 2>&1; then
            echo "Installing flatpak daemon..."
            if command -v apt-get >/dev/null 2>&1; then
                apt-get update -qq && apt-get install -y flatpak
            elif command -v dnf >/dev/null 2>&1; then
                dnf install -y flatpak
            elif command -v pacman >/dev/null 2>&1; then
                pacman -S --needed --noconfirm flatpak
            fi
        fi

        echo "Ensuring Flathub repository is configured..."
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true

        echo "Installing {flatpak_id} from Flathub..."
        flatpak install -y flathub {flatpak_id}
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_snap(
        self,
        snap_name: str,
        classic: bool = False,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a Snap package."""
        flag = "--classic" if classic else ""
        script = f"""
        if ! command -v snap >/dev/null 2>&1; then
            echo "Installing snapd..."
            if command -v apt-get >/dev/null 2>&1; then
                apt-get update -qq && apt-get install -y snapd
            elif command -v dnf >/dev/null 2>&1; then
                dnf install -y snapd
            elif command -v pacman >/dev/null 2>&1; then
                pacman -S --needed --noconfirm snapd
            fi
            systemctl enable --now snapd.socket 2>/dev/null || true
            ln -s /var/lib/snapd/snap /snap 2>/dev/null || true
        fi

        echo "Installing snap package: {snap_name} {flag}..."
        snap install {snap_name} {flag}
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def add_apt_repository_secure(
        self,
        repo_name: str,
        gpg_key_url: str,
        sources_line: str,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """
        Adds a third-party APT repository following modern deb822 / keyring standards
        without using deprecated apt-key.
        """
        keyring_dir = "/etc/apt/keyrings"
        key_file = f"{keyring_dir}/{repo_name}.gpg"
        list_file = f"/etc/apt/sources.list.d/{repo_name}.list"

        script = f"""
        mkdir -p {keyring_dir}
        chmod 0755 {keyring_dir}
        curl -fsSL "{gpg_key_url}" | gpg --dearmor -o "{key_file}.tmp"
        mv "{key_file}.tmp" "{key_file}"
        chmod 0644 "{key_file}"
        echo "{sources_line}" > "{list_file}"
        apt-get update -qq
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def update_system_all(
        self,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Performs a comprehensive update across Native, Flatpak, Snap, and Firmware."""
        commands = []
        mgr = self.get_primary_native_manager()

        if mgr == "apt":
            commands.append("apt-get update && apt-get dist-upgrade -y && apt-get autoremove -y")
        elif mgr == "dnf":
            commands.append("dnf upgrade --refresh -y && dnf autoremove -y")
        elif mgr == "pacman":
            commands.append("pacman -Syu --noconfirm")
        elif mgr == "zypper":
            commands.append("zypper --non-interactive --auto-agree-with-licenses update")

        if shutil.which("flatpak"):
            commands.append("flatpak update -y")

        if shutil.which("snap"):
            commands.append("snap refresh")

        if shutil.which("fwupdmgr"):
            commands.append("fwupdmgr refresh 2>/dev/null || true")

        full_script = "\n".join(commands)
        return self.runner.run_script_block(full_script, use_sudo=True, callback=callback)
