"""Lettura delle traduzioni gia presenti nel repo (Keyed e DefInjected)."""
from __future__ import annotations

from pathlib import Path

from lxml import etree


def _iter_xml(base: Path):
    if base.exists():
        yield from sorted(base.rglob("*.xml"))


def _root(path: Path):
    try:
        return etree.parse(str(path)).getroot()
    except (etree.XMLSyntaxError, OSError):
        return None


def read_keyed(repo_root: Path, dlcs) -> dict[str, str]:
    """key -> testo presente nel repo (anche stringa vuota)."""
    out: dict[str, str] = {}
    for dlc in dlcs:
        for f in _iter_xml(repo_root / dlc / "Keyed"):
            root = _root(f)
            if root is None:
                continue
            for el in root:
                if isinstance(el.tag, str):  # salta commenti / PI
                    out[el.tag] = el.text or ""
    return out


def read_definjected(repo_root: Path, dlcs) -> dict[str, set]:
    """deftype -> insieme dei nomi-tag presenti sotto DefInjected/<deftype>/."""
    out: dict[str, set] = {}
    for dlc in dlcs:
        di = repo_root / dlc / "DefInjected"
        if not di.exists():
            continue
        for typedir in sorted(p for p in di.iterdir() if p.is_dir()):
            names = out.setdefault(typedir.name, set())
            for f in _iter_xml(typedir):
                root = _root(f)
                if root is None:
                    continue
                for el in root:
                    if isinstance(el.tag, str):
                        names.add(el.tag)
    return out
