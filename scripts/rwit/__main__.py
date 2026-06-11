"""rwit - strumenti per la traduzione italiana di RimWorld (1.6).

Uso (dalla radice del repo, col venv):
    .venv\\Scripts\\python scripts\\rwit --help
    .venv\\Scripts\\python scripts\\rwit analyze
    .venv\\Scripts\\python scripts\\rwit link
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

import config
import analyze as analyze_mod
import link as link_mod

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Strumenti per la traduzione italiana di RimWorld (1.6).",
)
console = Console()


@app.command(help="Confronta il TranslationReport con il repo e mostra il gap reale.")
def analyze(
    report: Optional[Path] = typer.Option(None, "--report", "-r", help="Percorso del TranslationReport.txt"),
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
):
    rep_path = report or config.desktop_report()
    if not rep_path or not Path(rep_path).exists():
        console.print("[red]Report non trovato.[/] Generalo in gioco o passa --report.")
        raise typer.Exit(1)

    ver = config.game_version() if _safe(config.game_version) else None
    console.print(f"[cyan]Report:[/] {rep_path}")
    if ver:
        console.print(f"[cyan]Gioco :[/] {ver}")

    gap = analyze_mod.compute(rep_path, dlc or None)

    t = Table(title="Gap di traduzione (reale, repo vs report)")
    t.add_column("Categoria")
    t.add_column("Conteggio", justify="right", style="bold")
    t.add_row("Keyed mancanti (assenti nel repo)", str(len(gap.keyed_missing)))
    t.add_row("Keyed non tradotte (vuote o == inglese)", str(len(gap.keyed_untranslated)))
    t.add_row("DefInjected mancanti", str(len(gap.def_missing)))
    console.print(t)

    by_type = analyze_mod.def_by_type(gap.def_missing)
    if by_type:
        tt = Table(title="DefInjected mancanti per tipo (top 25)")
        tt.add_column("DefType")
        tt.add_column("Mancanti", justify="right")
        for name, n in by_type.most_common(25):
            tt.add_row(name, str(n))
        console.print(tt)

    out = config.reports_dir() / f"gap_{datetime.now():%Y%m%d_%H%M}.txt"
    lines: list[str] = []
    lines.append("### KEYED MANCANTI (assenti nel repo) ###")
    lines += [f"{e.key} | {e.text}" for e in gap.keyed_missing]
    lines.append("")
    lines.append("### KEYED NON TRADOTTE (vuote o == inglese) ###")
    lines += [f"{e.key} | {e.text}" for e in gap.keyed_untranslated]
    lines.append("")
    lines.append("### DEFINJECTED MANCANTI ###")
    lines += [f"{e.deftype}: {e.defpath} | {e.text}" for e in gap.def_missing]
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio completo:[/] {out}")


@app.command(help="(Ri)crea i symlink Italiano nell'installazione del gioco.")
def link(game_data: Optional[str] = typer.Option(None, "--game-data")):
    data = config.game_data(game_data)
    console.print(f"[cyan]Repo :[/] {config.repo_root()}")
    console.print(f"[cyan]Gioco:[/] {data}")
    try:
        results = link_mod.relink(data, config.DLCS)
    except (PermissionError, OSError):
        if not link_mod.is_admin():
            console.print("[yellow]Permesso negato sui symlink: rilancio con UAC...[/]")
            link_mod.elevate()
        raise
    for dlc, msg in results:
        console.print(f"  {dlc:10} {msg}")
    console.print("[bold cyan]Fatto. Riavvia RimWorld perche rilegga la lingua.[/]")


@app.command(help="Rimuove i symlink Italiano dall'installazione del gioco.")
def unlink(game_data: Optional[str] = typer.Option(None, "--game-data")):
    data = config.game_data(game_data)
    try:
        results = link_mod.unlink(data, config.DLCS)
    except (PermissionError, OSError):
        if not link_mod.is_admin():
            console.print("[yellow]Permesso negato: rilancio con UAC...[/]")
            link_mod.elevate()
        raise
    for dlc, msg in results:
        console.print(f"  {dlc:10} {msg}")


def _safe(fn):
    try:
        fn()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    app()
