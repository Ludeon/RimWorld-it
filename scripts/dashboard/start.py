#!/usr/bin/env python3
"""Dev-friendly launcher for the RimWorld-it translation toolkit.

Zero-setup entry point: bootstraps the virtualenv + dependencies on first run,
then routes to the right tool. Run it with the SYSTEM python from the repo root:

    python scripts/dashboard/start.py             # launch the dashboard (default)
    python scripts/dashboard/start.py setup        # (re)create .venv + install deps
    python scripts/dashboard/start.py build        # rebuild the translation ledger
    python scripts/dashboard/start.py langcheck    # detect wrong-language strings
    python scripts/dashboard/start.py todo         # export the worklist
    python scripts/dashboard/start.py rwit -- ...  # pass through to the rwit CLI
    python scripts/dashboard/start.py help         # show this help

Cross-platform (Windows / macOS / Linux).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# scripts/dashboard/start.py -> repo root is two levels up.
ROOT = Path(__file__).resolve().parents[2]
DASH = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQS = ROOT / "scripts" / "requirements.txt"


def _venv_bin(name: str) -> Path:
    sub = "Scripts" if os.name == "nt" else "bin"
    exe = f"{name}.exe" if os.name == "nt" else name
    return VENV / sub / exe


def _has_env() -> bool:
    return _venv_bin("python").exists()


def setup(force: bool = False) -> None:
    """Create the venv (if missing) and install/refresh dependencies."""
    if not _has_env() or force:
        print("• Creating virtualenv (.venv)...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    print("• Installing dependencies...")
    subprocess.check_call([str(_venv_bin("python")), "-m", "pip", "install",
                           "-q", "--upgrade", "pip"])
    subprocess.check_call([str(_venv_bin("python")), "-m", "pip", "install",
                           "-q", "-r", str(REQS)])
    print("✓ Environment ready.")


def _ensure_env() -> None:
    if not _has_env():
        print("No .venv found — setting it up once...\n")
        setup()


def _run(args: list[str]) -> int:
    return subprocess.call(args, cwd=str(ROOT))


def dashboard() -> int:
    # Flask review dashboard: stateless, reads the CSV/XML fresh on every request
    # (no caching -> never shows stale data). Replaces the old Streamlit app.
    print("Review dashboard → http://127.0.0.1:5000  (Ctrl+C here to stop it)")
    return _run([str(_venv_bin("python")), str(DASH / "server.py")])


def rwit(extra: list[str]) -> int:
    return _run([str(_venv_bin("python")), str(ROOT / "scripts" / "rwit"), *extra])


def main(argv: list[str]) -> int:
    cmd = (argv[0] if argv else "dashboard").lower()
    rest = argv[1:]
    if rest and rest[0] == "--":  # allow: start.py rwit -- analyze --dlc Core
        rest = rest[1:]

    if cmd in ("help", "-h", "--help"):
        print(__doc__)
        return 0
    if cmd == "setup":
        setup(force="--force" in rest)
        return 0

    _ensure_env()
    if cmd == "dashboard":
        return dashboard()
    if cmd == "build":
        return rwit(["ledger", "build", *rest])
    if cmd in ("langcheck", "lang-check"):
        return rwit(["lang-check", *rest])
    if cmd == "todo":
        return rwit(["ledger", "todo", *rest])
    if cmd == "rwit":
        return rwit(rest)
    print(f"Unknown command: {cmd}\n")
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
