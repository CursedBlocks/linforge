"""
LinForge - Core Detection Engine
Detects Linux distribution, desktop environment, package managers,
kernel, CPU, GPU, audio subsystem, and display server.
"""

import os
import platform
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class SystemDetector:
    """Detects Linux distribution, hardware specs, and environment configuration."""

    def __init__(self):
        self._os_release = self._parse_os_release()

    def _parse_os_release(self) -> Dict[str, str]:
        """Parses /etc/os-release into a dictionary."""
        info = {}
        for path in ["/etc/os-release", "/usr/lib/os-release"]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                info[k.strip()] = v.strip().strip('"').strip("'")
                    break
                except Exception:
                    pass
        return info

    def get_distro_info(self) -> Dict[str, Any]:
        """Returns normalized distribution details."""
        distro_id = self._os_release.get("ID", platform.system()).lower()
        distro_id_like = self._os_release.get("ID_LIKE", "").lower().split()
        distro_name = self._os_release.get("NAME", platform.system())
        version = self._os_release.get("VERSION_ID", platform.release())
        pretty_name = self._os_release.get("PRETTY_NAME", f"{distro_name} {version}")
        codename = self._os_release.get("VERSION_CODENAME", "")

        # Determine family
        family = "unknown"
        if distro_id in ["ubuntu", "kubuntu", "xubuntu", "lubuntu", "ubuntu-mate", "pop", "mint", "elementary", "zorin", "neon", "tuxedo"] or "ubuntu" in distro_id_like or "debian" in distro_id_like:
            family = "debian"
        elif distro_id in ["debian"]:
            family = "debian"
        elif distro_id in ["fedora", "rhel", "centos", "rocky", "alma", "nobara"] or "fedora" in distro_id_like or "rhel" in distro_id_like:
            family = "fedora"
        elif distro_id in ["arch", "manjaro", "endeavouros", "garuda", "cachyos", "artix"] or "arch" in distro_id_like:
            family = "arch"
        elif distro_id in ["opensuse", "opensuse-tumbleweed", "opensuse-leap", "sles"] or "suse" in distro_id_like:
            family = "suse"

        de_info = self.get_desktop_environment()
        is_kubuntu = distro_id == "kubuntu" or (distro_id == "ubuntu" and de_info.get("name") == "KDE Plasma")
        is_ubuntu_based = family == "debian" and (distro_id == "ubuntu" or "ubuntu" in distro_id_like or distro_id in ["pop", "mint", "neon", "zorin", "kubuntu"])

        return {
            "id": distro_id,
            "id_like": distro_id_like,
            "name": distro_name,
            "pretty_name": pretty_name,
            "version": version,
            "codename": codename,
            "family": family,
            "is_kubuntu": is_kubuntu,
            "is_ubuntu_based": is_ubuntu_based,
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node()
        }

    def get_desktop_environment(self) -> Dict[str, str]:
        """Detects active Desktop Environment and Window Manager."""
        xdg_current = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        xdg_session_de = os.environ.get("XDG_SESSION_DESKTOP", "").upper()
        desktop_session = os.environ.get("DESKTOP_SESSION", "").upper()
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()

        de_name = "Unknown"
        de_version = ""

        if "KDE" in xdg_current or "KDE" in xdg_session_de or "PLASMA" in desktop_session:
            de_name = "KDE Plasma"
            try:
                out = subprocess.check_output(["plasmashell", "--version"], stderr=subprocess.DEVNULL, timeout=2).decode().strip()
                de_version = out.replace("plasmashell", "").strip()
            except Exception:
                pass
        elif "GNOME" in xdg_current or "GNOME" in xdg_session_de or "UBUNTU" in desktop_session:
            de_name = "GNOME"
            try:
                out = subprocess.check_output(["gnome-shell", "--version"], stderr=subprocess.DEVNULL, timeout=2).decode().strip()
                de_version = out.replace("GNOME Shell", "").strip()
            except Exception:
                pass
        elif "XFCE" in xdg_current or "XFCE" in desktop_session:
            de_name = "XFCE"
        elif "CINNAMON" in xdg_current or "CINNAMON" in desktop_session:
            de_name = "Cinnamon"
        elif "MATE" in xdg_current or "MATE" in desktop_session:
            de_name = "MATE"
        elif "COSMIC" in xdg_current or "COSMIC" in desktop_session:
            de_name = "COSMIC"
        elif "HYPRLAND" in xdg_current or "hyprland" in desktop_session.lower():
            de_name = "Hyprland (WM)"
        elif "SWAY" in xdg_current or "sway" in desktop_session.lower():
            de_name = "Sway (WM)"
        elif "I3" in xdg_current or "i3" in desktop_session.lower():
            de_name = "i3 (WM)"

        return {
            "name": de_name,
            "version": de_version,
            "session_type": session_type,  # wayland or x11
            "is_wayland": session_type == "wayland",
            "is_x11": session_type == "x11" or session_type == "xorg"
        }

    def get_package_managers(self) -> Dict[str, bool]:
        """Detects available native and universal package managers."""
        return {
            "apt": shutil.which("apt") is not None,
            "dnf": shutil.which("dnf") is not None,
            "pacman": shutil.which("pacman") is not None,
            "zypper": shutil.which("zypper") is not None,
            "flatpak": shutil.which("flatpak") is not None,
            "snap": shutil.which("snap") is not None,
            "nix": shutil.which("nix") is not None,
            "pip": shutil.which("pip3") is not None or shutil.which("pip") is not None,
            "cargo": shutil.which("cargo") is not None,
            "brew": shutil.which("brew") is not None
        }

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Detects installed graphics cards and active drivers."""
        gpus = []
        try:
            if shutil.which("lspci"):
                out = subprocess.check_output(["lspci", "-nnk"], stderr=subprocess.DEVNULL, timeout=3).decode()
                blocks = out.split("\n\n")
                for block in blocks:
                    if "VGA compatible controller" in block or "3D controller" in block or "Display controller" in block:
                        vendor = "Unknown"
                        driver = "None"

                        if "NVIDIA" in block or "10de:" in block:
                            vendor = "NVIDIA"
                        elif "AMD" in block or "Advanced Micro Devices" in block or "ATI" in block or "1002:" in block:
                            vendor = "AMD"
                        elif "Intel" in block or "8086:" in block:
                            vendor = "Intel"

                        match_drv = re.search(r"Kernel driver in use:\s*(\S+)", block)
                        if match_drv:
                            driver = match_drv.group(1)

                        first_line = block.strip().split("\n")[0]
                        desc = first_line.split(": ", 1)[-1] if ": " in first_line else first_line

                        gpus.append({
                            "vendor": vendor,
                            "description": desc,
                            "driver": driver,
                            "is_nvidia": vendor == "NVIDIA",
                            "is_amd": vendor == "AMD",
                            "is_intel": vendor == "Intel",
                            "is_proprietary_nvidia": driver == "nvidia",
                            "is_nouveau": driver == "nouveau"
                        })
        except Exception:
            pass

        if not gpus:
            gpus.append({
                "vendor": "Generic",
                "description": "Standard Display Adapter",
                "driver": "unknown",
                "is_nvidia": False,
                "is_amd": False,
                "is_intel": False,
                "is_proprietary_nvidia": False,
                "is_nouveau": False
            })

        return gpus

    def get_audio_subsystem(self) -> Dict[str, Any]:
        """Detects active sound server (PipeWire vs PulseAudio vs ALSA)."""
        has_pipewire = False
        has_wireplumber = False
        has_pulseaudio = False

        try:
            pids = subprocess.check_output(["ps", "-A"], stderr=subprocess.DEVNULL, timeout=2).decode()
            has_pipewire = "pipewire" in pids
            has_wireplumber = "wireplumber" in pids
            has_pulseaudio = "pulseaudio" in pids
        except Exception:
            pass

        primary = "ALSA"
        if has_pipewire:
            primary = "PipeWire"
        elif has_pulseaudio:
            primary = "PulseAudio"

        return {
            "primary": primary,
            "pipewire": has_pipewire,
            "wireplumber": has_wireplumber,
            "pulseaudio": has_pulseaudio
        }

    def get_full_summary(self) -> Dict[str, Any]:
        """Returns a consolidated system environment summary."""
        return {
            "distro": self.get_distro_info(),
            "desktop": self.get_desktop_environment(),
            "package_managers": self.get_package_managers(),
            "gpus": self.get_gpu_info(),
            "audio": self.get_audio_subsystem()
        }
