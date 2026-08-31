# ⚡ LinForge
### *The Ultimate Linux Setup, Optimization, Hardware Doctor & Maintenance Suite*
#### *Inspired by Chris Titus Tech's WinUtil — Re-engineered & Supercharged for Kubuntu, Ubuntu & Beyond.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux%20%7C%20Kubuntu%20%7C%20Ubuntu-orange.svg)]()
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-cyan.svg)]()
[![Desktop: KDE Plasma & GNOME](https://img.shields.io/badge/Desktop-KDE%20Plasma%20%7C%20GNOME-purple.svg)]()
[![One-Liner Launch](https://img.shields.io/badge/Launch-1--Command%20Curl-success.svg)]()

```
  ██╗     ██╗███╗   ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
  ██║     ██║████╗  ██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ██║     ██║██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
  ██║     ██║██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
  ███████╗██║██║ ╚████║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
  ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

---

## 🌟 Why LinForge?

Switching to Linux or setting up a fresh install of **Kubuntu or Ubuntu** should be an exhilarating experience — not a weekend spent hunting down broken Wi-Fi DKMS drivers, dealing with random PipeWire audio popping, wrestling with APT lock errors, or manually running dozens of terminal commands just to get Steam, Discord, and VS Code running properly.

**LinForge is the all-in-one companion app Linux has been missing.** 

Think of it as **Chris Titus Tech’s WinUtil for Linux**, but taken much further. With a single terminal command, LinForge launches a **stunning, modern glassmorphic graphical interface** (or an interactive terminal TUI in headless/SSH mode) that does all the heavy lifting automatically:

- 🪄 **1-Click System Presets**: Transform a fresh install with curated profiles (*Ultimate Gaming Rig*, *AI & Developer Workstation*, *Minimalist & Privacy Debloat*, *Content Creator Studio*).
- 🎨 **5 Bespoke Glassmorphic Themes**: Switch on the fly between *Cyber Neon*, *Plasma KDE Indigo*, *Midnight Dark*, *Ubuntu Warmth*, and *Emerald Matrix*.
- 📦 **1-Click App Store**: Bulk install 100+ curated native, Flatpak, and official vendor applications with a rich App Detail modal and source switcher.
- 🚀 **Gaming & Low-Latency Engine**: Maximize FPS, install XanMod gaming kernel, deploy GE-Proton, configure GameMode, and apply critical kernel memory map tweaks (`vm.max_map_count=2147483642`, swappiness 10, ZRAM).
- 🔧 **Driver Doctor**: 1-click NVIDIA proprietary driver installs with Wayland KMS fixes, AMD/Intel Mesa fresh upgrades, Broadcom/Realtek Wi-Fi fixes, and controller setup.
- 🧹 **Deep System Cleaner**: Vacuum journal logs, remove orphaned packages, purge old disabled Snap revisions, prune unused Flatpak runtimes, and trigger SSD TRIM.
- 🛠️ **Emergency Troubleshooter**: Automatically diagnose and repair package database locks, fix DNS dropouts, restart audio servers, and recover home directory permissions.
- 💻 **Developer Studio**: 1-click stacks for Web (Node/Bun/Deno/pnpm), Python AI (Astral `uv` & Ollama LLM), Systems (Rustup & C/C++), DevOps (Docker CE Engine & Kubernetes), and Starship prompt terminal supercharging.
- 🔄 **Universal Maintenance**: Update APT/DNF/Pacman + Flatpaks + Snaps + Hardware Firmware (LVFS) in one single coordinated operation, plus instant Timeshift restore points.
- 💻 **Live Terminal Console Drawer**: Real-time log streaming with tab filters (All, Stdout, Stderr, System), search, fullscreen expand, and instant clipboard copy.

---

## 🚀 Quick Start (One-Command Launch)

Open your Linux terminal and paste this single command:

```bash
curl -fsSL https://raw.githubusercontent.com/maddox-h/linforge/main/install.sh | bash
```

*Or with `wget`:*
```bash
wget -qO- https://raw.githubusercontent.com/maddox-h/linforge/main/install.sh | bash
```

### What Happens When You Run This?
1. LinForge automatically detects your Linux distribution, desktop environment, and hardware architecture.
2. Checks for Python 3 and prepares the environment in seconds.
3. Installs the `linforge` CLI command and creates a desktop shortcut in your Application Menu (KDE Kickoff / GNOME Activities).
4. Immediately pops open the sleek desktop GUI window!

---

## 📊 LinForge vs Other Tools

| Feature | LinForge | Chris Titus Linutil | Chris Titus WinUtil | Standard Linux Setup Scripts |
| :--- | :---: | :---: | :---: | :---: |
| **Primary Platform** | **Linux (Kubuntu/Ubuntu/All)** | Linux (General) | Windows Only | Linux |
| **UI Experience** | **5-Theme Glassmorphic GUI + TUI** | TUI (Ratatui) | WPF (PowerShell GUI) | Raw Bash text |
| **1-Click System Presets** | ✅ Gaming, Dev, Debloat, Creator | ❌ No | ⚠️ Basic WP | ❌ No |
| **One-Command Web Launch** | ✅ Yes (`curl \| bash`) | ✅ Yes | ✅ Yes (`irm \| iex`) | ⚠️ Varies |
| **Live Telemetry & Sparklines** | ✅ Real-time Chart.js Charts | ❌ No | ❌ No | ❌ No |
| **1-Click Curated App Store** | ✅ 100+ Native, Flatpak, Snap | ✅ Basic selection | ✅ WinGet Catalog | ⚠️ Minimal |
| **Automated Driver Doctor** | ✅ NVIDIA, AMD, Wi-Fi, Audio | ⚠️ Partial | ❌ No | ❌ No |
| **Automated Diagnostic & Repair** | ✅ APT locks, DNS, Audio, Perms | ❌ No | ⚠️ Windows repairs | ❌ No |
| **XanMod Kernel & GE-Proton** | ✅ 1-Click Complete | ⚠️ Manual steps | ⚠️ Windows tweaks | ❌ No |
| **KDE Plasma & Kubuntu Tuning** | ✅ Deep Baloo & KWin tweaks | ❌ Generic | ❌ N/A | ❌ No |
| **Developer Stacks (uv/Ollama)** | ✅ Web, AI, Rust, DevOps | ⚠️ Basic tools | ⚠️ Basic tools | ❌ No |
| **Snap & Flatpak Cleaner** | ✅ Automatic revision purge | ❌ No | ❌ N/A | ❌ No |
| **Timeshift Snapshot Safety** | ✅ Integrated restore points | ❌ No | ⚠️ System Restore | ❌ No |

---

## 🖥️ Feature Walkthrough

### 1. 🪄 1-Click System Transformation Presets
- **Ultimate Gaming Rig**: Automatically deploys Steam, Heroic, Lutris, ProtonUp-Qt, MangoHud, GameMode, Discord, OBS Studio, tunes kernel memory maps (`vm.max_map_count=2147483642`), swappiness 10, split-lock mitigation, and game controller udev rules.
- **AI & Developer Workstation**: Installs VS Code, Docker Engine, Postman, DBeaver, GitKraken, fastfetch, btop, and provisions complete Node.js/Bun/Deno, Astral `uv` Python/AI, Rustup, and Starship terminal stacks.
- **Minimalist & Privacy Debloat**: Strips Ubuntu crash report daemons (Apport/Whoopsie), silences ESM promotion terminal notices, enables Cloudflare/Quad9 DNS-over-TLS, configures UFW firewall, purges old Snap revisions, and installs LibreWolf & Bitwarden.
- **Content Creator Studio**: Sets up OBS Studio with NVENC/VA-API hardware acceleration, Blender 3D, Kdenlive, GIMP, Inkscape, Krita, Audacity, HandBrake, VLC, and configures low-latency PipeWire 128 quantum audio.

### 2. 📊 Real-Time Telemetry & Live Charts
- Real-time Chart.js interactive sparklines tracking CPU and RAM utilization over time.
- Live CPU percentage gauge, per-core load, clock frequencies, and core temperatures across all motherboard sensor drivers.
- RAM & Swap breakdown with live swappiness indicators.
- Partition storage bars with filesystem detection (Btrfs, Ext4, XFS, ZFS) and free space alerts.
- Live network throughput meters (KB/s down/up).

### 3. 📦 Curated One-Click App Store with App Detail Modal
Browse through 100+ categorized, tested Linux applications:
- **Web Browsers**: Google Chrome, Brave, Firefox (Native Deb PPA / Flatpak), Microsoft Edge, LibreWolf, Tor Browser, Vivaldi.
- **Development**: VS Code (Official repo), VSCodium, Cursor AI, JetBrains Toolbox, Docker CE, Postman, DBeaver, Neovim, GitKraken.
- **Gaming & Emulation**: Steam (32-bit Vulkan ready), Heroic Games Launcher, Lutris, Bottles, ProtonUp-Qt, MangoHud & Goverlay, GameMode, Prism Launcher, RetroArch, RPCS3, PCSX2, Dolphin.
- **Media & Creation**: OBS Studio, Blender, Kdenlive, GIMP, Inkscape, Krita, Audacity, HandBrake, VLC, Spotify.
- **Productivity & Office**: LibreOffice Fresh, ONLYOFFICE, Obsidian, Thunderbird, Discord, Vesktop, Telegram, Signal, Bitwarden, KeePassXC.
- **System Utilities**: Timeshift, GParted, Mission Center, Fastfetch, btop, Flatseal, Warehouse, OpenRGB, RustDesk, BleachBit.

### 4. ⚡ Gaming, Kernel & Performance Turbo
- **XanMod Kernel**: Install high-performance XanMod kernel optimized for real-time low-latency desktop gaming.
- **Kernel Sysctl Tuning**: `vm.max_map_count=2147483642` and `vm.swappiness=10`.
- **High-Speed ZRAM**: Enables Zstandard compressed RAM swap, boosting effective memory capacity.
- **GE-Proton Management**: Automatically pulls and unpacks latest GloriousEggroll Proton builds.
- **KDE Plasma Supercharging**: 2x faster KWin animations and Baloo file indexer exclusions.

### 5. 🔧 Driver Doctor & Hardware Enabler
- **NVIDIA Proprietary Drivers**: Detects GPU generation, configures Graphics Drivers PPA, installs recommended proprietary drivers, sets up 32-bit GL libraries, enables DRM Kernel Mode Setting (`modeset=1 fbdev=1`), and enables sleep/resume daemons.
- **AMD Radeon & Intel Graphics**: Upgrades to the Kisak-Mesa fresh PPA for fast Vulkan RADV gaming drivers.
- **Wireless & Wi-Fi**: 1-click Broadcom BCM43xx STA drivers and Realtek DKMS wireless drivers.
- **PipeWire Audio Stack**: Seamlessly configures 128-quantum low-latency audio.
- **Game Controllers & RGB**: Sets up Sony DualSense, Xbox One wireless dongles, and OpenRGB permissions.

---

## ⌨️ Command Line (CLI) & Headless TUI Mode

LinForge can be operated entirely from the terminal on remote servers, SSH connections, or by power users:

```bash
# Launch interactive Terminal UI (TUI)
linforge --tui

# Apply a 1-click system preset profile
linforge --preset preset_gaming
linforge --preset preset_developer
linforge --preset preset_debloat_privacy
linforge --preset preset_creator

# Run 1-Click Universal System Update
linforge --update-all

# Run Deep System Cleanup
linforge --clean

# Apply recommended gaming & performance tweaks
linforge --gaming

# Reset & repair PipeWire audio stack
linforge --fix-audio

# Unlock APT and repair broken package database
linforge --fix-packages

# Print comprehensive system specs and telemetry
linforge --info
```

---

## 🛠️ Supported Linux Distributions

LinForge is engineered with deep first-class optimizations for **Kubuntu and Ubuntu**, while providing seamless multi-distro package and driver abstraction for:

- 🟢 **Kubuntu / Ubuntu** (24.04 LTS, 24.10, 22.04 LTS, and all official flavors)
- 🟢 **Pop!_OS** & **Linux Mint**
- 🟢 **Debian** (12 Bookworm, Testing, Sid)
- 🟢 **KDE neon** & **TUXEDO OS**
- 🟢 **Fedora** & **Nobara Linux**
- 🟢 **Arch Linux**, **Manjaro**, **EndeavourOS**, **CachyOS**
- 🟢 **openSUSE** (Tumbleweed & Leap)

---

## 📁 Repository Structure

```
LinForge/
├── install.sh                  # One-line curl/wget bootstrap & launcher script
├── uninstall.sh                # Clean uninstaller script
├── linforge                    # Root executable wrapper
├── linforge.desktop            # Freedesktop application entry
├── assets/
│   └── linforge.svg            # Official vector icon
├── src/
│   ├── linforge.py             # Master CLI dispatcher & main entrypoint
│   ├── core/
│   │   ├── detector.py         # Hardware, Distro, DE, Kernel & GPU detection
│   │   ├── system_info.py      # Real-time hardware telemetry (CPU, RAM, Disks, Network)
│   │   ├── runner.py           # Async command executor with live streaming & pkexec/sudo
│   │   └── package_manager.py  # Universal package abstraction (APT, DNF, Pacman, Flatpak)
│   ├── modules/
│   │   ├── presets.py          # 1-Click full system profile orchestrator
│   │   ├── apps.py             # Curated app store & batch installer
│   │   ├── drivers.py          # NVIDIA, AMD/Intel Mesa, Wi-Fi, PipeWire audio doctor
│   │   ├── tweaks.py           # Performance, gaming, ZRAM, KDE Plasma & privacy tweaks
│   │   ├── cleanup.py          # System cleaner, journal vacuum, Snap/Flatpak pruner
│   │   ├── troubleshoot.py     # Diagnostic checks & 1-click emergency repairs
│   │   ├── developer.py        # 1-click dev stacks & Starship terminal supercharger
│   │   └── maintenance.py      # Universal updater, Timeshift snapshots, kernel cleaner
│   ├── ui/
│   │   ├── server.py           # Embedded lightweight HTTP server with SSE log streaming
│   │   ├── webview_launcher.py # Desktop window launcher (pywebview / Chrome app mode)
│   │   ├── tui.py              # Interactive ANSI Terminal UI with Presets menu
│   │   └── web/                # Glassmorphic dark frontend (HTML5, CSS3, JS, Lucide)
│   └── data/
│       ├── presets.json        # Curated 1-click system presets catalog
│       ├── apps.json           # Catalog metadata for 100+ applications
│       ├── tweaks.json         # Performance & desktop tweaks definitions
│       └── fixes.json          # Automated diagnostic & repair routines
├── tests/                      # Automated unit test suite (26 comprehensive tests)
└── docs/
    ├── SETUP_AND_UPLOAD_GUIDE.md # Step-by-step GitHub publishing & hosting guide
    └── MANUAL.md               # Complete power-user manual
```

---

## 🤝 Contributing

Contributions, new application suggestions, driver fixes, and tweaks are welcome!
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/awesome-tweak`).
3. Commit your changes (`git commit -m 'Add awesome gaming tweak'`).
4. Run tests: `python3 -m unittest discover -s tests -p "test_*.py"`.
5. Push to your branch and open a Pull Request.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.
Built with ❤️ for the Linux and Kubuntu community.
