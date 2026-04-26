#!/usr/bin/env python3
"""
SPECTRE — afk.py
AFK detection using KDE's org.freedesktop.ScreenSaver DBus interface.
Returns True if the user has been idle longer than AFK_THRESHOLD seconds.
"""

import subprocess

# ── Config ────────────────────────────────────────────────────────────────────
AFK_THRESHOLD = 120  # seconds of idle time before marking as AFK
# ─────────────────────────────────────────────────────────────────────────────


def get_idle_time_ms() -> int | None:
    """
    Get system idle time in milliseconds via DBus.

    Tries multiple DBus interfaces in order of preference:
    1. org.freedesktop.ScreenSaver (KDE Plasma standard)
    2. org.gnome.Mutter.IdleMonitor (fallback, unlikely on KDE)
    """
    # Method 1: freedesktop ScreenSaver — works on KDE Plasma
    try:
        result = subprocess.run(
            [
                "qdbus",
                "org.freedesktop.ScreenSaver",
                "/ScreenSaver",
                "org.freedesktop.ScreenSaver.GetSessionIdleTime",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip().isdigit():
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Method 2: dbus-send fallback
    try:
        result = subprocess.run(
            [
                "dbus-send",
                "--session",
                "--dest=org.freedesktop.ScreenSaver",
                "--type=method_call",
                "--print-reply",
                "/ScreenSaver",
                "org.freedesktop.ScreenSaver.GetSessionIdleTime",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            # Output: "   uint32 12345"
            for token in result.stdout.split():
                if token.isdigit():
                    return int(token)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def is_afk(threshold_seconds: int = AFK_THRESHOLD) -> bool:
    """
    Returns True if the user is currently AFK (idle beyond threshold).
    Returns False if idle time cannot be determined (fail-open: assume active).
    """
    idle_ms = get_idle_time_ms()
    if idle_ms is None:
        return False  # Can't determine — assume active
    return idle_ms >= (threshold_seconds * 1000)


def get_idle_seconds() -> float | None:
    """Returns idle time in seconds, or None if unavailable."""
    ms = get_idle_time_ms()
    return ms / 1000.0 if ms is not None else None


# Quick test when run directly
if __name__ == "__main__":
    idle = get_idle_seconds()
    afk = is_afk()
    if idle is not None:
        print(f"Idle time : {idle:.1f}s")
        print(f"AFK       : {afk} (threshold: {AFK_THRESHOLD}s)")
    else:
        print("Could not read idle time from DBus.")
        print("Make sure you're running a KDE Plasma session.")
