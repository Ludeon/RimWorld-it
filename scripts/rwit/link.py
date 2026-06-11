"""Gestione dei symlink repo -> installazione del gioco (Windows).

Crea, per ogni DLC, il collegamento  <Data>\<DLC>\Languages\Italiano -> <repo>\<DLC>.
Il bersaglio e SEMPRE ricalcolato dalla posizione attuale del repo: questo risolve
i link rotti dopo uno spostamento della cartella del progetto.

Richiede privilegi di amministratore, oppure la "Modalita sviluppatore" di Windows
attiva (che consente i symlink senza elevazione).
"""
from __future__ import annotations

import ctypes
import os
import shutil
import sys
from pathlib import Path

import config


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate() -> None:
    """Rilancia il comando corrente con privilegi admin (UAC) e termina."""
    script = str(Path(sys.argv[0]).resolve())
    args = [script] + sys.argv[1:]
    params = " ".join(f'"{a}"' for a in args)
    cwd = str(Path.cwd())
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, cwd, 1)
    if rc <= 32:
        raise RuntimeError(f"Elevazione UAC fallita (codice {rc})")
    sys.exit(0)


def _remove_link(link: Path) -> None:
    """Rimuove in sicurezza un link/cartella preesistente senza seguire i symlink."""
    if link.is_symlink():
        try:
            os.rmdir(link)        # symlink a cartella: elimina solo il link
        except OSError:
            os.unlink(link)
    elif link.is_dir():
        shutil.rmtree(link)
    elif link.exists():
        link.unlink()


def relink(game_data: Path, dlcs) -> list[tuple[str, str]]:
    results = []
    repo = config.repo_root()
    for dlc in dlcs:
        target = repo / dlc
        link = game_data / dlc / "Languages" / "Italiano"
        if not target.exists():
            results.append((dlc, "salto: assente nel repo"))
            continue
        if not link.parent.exists():
            results.append((dlc, "salto: manca Languages nel gioco"))
            continue
        _remove_link(link)
        os.symlink(target, link, target_is_directory=True)
        results.append((dlc, f"-> {target}"))
    return results


def unlink(game_data: Path, dlcs) -> list[tuple[str, str]]:
    results = []
    for dlc in dlcs:
        link = game_data / dlc / "Languages" / "Italiano"
        if link.is_symlink():
            _remove_link(link)
            results.append((dlc, "link rimosso"))
        elif link.exists():
            results.append((dlc, "ATTENZIONE: cartella reale, non tocco nulla"))
        else:
            results.append((dlc, "nessun link"))
    return results
