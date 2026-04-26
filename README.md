# SPECTRE

**Silent Process & Environment Control / Tracking & Reconnaissance Engine**

A local-first activity tracker for KDE Plasma on Wayland. Tracks your active window, measures time per application, and surfaces it through a cyberpunk dashboard — all stored privately on your machine. No cloud. No telemetry. Yours.

> Built on Arch Linux · KDE Plasma 6 · Wayland · Python 3

---

## Status

🚧 **Phase 00 — Daemon Core** (in active development)

| Phase | Description | Status |
|-------|-------------|--------|
| 00 | Daemon — active window polling via KWin DBus | 🔨 In Progress |
| 01 | Database layer — SQLite activity storage | ⏳ Planned |
| 02 | Flask API + cyberpunk dashboard (localhost:6969) | ⏳ Planned |
| 03 | systemd services + PKGBUILD packaging | ⏳ Planned |
| 04 | AUR release + r/unixporn | ⏳ Planned |

---

## Features (Phase 00)

- Polls active window every 5 seconds via KWin DBus
- AFK detection via `org.freedesktop.ScreenSaver` idle time
- Only logs on window change — clean terminal output
- Works on KDE Plasma 6 + Wayland (and X11)

---

## Requirements

- KDE Plasma 6 (KWin)
- Python 3.12+
- `qdbus` (usually pre-installed on KDE — part of `qt6-tools`)

```bash
# Check if qdbus is available
qdbus --version
```

---

## Running (Phase 00)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/spectre.git
cd spectre

# Run the daemon
python daemon.py

# Test AFK detection separately
python afk.py
```

Expected output:
```
============================================================
  SPECTRE daemon — Phase 00
  Poll interval : 5s
  PID           : 12345
============================================================

[14:23:01]  🖥  firefox              GitHub - spectre - Firefox
[14:23:11]  🖥  konsole              rust@arch: ~/projects/spectre
[14:26:00]  💤 AFK
```

---

## Project Structure

```
spectre/
├── daemon.py       # Core polling loop
├── afk.py          # AFK detection via DBus idle time
├── db.py           # (Phase 01) SQLite storage layer
├── server.py       # (Phase 02) Flask API server
├── dashboard/
│   └── index.html  # (Phase 02) Cyberpunk dashboard UI
└── README.md
```

---

## Why not ActivityWatch?

ActivityWatch is excellent but heavy — multi-process architecture, complex setup, and Wayland support on KDE is still incomplete. SPECTRE is intentionally minimal: a single Python daemon, tight KDE integration and zero bloat.

---

## License

GPL-3.0 — see [LICENSE](LICENSE)

---

*Built by [Rust](https://github.com/YOUR_USERNAME) · Surat, India · 2026*
