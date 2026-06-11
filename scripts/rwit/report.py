"""Parser del TranslationReport.txt generato da RimWorld (Dev mode)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SECTION = re.compile(r"^=+ (.+?) \((\d+)\) =+\s*$")
_KEYED = re.compile(r"^(\S+)\s+'(.*)'\s+\(English file:\s+(.+?):(\d+)\)\s*$")
_HINT = re.compile(r"\s+\(hint:.*\)\s*$")
_DEF_HEAD = re.compile(r"^(\w+):\s+(.*)$")
_DEF_BODY = re.compile(r"^(\S+)\s+'(.*)'$")


@dataclass
class KeyedEntry:
    key: str
    text: str
    file: str
    line: int


@dataclass
class DefEntry:
    deftype: str
    defpath: str
    text: str


@dataclass
class Report:
    path: Path
    sections: dict       # nome sezione -> conteggio dichiarato dal gioco
    keyed: list           # KeyedEntry della sezione "Missing keyed"
    defs: list            # DefEntry della sezione "Def-injected ... missing"


def parse(path) -> Report:
    path = Path(path)
    sections: dict[str, int] = {}
    keyed: list[KeyedEntry] = []
    defs: list[DefEntry] = []
    current: str | None = None
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            ms = _SECTION.match(line)
            if ms:
                current = ms.group(1).strip()
                sections[current] = int(ms.group(2))
                continue
            if not line.strip() or current is None:
                continue
            if current.startswith("Missing keyed"):
                m = _KEYED.match(line)
                if m:
                    keyed.append(KeyedEntry(m.group(1), m.group(2), m.group(3), int(m.group(4))))
            elif current.startswith("Def-injected translations missing"):
                e = _parse_def(line)
                if e:
                    defs.append(e)
    return Report(path, sections, keyed, defs)


def _parse_def(line: str) -> DefEntry | None:
    mh = _DEF_HEAD.match(line)
    if not mh:
        return None
    deftype, rest = mh.group(1), _HINT.sub("", mh.group(2))
    mb = _DEF_BODY.match(rest)
    if not mb:
        return None
    return DefEntry(deftype, mb.group(1), mb.group(2))
