"""In-app terminal backend: spawns a real shell in a pseudo-terminal (PTY).

The frontend (xterm.js) talks to this over a WebSocket. Each connection gets its
own bash process whose working directory is the generated project folder, so the
user can run npm/node/python against their files exactly like a local terminal.
"""

import os
import pty
import fcntl
import struct
import signal
import termios
import subprocess


def open_pty_shell(cwd: str):
    """Start `bash` attached to a new PTY in `cwd`.

    Returns (process, master_fd). Read the shell's output from master_fd and
    write the user's keystrokes to it.
    """
    os.makedirs(cwd, exist_ok=True)
    master_fd, slave_fd = pty.openpty()

    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["LANG"] = env.get("LANG", "C.UTF-8")
    # Project-local CLIs (e.g. node_modules/.bin) take precedence.
    local_bin = os.path.join(cwd, "node_modules", ".bin")
    env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    # A friendly, lightweight prompt.
    env["PS1"] = r"\[\e[38;5;141m\]\w\[\e[0m\] $ "

    proc = subprocess.Popen(
        ["bash", "--norc", "-i"],
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=cwd,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)
    return proc, master_fd


def set_winsize(fd: int, rows: int, cols: int):
    """Tell the PTY its window size so full-screen TUIs render correctly."""
    try:
        rows = max(1, min(300, int(rows)))
        cols = max(1, min(500, int(cols)))
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    except Exception:
        pass


def terminate(proc, master_fd):
    """Kill the shell's process group and close the PTY."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        pass
    try:
        os.close(master_fd)
    except Exception:
        pass
