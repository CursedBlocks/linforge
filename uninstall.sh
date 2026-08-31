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

# 1. Remove binary and share directory
rm -f "$HOME/.local/bin/linforge"
rm -rf "$HOME/.local/share/linforge"

# 2. Remove desktop shortcut and icon
rm -f "$HOME/.local/share/applications/linforge.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/linforge.svg"

# 3. Update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo -e "${GREEN}${BOLD}✓ LinForge has been completely removed.${NC}\n"
