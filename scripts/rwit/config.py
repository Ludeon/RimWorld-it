"""Percorsi e costanti condivise per gli strumenti di traduzione."""
from __future__ import annotations

import os
from pathlib import Path

# DLC supportate, nell'ordine di caricamento del gioco.
DLCS = ["Core", "Royalty", "Ideology", "Biotech", "Anomaly", "Odyssey"]


def repo_root() -> Path:
    """Radice del repo: .../RimWorld-it/scripts/rwit/config.py -> parents[2]."""
    return Path(__file__).resolve().parents[2]


def game_data(override: str | None = None) -> Path:
    """Cartella Data dell'installazione di RimWorld.

    Ordine: override esplicito -> variabile RIMWORLD_DATA -> percorsi noti.
    """
    if override:
        p = Path(override)
        if not p.exists():
            raise FileNotFoundError(f"GameData inesistente: {p}")
        return p
    env = os.environ.get("RIMWORLD_DATA")
    if env and Path(env).exists():
        return Path(env)
    for c in (
        r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data",
        r"C:\Program Files\Steam\steamapps\common\RimWorld\Data",
    ):
        if Path(c).exists():
            return Path(c)
    raise FileNotFoundError(
        "Installazione RimWorld non trovata; usa --game-data o imposta RIMWORLD_DATA"
    )


def game_version(data: Path | None = None) -> str | None:
    """Versione del gioco da Version.txt, o None."""
    data = data or game_data()
    vf = data.parent / "Version.txt"
    if vf.exists():
        return vf.read_text(encoding="utf-8").strip()
    return None


def reports_dir() -> Path:
    """Cartella reports/ (gitignored), creata se manca."""
    d = repo_root() / "reports"
    d.mkdir(exist_ok=True)
    return d


def desktop_report() -> Path | None:
    """TranslationReport.txt sul Desktop, se presente."""
    for base in (Path.home() / "Desktop", Path.home() / "OneDrive" / "Desktop"):
        f = base / "TranslationReport.txt"
        if f.exists():
            return f
    return None
