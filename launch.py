#!/usr/bin/env python3
"""Launch ORBIT and resize the terminal to 150×50 first."""
import os
import sys
import subprocess
import platform

COLS, ROWS = 140, 43


def resize_terminal() -> None:
    os_name = platform.system()
    if os_name == "Darwin":
        # AppleScript: resize the frontmost Terminal/iTerm window
        script = (
            f'tell application "Terminal" to set bounds of front window '
            f'to {{0, 0, {COLS * 8}, {ROWS * 18}}}'
        )
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
        # Also send ANSI resize escape just in case
        sys.stdout.write(f"\033[8;{ROWS};{COLS}t")
        sys.stdout.flush()
    elif os_name == "Windows":
        subprocess.run(["mode", "con:", f"cols={COLS}", f"lines={ROWS}"],
                       check=False, capture_output=True, shell=True)
    else:
        # Linux / generic: ANSI xterm resize sequence
        sys.stdout.write(f"\033[8;{ROWS};{COLS}t")
        sys.stdout.flush()


if __name__ == "__main__":
    resize_terminal()
    # Re-exec into the real entry point, passing through all args
    python = sys.executable
    orbit  = os.path.join(os.path.dirname(__file__), "orbit.py")
    os.execv(python, [python, orbit] + sys.argv[1:])
