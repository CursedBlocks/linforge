#!/usr/bin/env bash
# ==============================================================================
# LinForge - Universal 1-Command Bootstrap & Installer
# Launch via: curl -fsSL https://raw.githubusercontent.com/<USER>/<REPO>/main/install.sh | bash
# ==============================================================================
set -euo pipefail

# ANSI Color Codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "  ██╗     ██╗███╗   ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗"
echo "  ██║     ██║████╗  ██║██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝"
echo "  ██║     ██║██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  "
echo "  ██║     ██║██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  "
echo "  ███████╗██║██║ ╚████║██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗"
echo "  ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
echo -e "${NC}"
echo -e "${BOLD}LinForge - The Ultimate Linux Setup & Maintenance Suite${NC}"
echo -e "Starting automated installation & environment check...\n"

# 1. Attach TTY if executed via piped curl/wget
if [ ! -t 0 ]; then
    if [ -e /dev/tty ]; then
        exec < /dev/tty
    fi
fi

# 2. Prevent running entirely as root
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${RED}[ERROR]${NC} Please do not run the installer as root (sudo bash install.sh)."
    echo "LinForge will prompt for sudo credentials only when required."
    exit 1
fi

# 3. Detect Distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID="${ID:-linux}"
    DISTRO_NAME="${PRETTY_NAME:-$DISTRO_ID}"
else
    DISTRO_ID="linux"
    DISTRO_NAME="Linux"
fi

echo -e "${GREEN}[✓]${NC} Detected System: ${BOLD}${DISTRO_NAME}${NC} ($(uname -m))"

# 4. Check for Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}[!]${NC} Python 3 is required. Installing..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-pip git
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip git
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm python python-pip git
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3 python3-pip git
    fi
fi

INSTALL_DIR="$HOME/.local/share/linforge"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICONS_DIR"

# 5. Copy or Fetch codebase
SCRIPT_SRC_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
fi

if [ -n "$SCRIPT_SRC_DIR" ] && [ -f "$SCRIPT_SRC_DIR/src/linforge.py" ]; then
    echo -e "${GREEN}[✓]${NC} Installing LinForge from local repository..."
    cp -r "$SCRIPT_SRC_DIR/src" "$INSTALL_DIR/"
    cp -r "$SCRIPT_SRC_DIR/assets" "$INSTALL_DIR/" 2>/dev/null || true
else
    echo -e "${GREEN}[✓]${NC} Fetching latest LinForge release..."
    TMP_DIR=$(mktemp -d)
    CLONED=0

    if command -v git >/dev/null 2>&1; then
        if git clone --depth 1 https://github.com/maddox-h/linforge.git "$TMP_DIR" 2>/dev/null; then
            CLONED=1
        fi
    fi

    if [ $CLONED -eq 0 ]; then
        echo -e "${YELLOW}[!]${NC} Git unavailable or clone failed, extracting tarball..."
        curl -fsSL https://github.com/maddox-h/linforge/archive/refs/heads/main.tar.gz | tar -xz -C "$TMP_DIR" --strip-components=1 2>/dev/null || true
    fi

    if [ -d "$TMP_DIR/src" ]; then
        cp -r "$TMP_DIR/src" "$INSTALL_DIR/"
        cp -r "$TMP_DIR/assets" "$INSTALL_DIR/" 2>/dev/null || true
    fi
    rm -rf "$TMP_DIR"
fi

# 6. Install CLI Launcher script
cat << 'EOF' > "$BIN_DIR/linforge"
#!/usr/bin/env bash
python3 "$HOME/.local/share/linforge/src/linforge.py" "$@"
EOF
chmod +x "$BIN_DIR/linforge"

# Add ~/.local/bin to PATH if missing in current environment
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
    if [ -f "$HOME/.bashrc" ] && ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    if [ -f "$HOME/.zshrc" ] && ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
fi

# 7. Install Icon & Desktop Launcher Entry
if [ -f "$INSTALL_DIR/assets/linforge.svg" ]; then
    cp "$INSTALL_DIR/assets/linforge.svg" "$ICONS_DIR/linforge.svg"
fi

cat << EOF > "$DESKTOP_DIR/linforge.desktop"
[Desktop Entry]
Name=LinForge
Comment=The Ultimate Linux Setup, Optimization & Maintenance Suite
Exec=$BIN_DIR/linforge --gui
Icon=linforge
Terminal=false
Type=Application
Categories=System;Settings;Utility;
Keywords=linutil;winutil;setup;tweaks;drivers;cleanup;troubleshoot;gaming;
EOF
chmod +x "$DESKTOP_DIR/linforge.desktop"

# Refresh desktop database
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo -e "\n${GREEN}${BOLD}🎉 LinForge installed successfully!${NC}"
echo -e "• Launch anytime from your Application Menu or by typing: ${CYAN}linforge${NC}"
echo -e "• Starting LinForge now...\n"

# 8. Launch immediately
python3 "$INSTALL_DIR/src/linforge.py" "$@"
