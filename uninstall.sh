#!/usr/bin/env bash
# ==============================================================================
# LinForge - Clean Uninstaller Script
# Removes LinForge binaries, desktop menu entries, icons, and share data.
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}Uninstalling LinForge from system...${NC}"

TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$TARGET_USER" 2>/dev/null | cut -d: -f6 || echo "")
if [ -z "$TARGET_HOME" ] || [ ! -d "$TARGET_HOME" ]; then
    TARGET_HOME="$HOME"
fi

# 1. Remove binary and share directory
rm -f "$TARGET_HOME/.local/bin/linforge"
rm -rf "$TARGET_HOME/.local/share/linforge"

# 2. Remove desktop shortcut and icon
rm -f "$TARGET_HOME/.local/share/applications/linforge.desktop"
rm -f "$TARGET_HOME/.local/share/icons/hicolor/scalable/apps/linforge.svg"

# 3. Update desktop database
update-desktop-database "$TARGET_HOME/.local/share/applications" 2>/dev/null || true

echo -e "${GREEN}${BOLD}✓ LinForge has been completely removed.${NC}\n"
