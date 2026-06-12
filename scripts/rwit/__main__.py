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
import langcheck as langcheck_mod
import ledger as ledger_mod

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


@app.command("lang-check", help="Trova stringhe in lingua sbagliata (FR/ES/DE) - deterministico, offline.")
def lang_check(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
    min_conf: float = typer.Option(0.55, "--min-conf", help="Confidenza minima language-ID (Tier B)"),
    files: bool = typer.Option(False, "--files", help="Modalita FILE: interi file in lingua sbagliata (es. rulePack copiati)"),
):
    if files:
        rows = langcheck_mod.scan_files(dlc or None)
        t = Table(title=f"File in lingua sbagliata - {len(rows)}")
        t.add_column("Lingua"); t.add_column("%", justify="right")
        t.add_column("Stringhe", justify="right"); t.add_column("File")
        for rel, _dlc, n, frac, iso, _m in rows:
            t.add_row(iso, f"{frac*100:.0f}%", str(n), rel)
        console.print(t)
        return

    hits = langcheck_mod.scan(dlc or None, min_conf=min_conf)

    # Commenti EN adiacenti per la shortlist (best-effort, per la review).
    by_verdict: dict[str, int] = {}
    for h in hits:
        kind = h.verdict.split("=")[0].split("-")[0]  # copia | lingua
        by_verdict[h.verdict] = by_verdict.get(h.verdict, 0) + 1

    t = Table(title=f"Lingua sbagliata - {len(hits)} stringhe sospette")
    t.add_column("Verdetto")
    t.add_column("Conteggio", justify="right", style="bold")
    for v, n in sorted(by_verdict.items(), key=lambda kv: -kv[1]):
        t.add_row(v, str(n))
    console.print(t)

    out = config.reports_dir() / f"langcheck_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# lang-check - {len(hits)} stringhe sospette\n"]
    cur = None
    for h in sorted(hits, key=lambda h: (h.file, h.line or 0)):
        if h.file != cur:
            lines.append(f"\n=== {h.file} ===")
            cur = h.file
        lines.append(f"  L{h.line:<5} [{h.verdict} {h.detail}] {h.tag}")
        if h.en:
            lines.append(f"     EN: {h.en}")
        lines.append(f"     IT: {h.text}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")


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


ledger_app = typer.Typer(no_args_is_help=True, help="Registro versionato delle traduzioni (stato + hash, git-friendly).")
app.add_typer(ledger_app, name="ledger")


@ledger_app.command("build", help="(Ri)costruisce/fonde il ledger CSV preservando le validazioni.")
def ledger_build(dlc: Optional[List[str]] = typer.Option(None, "--dlc")):
    counts = ledger_mod.build(dlc or None)
    t = Table(title="Ledger - stringhe per stato")
    t.add_column("Stato")
    t.add_column("Conteggio", justify="right", style="bold")
    for s, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        t.add_row(s, str(n))
    console.print(t)
    console.print(f"[green]Ledger:[/] {ledger_mod.LEDGER}")


@ledger_app.command("stats", help="Conteggi per stato e per DLC dal ledger esistente.")
def ledger_stats():
    rows = list(ledger_mod.load().values())
    if not rows:
        console.print("[yellow]Ledger vuoto: esegui prima 'rwit ledger build'.[/]")
        raise typer.Exit(1)
    from collections import Counter
    by_state = Counter(r["status"] for r in rows)
    t = Table(title=f"Ledger - {len(rows)} stringhe")
    t.add_column("Stato"); t.add_column("Conteggio", justify="right", style="bold")
    for s, n in by_state.most_common():
        t.add_row(s, str(n))
    console.print(t)


@ledger_app.command("report", help="Genera un dashboard HTML del progresso (apribile nel browser).")
def ledger_report(
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Apri nel browser"),
):
    if not ledger_mod.LEDGER.exists():
        console.print("[yellow]Ledger vuoto: esegui prima 'rwit ledger build'.[/]")
        raise typer.Exit(1)
    out = config.reports_dir() / "dashboard.html"
    ledger_mod.report_html(out, f"{datetime.now():%Y-%m-%d %H:%M}")
    console.print(f"[green]Dashboard:[/] {out}")
    if open_browser:
        import webbrowser
        webbrowser.open(out.as_uri())


@ledger_app.command("validate", help="Promuove a 'validated' (fissa la baseline degli hash).")
def ledger_validate(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Conferma senza prompt"),
):
    target = ", ".join(dlc) if dlc else "TUTTE le DLC"
    if not yes:
        console.print(f"[yellow]Marchero 'validated' le stringhe tradotte in: {target}.[/]")
        console.print("Rilancia con --yes per confermare.")
        raise typer.Exit(1)
    n = ledger_mod.validate(dlc or None)
    console.print(f"[green]Validate {n} stringhe.[/]")


@ledger_app.command("todo", help="Esporta la worklist (da tradurre/ritradurre) per LLM/tool esterno.")
def ledger_todo(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    status: Optional[List[str]] = typer.Option(None, "--status", help="Stati da includere (default: untranslated, stale)"),
):
    items = ledger_mod.todo(dlc or None, tuple(status) if status else ("untranslated", "stale"))
    out = config.reports_dir() / f"todo_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# worklist - {len(items)} stringhe da tradurre/ritradurre\n"]
    cur = None
    for it in items:
        if it["file"] != cur:
            lines.append(f"\n=== {it['file']} ==="); cur = it["file"]
        lines.append(f"  L{it['line']:<5} [{it['status']}{('/'+it['lang_flag']) if it.get('lang_flag') else ''}] {it['tag']}")
        if it["en"]:
            lines.append(f"     EN: {it['en']}")
        lines.append(f"     IT: {it['it']}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Worklist ({len(items)} voci):[/] {out}")


def _safe(fn):
    try:
        fn()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    app()
