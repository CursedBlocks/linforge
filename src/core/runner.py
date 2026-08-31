"""
LinForge - Asynchronous Command Runner & Diagnostic Error Classifier
Executes shell commands with live stdout/stderr streaming, privilege escalation
(pkexec / sudo), user context resolution ($REAL_USER, $REAL_HOME), timeout enforcement,
and intelligent error classification.
"""

import os
import queue
import re
import select
import shutil
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class CommandResult:
    """Encapsulates the result of a finished command execution with structured diagnostics."""

    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        cancelled: bool = False,
        error_code: Optional[str] = None,
        error_title: Optional[str] = None,
        error_suggestion: Optional[str] = None
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.cancelled = cancelled
        self.success = (exit_code == 0) and not cancelled

        if not self.success and not error_code:
            code, title, sugg = self._classify_error(exit_code, stdout, stderr, cancelled)
            self.error_code = code
            self.error_title = title
            self.error_suggestion = sugg
        else:
            self.error_code = error_code or ("SUCCESS" if self.success else "ERR_EXEC_FAILED")
            self.error_title = error_title or ("Operation Succeeded" if self.success else "Command Failed")
            self.error_suggestion = error_suggestion or ""

    @staticmethod
    def _classify_error(exit_code: int, stdout: str, stderr: str, cancelled: bool) -> Tuple[str, str, str]:
        """Analyzes command outputs to provide a structured error code, title, and actionable fix."""
        combined = f"{stdout}\n{stderr}".lower()

        if cancelled:
            return (
                "ERR_CANCELLED",
                "Operation Cancelled",
                "The task was manually stopped by the user."
            )

        if "could not get lock" in combined or "unable to lock directory" in combined or "is another process using it" in combined:
            return (
                "ERR_DPKG_LOCKED",
                "Package Manager Database Locked",
                "Another package manager (like apt, unattended-upgrades, or Software Center) is currently running in the background. Use the LinForge Troubleshooter to unlock APT, or wait for the background update to finish."
            )

        if "unmet dependencies" in combined or "depends:" in combined or "dependency problems" in combined or "broken packages" in combined:
            return (
                "ERR_DEPENDENCY_MISSING",
                "Unmet Package Dependencies",
                "Required shared libraries or system packages are missing. LinForge can attempt an automatic dependency fix (`apt-get install -f -y`) or install this app via Flatpak instead."
            )

        if "libfuse.so.2" in combined or "cannot open shared object file: no such file" in combined and "fuse" in combined:
            return (
                "ERR_FUSE_MISSING",
                "AppImage FUSE2 Runtime Missing",
                "Modern Ubuntu 24.04 and Debian 12 do not pre-install libfuse2. LinForge can automatically install `libfuse2t64` / `libfuse2` to run AppImages."
            )

        if "could not resolve host" in combined or "failed to fetch" in combined or "404  not found" in combined or "network is unreachable" in combined:
            return (
                "ERR_NETWORK_OR_404",
                "Download or Network Connection Failed",
                "Could not download package archives from the remote repository. Check your internet connection or verify that the repository URL is active."
            )

        if "permission denied" in combined or "must be root" in combined or "are you root?" in combined or "sudo: a password is required" in combined:
            return (
                "ERR_PERMISSION_DENIED",
                "Privilege Escalation Required",
                "This action requires administrator (root/sudo) permissions. Please allow the authorization prompt when asked."
            )

        if "command not found" in combined or "no such file or directory" in combined:
            missing_cmd = "A required system tool"
            m = re.search(r"([a-zA-Z0-9_\-\.]+):\s*(?:command\s*not\s*found|No\s*such\s*file)", combined)
            if m:
                missing_cmd = f"Command `{m.group(1)}`"
            return (
                "ERR_COMMAND_NOT_FOUND",
                f"{missing_cmd} is Not Installed",
                "A required utility is missing from the system. LinForge will auto-install prerequisite packages."
            )

        if "no space left on device" in combined:
            return (
                "ERR_DISK_FULL",
                "Disk Storage Full",
                "Your storage drive has run out of free space. Run the LinForge System Cleaner to reclaim disk space."
            )

        return (
            f"ERR_EXIT_{exit_code}",
            f"Process Terminated with Error (Code {exit_code})",
            "Review the terminal console output below for full error details."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": round(self.duration, 2),
            "cancelled": self.cancelled,
            "success": self.success,
            "error_code": self.error_code,
            "error_title": self.error_title,
            "error_suggestion": self.error_suggestion
        }


