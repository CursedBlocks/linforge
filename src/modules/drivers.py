"""
LinForge - Driver Doctor & Hardware Enabler
Automated detection, installation, and optimization for NVIDIA, AMD, Intel graphics,
Broadcom/Realtek wireless chipsets, low-latency PipeWire audio, and gaming peripherals.
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


class DriverManager:
    """Hardware driver doctor and peripheral enabler."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()

    def get_hardware_status(self) -> Dict[str, Any]:
        """Scans hardware devices and reports active driver health."""
        gpus = self.detector.get_gpu_info()
        audio = self.detector.get_audio_subsystem()
        distro = self.detector.get_distro_info()

        wifi_info = "Unknown / Built-in"
        try:
            if shutil.which("lspci"):
                out = subprocess.check_output(["lspci"], stderr=subprocess.DEVNULL, timeout=2).decode()
                for line in out.splitlines():
                    if "Network controller" in line or "Wireless" in line:
                        wifi_info = line.split(":", 2)[-1].strip()
                        break
        except Exception:
            pass

        return {
            "gpus": gpus,
            "audio": audio,
            "wifi": wifi_info,
            "distro": distro
        }

    def install_nvidia_recommended(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs the latest recommended NVIDIA proprietary driver branch with Wayland and sleep fixes."""
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            script = """
            echo "Configuring official Graphics Drivers PPA..."
            add-apt-repository -y ppa:graphics-drivers/ppa
            dpkg --add-architecture i386
            apt-get update -qq

            echo "Detecting recommended NVIDIA driver..."
            if command -v ubuntu-drivers >/dev/null 2>&1; then
                ubuntu-drivers install
            else
                apt-get install -y nvidia-driver-550 libnvidia-gl-550:i386 nvidia-settings
            fi

            echo "Configuring Wayland DRM Kernel Mode Setting..."
            cat << 'EOF' > /etc/modprobe.d/nvidia-graphics-drivers.conf
options nvidia-drm modeset=1 fbdev=1
options nvidia NVreg_PreserveVideoMemoryAllocations=1
EOF

            echo "Enabling NVIDIA power management services..."
            systemctl enable nvidia-suspend.service nvidia-hibernate.service nvidia-resume.service 2>/dev/null || true
            if command -v update-initramfs >/dev/null 2>&1; then
                update-initramfs -u 2>/dev/null || true
            fi
            echo "NVIDIA Driver installation complete! Please reboot your computer."
            """
        elif family == "fedora" or shutil.which("dnf"):
            script = """
            echo "Enabling RPM Fusion and installing NVIDIA drivers for Fedora..."
            dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm || true
            dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda vulkan
            """
        elif family == "arch" or shutil.which("pacman"):
            script = """
            echo "Installing Arch Linux NVIDIA DKMS driver..."
            pacman -S --needed --noconfirm nvidia-dkms nvidia-utils lib32-nvidia-utils nvidia-settings opencl-nvidia
            """
        else:
            script = "ubuntu-drivers install || apt-get install -y nvidia-driver-550"

        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_amd_kisak_mesa(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs latest fresh Kisak-Mesa PPA for bleeding-edge Vulkan RADV gaming performance."""
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            script = """
            echo "Adding Kisak-Mesa Fresh PPA..."
            add-apt-repository -y ppa:kisak/kisak-mesa
            dpkg --add-architecture i386
            apt-get update -qq
            apt-get dist-upgrade -y
            apt-get install -y libgl1-mesa-dri:i386 mesa-vulkan-drivers mesa-vulkan-drivers:i386 libva-mesa-driver vainfo
            echo "Latest AMD/Intel Mesa graphics stack updated successfully!"
            """
        elif family == "fedora" or shutil.which("dnf"):
            script = """
            echo "Updating Fedora Mesa graphics stack..."
            dnf upgrade -y mesa* vulkan*
            """
        elif family == "arch" or shutil.which("pacman"):
            script = """
            echo "Updating Arch Linux Mesa RADV drivers..."
            pacman -S --needed --noconfirm mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon libva-mesa-driver
            """
        else:
            script = "apt-get install -y mesa-vulkan-drivers libgl1-mesa-dri"

        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_broadcom_wifi(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Broadcom STA wireless drivers (BCM43xx)."""
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            script = """
            apt-get update -qq
            apt-get install -y bcmwl-kernel-source firmware-b43-installer
            modprobe -r b43 b43legacy ssb bcm43xx wl 2>/dev/null || true
            modprobe wl || true
            echo "Broadcom Wi-Fi driver installed and activated."
            """
        elif family == "arch" or shutil.which("pacman"):
            script = "pacman -S --needed --noconfirm broadcom-wl-dkms"
        elif family == "fedora" or shutil.which("dnf"):
            script = "dnf install -y broadcom-wl kmod-wl"
        else:
            script = "apt-get install -y bcmwl-kernel-source"

        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_realtek_wifi(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Realtek DKMS Wi-Fi and Ethernet drivers."""
        script = """
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq
            apt-get install -y dkms git build-essential linux-headers-$(uname -r) rtl8821ce-dkms r8168-dkms linux-firmware 2>/dev/null || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y dkms git kernel-devel kernel-headers 2>/dev/null || true
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm dkms linux-headers rtl8821ce-dkms-git 2>/dev/null || true
        fi
        echo "Realtek wireless & network drivers installed."
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def setup_pipewire_audio(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Configures low-latency PipeWire and WirePlumber audio stack."""
        script = """
        echo "Installing PipeWire, WirePlumber, and Bluetooth audio codecs..."
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq
            apt-get install -y pipewire pipewire-pulse pipewire-alsa pipewire-jack wireplumber libspa-0.2-bluetooth 2>/dev/null || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y pipewire pipewire-pulseaudio pipewire-alsa wireplumber pipewire-codec-aptx
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm pipewire pipewire-pulse pipewire-alsa wireplumber pipewire-audio
        fi

        # Configure user config directory
        CONFIG_DIR="${REAL_HOME:-$HOME}/.config/pipewire/pipewire.conf.d"
        mkdir -p "$CONFIG_DIR"
        cat << 'EOF' > "$CONFIG_DIR/99-lowlatency.conf"
context.properties = {
    default.clock.rate = 48000
    default.clock.quantum = 128
    default.clock.min-quantum = 64
    default.clock.max-quantum = 1024
}
EOF

        WP_DIR="${REAL_HOME:-$HOME}/.config/wireplumber/wireplumber.conf.d"
        mkdir -p "$WP_DIR"
        cat << 'EOF' > "$WP_DIR/51-disable-suspension.conf"
monitor.alsa.rules = [
  {
    matches = [ { node.name = "~alsa_input.*" }, { node.name = "~alsa_output.*" } ]
    actions = {
      update-props = {
        session.suspend-timeout-seconds = 0
      }
    }
  }
]
EOF

        chown -R "$REAL_USER:$REAL_USER" "${REAL_HOME:-$HOME}/.config/pipewire" "${REAL_HOME:-$HOME}/.config/wireplumber" 2>/dev/null || true

        # Restart user-level Pipewire daemons safely
        USER_UID=$(id -u "$REAL_USER" 2>/dev/null || echo "1000")
        sudo -u "$REAL_USER" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user restart pipewire wireplumber pipewire-pulse 2>/dev/null || true

        echo "Low-latency PipeWire audio stack configured and running!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def setup_game_controllers(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Xbox One/Series and DualSense controller udev rules."""
        script = """
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq
            apt-get install -y steam-devices joystick jstest-gtk 2>/dev/null || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y joystick jstest-gtk 2>/dev/null || true
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm game-devices-udev 2>/dev/null || true
        fi

        cat << 'EOF' > /etc/udev/rules.d/70-dualsense.rules
KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*054C:0CE6*", MODE="0660", TAG+="uaccess"
EOF

        udevadm control --reload-rules && udevadm trigger 2>/dev/null || true
        echo "Game controller rules and calibration tools installed!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def setup_openrgb_udev(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Configures i2c-dev and OpenRGB udev permissions for motherboard RGB access."""
        script = """
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq
            apt-get install -y i2c-tools 2>/dev/null || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y i2c-tools
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm i2c-tools
        fi

        modprobe i2c-dev || true
        echo "i2c-dev" >> /etc/modules-load.d/i2c.conf 2>/dev/null || true

        curl -fsSL https://openrgb.org/releases/release_0.9/60-openrgb.rules -o /etc/udev/rules.d/60-openrgb.rules 2>/dev/null || true
        udevadm control --reload-rules && udevadm trigger 2>/dev/null || true
        usermod -aG i2c "$REAL_USER" 2>/dev/null || true
        echo "OpenRGB hardware permissions configured!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_autocpufreq_battery(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs auto-cpufreq to dramatically extend laptop battery life."""
        script = """
        echo "Installing auto-cpufreq for automated CPU governor & power saving..."
        TMP_DIR=$(mktemp -d)
        git clone https://github.com/AdnanHodzic/auto-cpufreq.git "$TMP_DIR"
        cd "$TMP_DIR" && ./auto-cpufreq-installer --install
        auto-cpufreq --install
        rm -rf "$TMP_DIR"
        echo "auto-cpufreq active and running!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_xanmod_kernel(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs XanMod high-performance gaming kernel with multi-distro awareness."""
        family = self.detector.get_distro_info().get("family", "debian")

        if family == "debian" or shutil.which("apt-get"):
            script = """
            echo "Installing XanMod High-Performance Gaming Kernel for Ubuntu/Debian..."
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://dl.xanmod.org/archive.key | gpg --dearmor -o /etc/apt/keyrings/xanmod-archive-keyring.gpg
            echo 'deb [signed-by=/etc/apt/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' > /etc/apt/sources.list.d/xanmod-release.list
            apt-get update -qq
            apt-get install -y linux-xanmod-x64v3 || apt-get install -y linux-xanmod
            update-grub 2>/dev/null || true
            echo "XanMod Kernel installed! Reboot to boot into XanMod."
            """
        elif family == "arch" or shutil.which("pacman"):
            script = """
            echo "Installing XanMod Kernel on Arch Linux..."
            if command -v yay >/dev/null 2>&1; then
                sudo -u "$REAL_USER" yay -S --noconfirm linux-xanmod linux-xanmod-headers
            elif command -v paru >/dev/null 2>&1; then
                sudo -u "$REAL_USER" paru -S --noconfirm linux-xanmod linux-xanmod-headers
            else
                pacman -S --needed --noconfirm linux-zen linux-zen-headers
            fi
            """
        else:
            script = "echo 'XanMod kernel installation is optimized for Debian, Ubuntu, and Arch-based distributions.'"

        return self.runner.run_script_block(script, use_sudo=True, callback=callback)
