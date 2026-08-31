# 📖 LinForge Comprehensive User Manual & CLI Reference

LinForge is designed to be accessible to total beginners through its intuitive graphical interface while remaining a versatile tool for sysadmins and power users through its CLI and TUI modes.

---

## 1. Running Modes

### A. Desktop GUI Mode (Default)
When run from an active desktop session (KDE Plasma, GNOME, XFCE, Cinnamon, etc.), LinForge automatically launches the web-view GUI:
```bash
linforge
# or
linforge --gui
```
- **Port Selection**: By default, LinForge runs its embedded API server on port `8990`. To specify a different port:
  ```bash
  linforge --port 9500
  ```
- **Headless Server Mode**: Run the backend server without popping up a browser window:
  ```bash
  linforge --headless
  ```

### B. Interactive Terminal UI (TUI)
For remote SSH sessions, servers, or minimal window managers:
```bash
linforge --tui
```
- Fully navigable using numbers `1-8` and `0` to exit.
- Features multi-select for batch app installations (e.g. `1,3,7`).

### C. Direct Command-Line Actions (Automation & Scripts)
Automate setup scripts or integrate LinForge into custom provisioning workflows:

| Command | Action |
| :--- | :--- |
| `linforge --update-all` | Universal update for APT/DNF/Pacman + Flatpaks + Snaps + Firmware |
| `linforge --clean` | Full system deep clean (package cache, journal logs, Flatpak/Snap runtimes, SSD TRIM) |
| `linforge --gaming` | Apply recommended gaming tweaks (`vm.max_map_count`, swappiness 10, split-lock, BBR) |
| `linforge --fix-audio` | Reset and configure low-latency PipeWire / WirePlumber audio stack |
| `linforge --fix-packages` | Remove stale APT locks and repair broken dependencies |
| `linforge --info` | Output full system telemetry, CPU, RAM, GPU, audio server, and disks |

---

## 2. Module Explanations & Best Practices

### A. App Store & Multi-Source Engine
- **Source Selection**: LinForge automatically selects the optimal source for your distribution. On Kubuntu/Ubuntu, it prefers clean Native APT packages with modern deb822 keyrings or Flathub Flatpaks for sandboxed desktop software.
- **Batch Processing**: In the GUI, you can check multiple apps across different categories and click **Install (X) Selected** to install them all unattended.

### B. Driver Doctor
- **NVIDIA Proprietary Drivers**: Configures official PPA, installs recommended driver with 32-bit GL libraries for Steam, sets `modeset=1 fbdev=1` for smooth Wayland support, and configures systemd power management to eliminate wake-up black screens.
- **Mesa Fresh**: On Ubuntu/Kubuntu, upgrades Mesa to the Kisak-Mesa PPA for the latest Vulkan RADV drivers.
- **PipeWire Audio**: Fixes audio device auto-suspend popping sounds and sets 128 quantum low-latency buffer for pro audio and gaming.

### C. System Cleaner
- **Journal Vacuuming**: Restricts system logs to 100MB and 7 days retention.
- **Snap Revision Purge**: By default, Canonical Snap keeps 3 revisions of every installed snap. LinForge purges old disabled revisions and limits future retention to 2 revisions, saving 10–30 GB on typical systems.
- **SSD TRIM**: Triggers `fstrim -av` to inform the SSD controller about freed blocks, prolonging SSD lifespan and write speeds.

### D. Emergency Troubleshooter
- **APT Lock Fixer**: Removes `/var/lib/dpkg/lock-frontend` and kills stale background apt processes that prevent you from installing new packages.
- **DNS Resolver Doctor**: Flushes caches and fixes broken `/etc/resolv.conf` symlinks.
- **Permissions Fixer**: Restores user ownership over `~/.config`, `~/.cache`, and `~/.local` if you accidentally ran commands with `sudo`.

---

## 3. Extending LinForge with Custom Apps & Tweaks

### Adding a New Application
Open `src/data/apps.json` and append a new JSON object:
```json
{
  "id": "my-new-app",
  "name": "My New App",
  "category": "utilities",
  "description": "Awesome new Linux tool.",
  "icon": "box",
  "sources": {
    "native_deb": "my-new-app-pkg",
    "flatpak": "com.example.MyApp"
  },
  "default_source": "flatpak"
}
```

### Adding a New Tweak
Open `src/data/tweaks.json` and append:
```json
{
  "id": "tweak_custom_example",
  "name": "Custom Performance Parameter",
  "category": "gaming",
  "description": "Configures custom sysctl parameter.",
  "risk": "safe",
  "apply_script": "echo 'custom.param=1' > /etc/sysctl.d/99-custom.conf && sysctl --system",
  "revert_script": "rm -f /etc/sysctl.d/99-custom.conf && sysctl --system"
}
```
