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

# Sezione "Unnecessary keyed translations": `Key 'testo' (File.xml:line)`.
# Il testo puo' contenere apostrofi -> match greedy fino all'ultimo ' prima di (file:line).
_UNUSED_KEYED = re.compile(r"^(\S+)\s+'(.*)'\s+\((.+?):(\d+)\)\s*$")
# Load error "Couldn't inject X into Y (File.xml): reason"
_INJECT_ERR = re.compile(r"^Couldn't inject (\S+) into (\S+) \((.+?)\): (.+)$")
# Load error "Found no <DefType> named <Name> to match <Path> (File.xml)"
_NODEF_ERR = re.compile(r"^Found no (\S+) named (\S+) to match (\S+) \((.+?)\)\s*$")


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
class UnusedKeyed:
    key: str
    text: str
    file: str            # basename del file IT (es. "Alerts.xml")
    line: int            # riga nel file IT caricato (= file del repo, via symlink)


@dataclass
class LoadError:
    raw: str             # riga integrale del report
    kind: str            # "inject" | "nodef"
    path: str            # path d'iniezione (X) o tag-path da matchare
    target: str          # DefType di destinazione, o DefType cercato
    file: str            # file Defs di origine fra parentesi (es. "Apparel_Packs.xml")
    reason: str          # motivo (per "inject") o nome-def mancante (per "nodef")


@dataclass
class Report:
    path: Path
    sections: dict       # nome sezione -> conteggio dichiarato dal gioco
    keyed: list           # KeyedEntry della sezione "Missing keyed"
    defs: list            # DefEntry della sezione "Def-injected ... missing"
    unused_keyed: list    # UnusedKeyed della sezione "Unnecessary keyed translations"
    load_errors: list     # LoadError della sezione "Def-injected ... load errors"


def parse(path) -> Report:
    path = Path(path)
    sections: dict[str, int] = {}
    keyed: list[KeyedEntry] = []
    defs: list[DefEntry] = []
    unused_keyed: list[UnusedKeyed] = []
    load_errors: list[LoadError] = []
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
            elif current.startswith("Unnecessary keyed"):
                m = _UNUSED_KEYED.match(line)
                if m:
                    unused_keyed.append(UnusedKeyed(m.group(1), m.group(2), m.group(3), int(m.group(4))))
            elif current.startswith("Def-injected translations load errors"):
                e = _parse_load_error(line)
                if e:
                    load_errors.append(e)
    return Report(path, sections, keyed, defs, unused_keyed, load_errors)


def _parse_load_error(line: str) -> LoadError | None:
    mi = _INJECT_ERR.match(line)
    if mi:
        return LoadError(line, "inject", mi.group(1), mi.group(2), mi.group(3), mi.group(4))
    mn = _NODEF_ERR.match(line)
    if mn:
        # "Found no <DefType> named <Name> to match <Path> (File)"
        return LoadError(line, "nodef", mn.group(3), mn.group(1), mn.group(4), mn.group(2))
    return None


def _parse_def(line: str) -> DefEntry | None:
    mh = _DEF_HEAD.match(line)
    if not mh:
        return None
    deftype, rest = mh.group(1), _HINT.sub("", mh.group(2))
    mb = _DEF_BODY.match(rest)
    if not mb:
        return None
    return DefEntry(deftype, mb.group(1), mb.group(2))
