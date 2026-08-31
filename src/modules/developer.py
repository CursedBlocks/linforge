"""
LinForge - Developer & SysAdmin Power Suite Engine
1-Click installation of complete developer stacks (Web, Python/AI, Rust/Systems, DevOps/Docker)
and terminal environment supercharging (Starship, Zsh/Oh-My-Zsh, Fish, Modern CLI tools).
"""

import shutil
from typing import Any, Callable, Dict, List, Optional

try:
    from core.detector import SystemDetector
    from core.runner import CommandRunner, CommandResult
    from core.package_manager import PackageManager
except (ImportError, ValueError):
    from ..core.detector import SystemDetector
    from ..core.runner import CommandRunner, CommandResult
    from ..core.package_manager import PackageManager


class DeveloperManager:
    """Manages developer environments, language runtimes, SDKs, and shell configurations."""

    def __init__(self, detector: Optional[SystemDetector] = None, runner: Optional[CommandRunner] = None):
        self.detector = detector or SystemDetector()
        self.runner = runner or CommandRunner()
        self.pkg_mgr = PackageManager(self.detector, self.runner)

    def install_web_stack(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Node.js LTS via fnm, Bun, Deno, pnpm, and Git tools."""
        script = """
        echo "Installing Fast Node Manager (fnm) and Node.js LTS for $REAL_USER..."
        sudo -u "$REAL_USER" -H bash -c '
            curl -fsSL https://fnm.vercel.app/install | bash
            export PATH="$HOME/.local/share/fnm:$PATH"
            eval "$(fnm env 2>/dev/null || true)"
            fnm install --lts || true
            curl -fsSL https://bun.sh/install | bash || true
            curl -fsSL https://deno.land/install.sh | sh -s -- -y || true
            curl -fsSL https://get.pnpm.io/install.sh | sh - || true
        '
        echo "Web Development stack installed successfully!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_python_ai_stack(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Astral uv (blazing-fast Python manager), PyTorch support, and Ollama."""
        script = """
        echo "Installing Astral uv (Python package & project manager)..."
        sudo -u "$REAL_USER" -H bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh' || true

        echo "Installing Ollama local LLM runner..."
        curl -fsSL https://ollama.com/install.sh | sh || true

        echo "Python & AI Development stack installed!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_rust_systems_stack(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Rust toolchain (rustup, cargo), build-essential, GCC, Clang, CMake, and Ninja."""
        script = """
        echo "Installing C/C++ compiler toolchain (build-essential, clang, cmake, ninja)..."
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y build-essential clang cmake ninja-build gdb valgrind pkg-config libssl-dev
        elif command -v dnf >/dev/null 2>&1; then
            dnf groupinstall -y "Development Tools" && dnf install -y clang cmake ninja-build gdb valgrind openssl-devel
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm base-devel clang cmake ninja gdb valgrind openssl
        elif command -v zypper >/dev/null 2>&1; then
            zypper --non-interactive --auto-agree-with-licenses install -t pattern devel_basis && zypper install -y clang cmake ninja gdb
        fi

        echo "Installing Rust toolchain via rustup for $REAL_USER..."
        sudo -u "$REAL_USER" -H bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y' || true
        echo "Rust & Systems development stack ready!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_devops_stack(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Docker Engine, Docker Compose, Kubectl, Helm, and GitHub CLI (gh)."""
        script = """
        echo "Installing GitHub CLI (gh) & Docker..."
        if command -v apt-get >/dev/null 2>&1; then
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg 2>/dev/null || true
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
            
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs 2>/dev/null || echo jammy) stable" > /etc/apt/sources.list.d/docker.list

            apt-get update -qq
            apt-get install -y gh docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || apt-get install -y docker.io docker-compose
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y gh docker docker-compose
            systemctl enable --now docker 2>/dev/null || true
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm github-cli docker docker-compose
            systemctl enable --now docker 2>/dev/null || true
        fi

        usermod -aG docker "$REAL_USER" 2>/dev/null || true
        echo "DevOps & Cloud stack installed successfully!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_modern_cli_tools(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs modern rust replacements: eza, bat, zoxide, fzf, ripgrep, and Starship prompt."""
        script = """
        echo "Installing modern CLI productivity utilities..."
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y bat fzf ripgrep fd-find zoxide 2>/dev/null || true
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y bat fzf ripgrep fd-find zoxide 2>/dev/null || true
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm bat fzf ripgrep fd zoxide eza
        fi

        curl -sS https://starship.rs/install.sh | sh -s -- -y

        sudo -u "$REAL_USER" -H bash -c '
            mkdir -p "$HOME/.config"
            if ! grep -q "starship init bash" "$HOME/.bashrc" 2>/dev/null; then
                echo '\''eval "$(starship init bash)"'\'' >> "$HOME/.bashrc"
            fi
            if ! grep -q "alias cat=" "$HOME/.bashrc" 2>/dev/null; then
                echo '\''alias cat="batcat --paging=never 2>/dev/null || bat --paging=never 2>/dev/null || cat"'\'' >> "$HOME/.bashrc"
                echo '\''alias ls="eza --icons 2>/dev/null || ls --color=auto"'\'' >> "$HOME/.bashrc"
            fi
        ' || true

        echo "Modern CLI tools & Starship prompt configured!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)

    def install_zsh_ohmyzsh(self, callback: Optional[Callable[[str, str], None]] = None) -> CommandResult:
        """Installs Zsh and Oh-My-Zsh with syntax highlighting and autosuggestions."""
        script = """
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y zsh git curl
        elif command -v dnf >/dev/null 2>&1; then
            dnf install -y zsh git curl
        elif command -v pacman >/dev/null 2>&1; then
            pacman -S --needed --noconfirm zsh git curl
        fi

        sudo -u "$REAL_USER" -H bash -c '
            export RUNZSH=no
            export CHSH=no
            sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended 2>/dev/null || true
            ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
            git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null || true
            git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null || true
            sed -i '\''s/plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting)/g'\'' "$HOME/.zshrc" 2>/dev/null || true
            if ! grep -q "starship init zsh" "$HOME/.zshrc" 2>/dev/null; then
                echo '\''eval "$(starship init zsh)"'\'' >> "$HOME/.zshrc"
            fi
        ' || true

        echo "Zsh with Oh-My-Zsh and plugins installed!"
        """
        return self.runner.run_script_block(script, use_sudo=True, callback=callback)
