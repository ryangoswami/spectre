#!/usr/bin/env python3
"""
SPECTRE — daemon.py
Phase 00: Active window tracker via KWin DBus (KDE Plasma 6 + Wayland)

Uses org.kde.KWin.queryWindowInfo to get the active window.
Prints to stdout on every window change. No DB yet (Phase 01).
"""

import time
import subprocess
import os
import sys
from datetime import datetime

from afk import is_afk

# ── Config ────────────────────────────────────────────────────────────────────
POLL_INTERVAL = 5       # seconds between polls
QDBUS = "qdbus6"        # binary name on Arch + qt6-tools
# ─────────────────────────────────────────────────────────────────────────────


def parse_kwin_map(raw: str) -> dict:
    """
    Parse KWin's key: value output into a Python dict.
    Example input line: 'caption: ~ : bash — Konsole'
    """
    result = {}
    for line in raw.strip().splitlines():
        if ": " in line:
            key, _, value = line.partition(": ")
            result[key.strip()] = value.strip()
    return result


def get_active_window() -> dict | None:
    """
    Get the currently active window info from KWin via DBus.

    Uses: qdbus6 org.kde.KWin /KWin org.kde.KWin.queryWindowInfo
    When called non-interactively from a daemon, this returns the
    currently focused/active window reliably.

    Returns dict with keys: title, app, desktop, uuid
    Returns None on any failure.
    """
    try:
        result = subprocess.run(
            [
                QDBUS,
                "org.kde.KWin",
                "/KWin",
                "org.kde.KWin.queryWindowInfo",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        data = parse_kwin_map(result.stdout)

        return {
            "title":   data.get("caption", "Unknown"),
            "app":     data.get("resourceClass", "unknown"),
            "desktop": data.get("desktopFile", "unknown"),
            "uuid":    data.get("uuid", ""),
        }

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        print(f"[ERROR] '{QDBUS}' not found. Run: sudo pacman -S qt6-tools")
        sys.exit(1)
    except Exception:
        return None


def format_log(window: dict | None, afk: bool) -> str:
    """Format a single poll line for terminal output."""
    ts = datetime.now().strftime("%H:%M:%S")
    if afk:
        return f"[{ts}]  💤  AFK"
    if window is None:
        return f"[{ts}]  ⚠   Could not read active window"
    app   = window.get("app", "?")
    title = window.get("title", "?")
    if len(title) > 55:
        title = title[:52] + "..."
    return f"[{ts}]  🖥   {app:<22} {title}"


def main():
    print("=" * 60)
    print("  SPECTRE daemon — Phase 00")
    print(f"  Poll interval : {POLL_INTERVAL}s")
    print(f"  PID           : {os.getpid()}")
    print("=" * 60)
    print()

    last_key = None

    try:
        while True:
            afk    = is_afk()
            window = get_active_window()

            if afk:
                current_key = "afk"
            elif window:
                current_key = (window.get("app"), window.get("title"))
            else:
                current_key = None

           # Only print when something actually changes, skip transient None states
            if current_key != last_key and current_key is not None:
                print(format_log(window, afk))
                last_key = current_key

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n  SPECTRE daemon stopped. o7")
        sys.exit(0)


if __name__ == "__main__":
    main()