class CommandRunner:
    """Thread-safe command executor with live output callbacks and user context resolution."""

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._is_cancelled = False

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._current_process is not None and self._current_process.poll() is None

    def cancel_current(self) -> bool:
        """Terminates the actively running process tree."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                self._is_cancelled = True
                try:
                    if os.name == "posix":
                        import signal
                        os.killpg(os.getpgid(self._current_process.pid), signal.SIGTERM)
                    else:
                        self._current_process.terminate()
                    threading.Timer(2.0, self._force_kill_if_alive).start()
                    return True
                except Exception:
                    pass
        return False

    def _force_kill_if_alive(self):
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                try:
                    if os.name == "posix":
                        import signal
                        os.killpg(os.getpgid(self._current_process.pid), signal.SIGKILL)
                    else:
                        self._current_process.kill()
                except Exception:
                    pass

    def run_command(
        self,
        command: str,
        use_sudo: bool = False,
        callback: Optional[Callable[[str, str], None]] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Executes a shell command synchronously on the caller thread while streaming live stdout/stderr.
        """
        self._is_cancelled = False
        start_time = time.time()
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        exec_env["DEBIAN_FRONTEND"] = "noninteractive"
        exec_env["NEEDRESTART_MODE"] = "a"

        # Determine real non-root user and home directory
        real_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"
        real_home = os.path.expanduser(f"~{real_user}") if real_user != "root" else os.path.expanduser("~")
        exec_env["REAL_USER"] = real_user
        exec_env["REAL_HOME"] = real_home

        final_cmd = command
        is_graphical = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

        if use_sudo and os.name == "posix":
            is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
            if not is_root:
                import shlex
                quoted_cmd = shlex.quote(command)
                if shutil.which("pkexec") and is_graphical:
                    final_cmd = f"pkexec env DISPLAY={shlex.quote(os.environ.get('DISPLAY', ''))} XAUTHORITY={shlex.quote(os.environ.get('XAUTHORITY', ''))} WAYLAND_DISPLAY={shlex.quote(os.environ.get('WAYLAND_DISPLAY', ''))} REAL_USER={shlex.quote(real_user)} REAL_HOME={shlex.quote(real_home)} bash -c {quoted_cmd}"
                elif shutil.which("sudo"):
                    final_cmd = f"sudo env REAL_USER={shlex.quote(real_user)} REAL_HOME={shlex.quote(real_home)} bash -c {quoted_cmd}"

        if callback:
            callback("system", f"▶ Executing: {command[:120]}{'...' if len(command) > 120 else ''}")

        try:
            process = subprocess.Popen(
                final_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=cwd,
                env=exec_env,
                start_new_session=(os.name == "posix")
            )

            with self._lock:
                self._current_process = process

            def read_stream(stream, stream_type: str, accumulator: List[str]):
                try:
                    for line in iter(stream.readline, ""):
                        if not line:
                            break
                        clean_line = line.rstrip("\r\n")
                        accumulator.append(clean_line)
                        if callback:
                            callback(stream_type, clean_line)
                    stream.close()
                except Exception:
                    pass

            t_out = threading.Thread(target=read_stream, args=(process.stdout, "stdout", stdout_lines))
            t_err = threading.Thread(target=read_stream, args=(process.stderr, "stderr", stderr_lines))
            t_out.start()
            t_err.start()

            # Wait with optional timeout
            deadline = time.time() + timeout if timeout else None
            while process.poll() is None:
                if deadline and time.time() > deadline:
                    self.cancel_current()
                    if callback:
                        callback("stderr", f"Command timed out after {timeout} seconds.")
                    break
                time.sleep(0.05)

            t_out.join(timeout=2.0)
            t_err.join(timeout=2.0)

            exit_code = process.returncode if process.returncode is not None else 1
            duration = time.time() - start_time
            stdout_str = "\n".join(stdout_lines)
            stderr_str = "\n".join(stderr_lines)

            res = CommandResult(
                exit_code=exit_code if not self._is_cancelled else -1,
                stdout=stdout_str,
                stderr=stderr_str,
                duration=duration,
                cancelled=self._is_cancelled
            )

            if callback:
                if self._is_cancelled:
                    callback("system", "⏹️ Command was cancelled by user.")
                elif res.success:
                    callback("system", f"✅ Completed successfully in {round(duration, 2)}s")
                else:
                    callback("system", f"❌ Failed [{res.error_code}]: {res.error_title} (exit code {exit_code}) in {round(duration, 2)}s")
                    if res.error_suggestion:
                        callback("system", f"💡 Suggestion: {res.error_suggestion}")

            return res

        except Exception as e:
            err_msg = str(e)
            if callback:
                callback("stderr", f"Execution error: {err_msg}")
            return CommandResult(
                exit_code=1,
                stdout="\n".join(stdout_lines),
                stderr=err_msg,
                duration=time.time() - start_time,
                cancelled=False,
                error_code="ERR_SUBPROCESS_EXCEPTION",
                error_title="Subprocess Launch Failed",
                error_suggestion="Check system resource limits or process permissions."
            )
        finally:
            with self._lock:
                self._current_process = None

    def run_script_block(
        self,
        script_content: str,
        use_sudo: bool = False,
        callback: Optional[Callable[[str, str], None]] = None,
        timeout: Optional[int] = None
    ) -> CommandResult:
        """Executes a multi-line bash script block safely with user environment preservation."""
        script_header = """
if [ -z "${REAL_USER:-}" ] || [ "${REAL_USER}" = "root" ]; then
    if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
        REAL_USER="$SUDO_USER"
    elif [ -n "${PKEXEC_UID:-}" ]; then
        REAL_USER=$(id -nu "$PKEXEC_UID" 2>/dev/null || echo "root")
    elif [ -n "${LOGNAME:-}" ] && [ "${LOGNAME}" != "root" ]; then
        REAL_USER="$LOGNAME"
    else
        REAL_USER=$(logname 2>/dev/null || echo "$USER")
    fi
fi
REAL_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6 || echo "")
if [ -z "$REAL_HOME" ] || [ ! -d "$REAL_HOME" ]; then
    REAL_HOME=$(eval echo "~$REAL_USER" 2>/dev/null || echo "$HOME")
fi
export REAL_USER REAL_HOME
"""
        script_cmd = f"bash -s << 'LINFORGE_EOF'\nset -eo pipefail\n{script_header}\n{script_content}\nLINFORGE_EOF"
        return self.run_command(
            command=script_cmd,
            use_sudo=use_sudo,
            callback=callback,
            timeout=timeout
        )
