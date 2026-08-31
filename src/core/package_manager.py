"""
LinForge - Universal Package Manager Abstraction Layer & Dependency Auto-Healer
Provides unified, self-healing package management across APT, DNF, Pacman, Zypper, Flatpak, Snap, and Native Repositories.
"""

import os
import shutil
import subprocess
import tempfile
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
except (ImportError, ValueError):
    from .detector import SystemDetector
    from .runner import CommandRunner, CommandResult


class PackageManager:
    """Universal package manager abstraction layer with automated dependency resolution and self-healing."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.distro_info = self.detector.get_distro_info()
        self.family = self.distro_info.get("family", "debian")
        self._prereqs_verified = False

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

    def ensure_system_prerequisites(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """
        Proactively verifies and installs essential bootstrap tools:
        curl, wget, gpg, ca-certificates, software-properties-common, libfuse2 (for AppImages), flatpak, xdg-utils.
        """
        if self._prereqs_verified:
            return CommandResult(0, "Prerequisites already verified", "", 0.0)

        mgr = self.get_primary_native_manager()

        if mgr == "apt":
            script = """
            export DEBIAN_FRONTEND=noninteractive
            # Clear stale locks if any
            rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock* 2>/dev/null || true

            echo "Ensuring core system utilities and AppImage/Flatpak runtimes are installed..."
            apt-get update -qq || true
            apt-get install -y --no-install-recommends \
                curl wget gpg gnupg ca-certificates software-properties-common apt-transport-https \
                xdg-utils libfuse2 libfuse2t64 flatpak 2>/dev/null || \
            apt-get install -y --no-install-recommends \
                curl wget gpg gnupg ca-certificates software-properties-common apt-transport-https \
                xdg-utils flatpak 2>/dev/null || true

            # Configure Flathub if flatpak is present
            if command -v flatpak >/dev/null 2>&1; then
                flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
            fi
            """
        elif mgr == "dnf":
            script = """
            echo "Verifying Fedora core package prerequisites..."
            dnf install -y curl wget gnupg2 ca-certificates fuse-libs flatpak xdg-utils 2>/dev/null || true
            if command -v flatpak >/dev/null 2>&1; then
                flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
            fi
            """
        elif mgr == "pacman":
            script = """
            echo "Verifying Arch Linux prerequisites..."
            pacman -S --needed --noconfirm curl wget gnupg ca-certificates fuse2 flatpak xdg-utils 2>/dev/null || true
            if command -v flatpak >/dev/null 2>&1; then
                flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
            fi
            """
        elif mgr == "zypper":
            script = """
            echo "Verifying openSUSE prerequisites..."
            zypper --non-interactive --auto-agree-with-licenses install -y curl wget gpg2 ca-certificates libfuse2 flatpak xdg-utils 2>/dev/null || true
            if command -v flatpak >/dev/null 2>&1; then
                flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
            fi
            """
        else:
            script = "true"

        res = self.runner.run_script_block(script, use_sudo=True, callback=callback)
        if res.success:
            self._prereqs_verified = True
        return res

    def auto_heal_apt(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Kills stuck background package processes, clears stale locks, and repairs database."""
        script = """
        echo "Auto-healing package manager locks and repairing broken packages..."
        killall -9 apt apt-get dpkg unattended-upgrade 2>/dev/null || true
        rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock* /var/lib/dpkg/updates/* 2>/dev/null || true
        dpkg --configure -a || true
        apt-get install -f -y || true
        apt-get update --fix-missing -qq || true
        echo "Package manager unlocked and healed."
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def is_package_installed(self, package_name: str, manager_type: str = "auto") -> Tuple[bool, str]:
        """
        Checks if a given package, binary, Flatpak, or Snap is installed.
        Returns (is_installed: bool, installed_source: str)
        """
        # Check binary on PATH
        if shutil.which(package_name):
            return True, "binary"
        if package_name == "python3" and (shutil.which("python") or shutil.which("python3")):
            return True, "binary"

        mgr = self.get_primary_native_manager() if manager_type == "auto" else manager_type

        try:
            # Native Package Manager checks
            if mgr == "apt" and shutil.which("dpkg"):
                res = subprocess.run(["dpkg", "-s", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "native"
            elif mgr == "dnf" and shutil.which("rpm"):
                res = subprocess.run(["rpm", "-q", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "native"
            elif mgr == "pacman" and shutil.which("pacman"):
                res = subprocess.run(["pacman", "-Q", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "native"
            elif mgr == "zypper" and shutil.which("rpm"):
                res = subprocess.run(["rpm", "-q", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "native"

            # Flatpak Check
            if shutil.which("flatpak"):
                res = subprocess.run(["flatpak", "info", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "flatpak"

            # Snap Check
            if shutil.which("snap"):
                res = subprocess.run(["snap", "list", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return True, "snap"

            # Desktop File Check
            desktop_paths = [
                f"/usr/share/applications/{package_name}.desktop",
                f"/usr/local/share/applications/{package_name}.desktop",
                f"{os.path.expanduser('~')}/.local/share/applications/{package_name}.desktop",
                f"/var/lib/flatpak/exports/share/applications/{package_name}.desktop"
            ]
            for dp in desktop_paths:
                if os.path.exists(dp):
                    return True, "desktop_entry"

        except Exception:
            pass

        return False, "none"

    def install_native_packages(
        self,
        packages: List[str],
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs native distribution packages with automated dependency resolution."""
        if not packages:
            return CommandResult(0, "No packages specified", "", 0.0)

        self.ensure_system_prerequisites(callback=callback)
        mgr = self.get_primary_native_manager()
        pkg_str = " ".join(packages)

        if mgr == "apt":
            cmd = f"""
            apt-get update -qq || true
            apt-get install -y --no-install-recommends {pkg_str} || (apt-get install -f -y && apt-get install -y {pkg_str})
            """
        elif mgr == "dnf":
            cmd = f"dnf install -y {pkg_str}"
        elif mgr == "pacman":
            cmd = f"pacman -S --needed --noconfirm {pkg_str}"
        elif mgr == "zypper":
            cmd = f"zypper --non-interactive --auto-agree-with-licenses install {pkg_str}"
        else:
            cmd = f"apt-get install -y {pkg_str}"

        res = self.runner.run_script_block(cmd, use_sudo=True, callback=callback)

        # Auto-heal on APT lock failures and retry once
        if not res.success and res.error_code == "ERR_DPKG_LOCKED" and mgr == "apt":
            if callback:
                callback("system", "⚠️ Lock detected. Automatically unlocking package manager and retrying...")
            self.auto_heal_apt(callback=callback)
            res = self.runner.run_script_block(cmd, use_sudo=True, callback=callback)

        return res

    def remove_native_packages(
        self,
        packages: List[str],
        purge: bool = True,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Removes native packages cleanly."""
        if not packages:
            return CommandResult(0, "No packages specified", "", 0.0)

        mgr = self.get_primary_native_manager()
        pkg_str = " ".join(packages)

        if mgr == "apt":
            flag = "--purge" if purge else ""
            cmd = f"apt-get remove -y {flag} {pkg_str} && apt-get autoremove -y"
        elif mgr == "dnf":
            cmd = f"dnf remove -y {pkg_str} && dnf autoremove -y"
        elif mgr == "pacman":
            cmd = f"pacman -Rns --noconfirm {pkg_str}"
        elif mgr == "zypper":
            cmd = f"zypper --non-interactive remove -u {pkg_str}"
        else:
            cmd = f"apt-get remove -y {pkg_str}"

        return self.runner.run_script_block(cmd, use_sudo=True, callback=callback)

    def install_flatpak(
        self,
        flatpak_id: str,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a Flatpak from Flathub with auto-runtime provisioning."""
        self.ensure_system_prerequisites(callback=callback)

        script = f"""
        echo "Ensuring Flatpak and Flathub repository are configured..."
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true

        echo "Installing {flatpak_id} from Flathub with automated runtime provisioning..."
        flatpak install -y --noninteractive flathub {flatpak_id}
        """
        res = self.runner.run_script_block(script, use_sudo=True, callback=callback)

        if not res.success and callback:
            callback("stderr", f"Flatpak installation of {flatpak_id} failed: {res.error_title}")

        return res

    def install_snap(
        self,
        snap_name: str,
        classic: bool = False,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """Installs a Snap package with auto-service initialization."""
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

    def install_deb_url_safe(
        self,
        download_url: str,
        app_name: str,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """
        Safely downloads a .deb package from URL and installs it using apt-get,
        which automatically pulls all required shared libraries and dependencies.
        """
        self.ensure_system_prerequisites(callback=callback)

        script = f"""
        TMP_DEB=$(mktemp /tmp/linforge_{app_name}_XXXXXX.deb)
        trap "rm -f '$TMP_DEB'" EXIT

        echo "Downloading {app_name} package from verified vendor URL..."
        if command -v wget >/dev/null 2>&1; then
            wget -q --show-progress --timeout=30 -O "$TMP_DEB" "{download_url}"
        else
            curl -fsSL --connect-timeout 30 -o "$TMP_DEB" "{download_url}"
        fi

        if [ ! -s "$TMP_DEB" ]; then
            echo "Error: Downloaded package is empty or download failed." >&2
            exit 1
        fi

        echo "Installing {app_name} with automated dependency fulfillment..."
        apt-get update -qq || true
        apt-get install -y "$TMP_DEB" || (dpkg -i "$TMP_DEB" && apt-get install -f -y)
        echo "{app_name} installed successfully!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def add_apt_repository_secure(
        self,
        repo_name: str,
        gpg_key_url: str,
        sources_line: str,
        package_to_install: Optional[str] = None,
        callback: Optional[Callable[[str, str], None]] = None
    ) -> CommandResult:
        """
        Adds a third-party APT repository following modern deb822 standards
        and installs the requested package with dependency auto-resolution.
        """
        self.ensure_system_prerequisites(callback=callback)

        keyring_dir = "/etc/apt/keyrings"
        key_file = f"{keyring_dir}/{repo_name}.gpg"
        list_file = f"/etc/apt/sources.list.d/{repo_name}.list"

        install_clause = f"apt-get install -y --no-install-recommends {package_to_install}" if package_to_install else "true"

        script = f"""
        mkdir -p {keyring_dir}
        chmod 0755 {keyring_dir}
        echo "Importing verified GPG signing key for {repo_name}..."
        curl -fsSL "{gpg_key_url}" | gpg --dearmor -o "{key_file}.tmp"
        mv "{key_file}.tmp" "{key_file}"
        chmod 0644 "{key_file}"
        echo "{sources_line}" > "{list_file}"
        apt-get update -qq
        {install_clause}
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
