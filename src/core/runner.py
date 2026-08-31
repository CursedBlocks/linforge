"""
LinForge - Asynchronous Command Runner
Executes shell commands with live stdout/stderr streaming, privilege escalation
(pkexec / sudo), user context resolution ($REAL_USER, $REAL_HOME), timeout enforcement, and cancellation control.
"""

import os
import queue
import select
import shutil
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class CommandResult:
    """Encapsulates the result of a finished command execution."""

    def __init__(self, exit_code: int, stdout: str, stderr: str, duration: float, cancelled: bool = False):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.cancelled = cancelled
        self.success = (exit_code == 0) and not cancelled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": round(self.duration, 2),
            "cancelled": self.cancelled,
            "success": self.success
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
        """Terminates the actively running process."""
        with self._lock:
            if self._current_process and self._current_process.poll() is None:
                self._is_cancelled = True
                try:
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
                if shutil.which("pkexec") and is_graphical:
                    final_cmd = f"pkexec env DISPLAY={os.environ.get('DISPLAY', '')} XAUTHORITY={os.environ.get('XAUTHORITY', '')} WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY', '')} bash -c {subprocess.list2cmdline([command])}"
                elif shutil.which("sudo"):
                    final_cmd = f"sudo -E bash -c {subprocess.list2cmdline([command])}"

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
                env=exec_env
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

            if callback:
                if self._is_cancelled:
                    callback("system", "⏹️ Command was cancelled by user.")
                elif exit_code == 0:
                    callback("system", f"✅ Completed successfully in {round(duration, 2)}s")
                else:
                    callback("system", f"❌ Failed with exit code {exit_code} in {round(duration, 2)}s")

            return CommandResult(
                exit_code=exit_code if not self._is_cancelled else -1,
                stdout="\n".join(stdout_lines),
                stderr="\n".join(stderr_lines),
                duration=duration,
                cancelled=self._is_cancelled
            )

        except Exception as e:
            err_msg = str(e)
            if callback:
                callback("stderr", f"Execution error: {err_msg}")
            return CommandResult(
                exit_code=1,
                stdout="\n".join(stdout_lines),
                stderr=err_msg,
                duration=time.time() - start_time,
                cancelled=False
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
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6 2>/dev/null || echo "/home/$REAL_USER")
if [ -z "$REAL_HOME" ] || [ ! -d "$REAL_HOME" ]; then
    REAL_HOME="$HOME"
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
