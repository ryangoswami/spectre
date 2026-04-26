#!/usr/bin/env python3
"""
SPECTRE — daemon.py
Phase 00 (revised): Event-driven window tracker via KWin scripting + journalctl.

Architecture:
  1. A KWin JS script (spectre_watch.js) listens to workspace.windowActivated
     and prints "SPECTRE|caption|resourceClass" to journald via print().
  2. This daemon reads journalctl -f in real time, parses those lines,
     and logs window switches to stdout (Phase 01: also writes to SQLite).

No polling. No cursor freeze. Completely silent.
"""

import subprocess
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from afk import is_afk

# ── Config ────────────────────────────────────────────────────────────────────
KWIN_SCRIPT_NAME = "spectre_watch"
KWIN_SCRIPT_PATH = Path(__file__).parent / "spectre_watch.js"
SPECTRE_PREFIX   = "SPECTRE|"
# ─────────────────────────────────────────────────────────────────────────────


def load_kwin_script():
    """Load the KWin JS watcher script into the running KWin instance."""
    if not KWIN_SCRIPT_PATH.exists():
        print(f"[ERROR] KWin script not found: {KWIN_SCRIPT_PATH}")
        sys.exit(1)

    # Unload first in case it's already loaded from a previous run
    subprocess.run(
        ["qdbus6", "org.kde.KWin", "/Scripting",
         "org.kde.kwin.Scripting.unloadScript", KWIN_SCRIPT_NAME],
        capture_output=True,
    )

    # Load the script
    result = subprocess.run(
        ["qdbus6", "org.kde.KWin", "/Scripting",
         "org.kde.kwin.Scripting.loadScript",
         str(KWIN_SCRIPT_PATH), KWIN_SCRIPT_NAME],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] Failed to load KWin script: {result.stderr}")
        sys.exit(1)

    # Start the scripting engine
    subprocess.run(
        ["qdbus6", "org.kde.KWin", "/Scripting",
         "org.kde.kwin.Scripting.start"],
        capture_output=True,
    )

    print(f"  KWin script loaded: {KWIN_SCRIPT_NAME}")


def parse_spectre_line(line: str) -> dict | None:
    """
    Parse a journald line containing SPECTRE output.
    Format: '... kwin_wayland[PID]: SPECTRE|caption|resourceClass'
    Returns dict with title and app, or None if not a SPECTRE line.
    """
    if SPECTRE_PREFIX not in line:
        return None

    # Extract the SPECTRE|... part
    idx = line.index(SPECTRE_PREFIX)
    payload = line[idx + len(SPECTRE_PREFIX):]
    parts = payload.strip().split("|")

    if len(parts) < 2:
        return None

    return {
        "title": parts[0].strip(),
        "app":   parts[1].strip(),
    }


def format_log(window: dict, afk: bool) -> str:
    """Format a window event line for terminal output."""
    ts = datetime.now().strftime("%H:%M:%S")
    if afk:
        return f"[{ts}]  💤  AFK"
    app   = window.get("app", "?")
    title = window.get("title", "?")
    if len(title) > 55:
        title = title[:52] + "..."
    return f"[{ts}]  🖥   {app:<22} {title}"


def main():
    print("=" * 60)
    print("  SPECTRE daemon — Phase 00 (event-driven)")
    print(f"  PID : {os.getpid()}")
    print("=" * 60)
    print()

    # Load the KWin watcher script
    load_kwin_script()
    print("  Listening for window events...\n")

    # Stream journalctl output in real time
    proc = subprocess.Popen(
        ["journalctl", "-f", "--no-pager", "--output=short"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    try:
        for line in proc.stdout:
            window = parse_spectre_line(line)
            if window:
                afk = is_afk()
                print(format_log(window, afk))

    except KeyboardInterrupt:
        print("\n\n  SPECTRE daemon stopped. o7")
        proc.terminate()
        # Unload KWin script cleanly
        subprocess.run(
            ["qdbus6", "org.kde.KWin", "/Scripting",
             "org.kde.kwin.Scripting.unloadScript", KWIN_SCRIPT_NAME],
            capture_output=True,
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
