#!/usr/bin/env python3
"""
SPECTRE — daemon.py
Phase 00: Active window tracker via KWin DBus (KDE Plasma + Wayland)

Polls the active window every POLL_INTERVAL seconds using KWin's
scripting API over DBus. Prints to stdout for now (Phase 00).
DB writes come in Phase 01.
"""

import time
import subprocess
import os
import sys
from datetime import datetime

from afk import is_afk

# ── Config ────────────────────────────────────────────────────────────────────
POLL_INTERVAL = 5  # seconds between polls
# ─────────────────────────────────────────────────────────────────────────────


def get_active_window() -> dict | None:
    """
    Ask KWin for the currently active window via its scripting DBus API.

    KWin exposes a method: org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript
    We inject a tiny JS snippet that reads workspace.activeClient (KWin 5)
    or workspace.activeWindow (KWin 6) and logs caption + resourceClass.
    The output comes back via KWin's console.log → journald.

    Simpler approach for Phase 00: use qdbus directly via subprocess.
    This avoids needing dbus-python installed and works immediately.
    """
    try:
        # Try KWin 6 style first (Plasma 6 / KWin 6)
        result = subprocess.run(
            [
                "qdbus",
                "org.kde.KWin",
                "/KWin",
                "org.kde.KWin.activeWindow",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0 and result.stdout.strip():
            window_id = result.stdout.strip()

            # Get window title
            title_result = subprocess.run(
                ["qdbus", "org.kde.KWin", f"/windows/{window_id}", "org.kde.KWin.Window.caption"],
                capture_output=True, text=True, timeout=2,
            )
            # Get app class
            class_result = subprocess.run(
                ["qdbus", "org.kde.KWin", f"/windows/{window_id}", "org.kde.KWin.Window.resourceClass"],
                capture_output=True, text=True, timeout=2,
            )

            title = title_result.stdout.strip() if title_result.returncode == 0 else "Unknown"
            app_class = class_result.stdout.strip() if class_result.returncode == 0 else "unknown"

            return {"title": title, "app": app_class, "window_id": window_id}

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: KWin scripting injection via eval script
    try:
        js_snippet = """
var w = workspace.activeWindow || workspace.activeClient;
if (w) {
    print(w.caption + '|||' + w.resourceClass);
} else {
    print('none|||none');
}
"""
        # Write temp script
        tmp_script = "/tmp/spectre_query.js"
        with open(tmp_script, "w") as f:
            f.write(js_snippet)

        result = subprocess.run(
            ["qdbus", "org.kde.KWin", "/Scripting",
             "org.kde.kwin.Scripting.loadScript", tmp_script, "spectre_query"],
            capture_output=True, text=True, timeout=3,
        )

        if result.returncode == 0:
            script_id = result.stdout.strip()
            subprocess.run(
                ["qdbus", "org.kde.KWin", f"/{script_id}",
                 "org.kde.kwin.Script.run"],
                capture_output=True, text=True, timeout=3,
            )

    except Exception:
        pass

    return None


def format_log(window: dict | None, afk: bool) -> str:
    """Format a single poll line for terminal output."""
    ts = datetime.now().strftime("%H:%M:%S")
    if afk:
        return f"[{ts}]  💤 AFK"
    if window is None:
        return f"[{ts}]  ⚠  Could not read active window"
    app = window.get("app", "?")
    title = window.get("title", "?")
    # Truncate long titles
    if len(title) > 60:
        title = title[:57] + "..."
    return f"[{ts}]  🖥  {app:<20}  {title}"


def main():
    print("=" * 60)
    print("  SPECTRE daemon — Phase 00")
    print(f"  Poll interval : {POLL_INTERVAL}s")
    print(f"  PID           : {os.getpid()}")
    print("=" * 60)
    print()

    last_window = None

    try:
        while True:
            afk = is_afk()
            window = get_active_window()

            # Only print when something changes (cleaner output)
            current_key = (
                "afk" if afk
                else (window.get("app"), window.get("title")) if window
                else None
            )

            if current_key != last_window:
                print(format_log(window, afk))
                last_window = current_key

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n  SPECTRE daemon stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
