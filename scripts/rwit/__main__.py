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
import stringsdiff as stringsdiff_mod
import variants as variants_mod
import reconcile as reconcile_mod
import freshness as freshness_mod
import argscheck as argscheck_mod
import pluralcheck as pluralcheck_mod
import syntaxcheck as syntaxcheck_mod
import gendercheck as gendercheck_mod
import clean as clean_mod
import report as report_mod
import stripbasedesc as stripbasedesc_mod

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
    if gap.def_phantom:
        console.print(f"[dim]({gap.def_phantom} voci 'fantasma' escluse: cache runtime "
                      f"unlockedRolesCachedFor / requiredMemeList, non traducibili)[/]")

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


@app.command("reconcile", help="Riconciliazione riga-per-riga delle liste Words con l'inglese: glosse/non tradotte/mancanti.")
def reconcile_cmd(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    fix_glosses: bool = typer.Option(False, "--fix-glosses", help="Rimuove le glosse tra parentesi (deterministico)"),
    game_data: Optional[str] = typer.Option(None, "--game-data"),
):
    if fix_glosses:
        n = reconcile_mod.fix_glosses(dlc or None)
        console.print(f"[green]Glosse rimosse da {n} voci.[/]")
        return
    rows = reconcile_mod.scan(dlc or None, game_data)
    from collections import Counter
    tally = Counter(kind for _d, _r, issues in rows for _ln, kind, _w, _f in issues)
    t = Table(title=f"Reconcile liste Words (vs inglese) - {len(rows)} file")
    t.add_column("Problema"); t.add_column("Conteggio", justify="right", style="bold")
    for k, c in tally.most_common():
        t.add_row(k, str(c))
    console.print(t)
    out = config.reports_dir() / f"reconcile_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# reconcile vs inglese del gioco - {len(rows)} file\n"]
    for dlc_, rel, issues in sorted(rows, key=lambda r: (r[0], r[1])):
        lines.append(f"\n=== {dlc_}/Strings/{rel} ===")
        for ln, kind, w, fix in issues:
            extra = f"  ->  {fix}" if fix else ""
            lines.append(f"  L{ln:<4} [{kind:7}] {w}{extra}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")


@app.command("strings-diff", help="Confronta i file Strings (Words/Names) con l'inglese del gioco: mancanti/non tradotti/incompleti.")
def strings_diff(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    game_data: Optional[str] = typer.Option(None, "--game-data"),
):
    rows = stringsdiff_mod.diff(dlc or None, game_data)
    from collections import Counter
    by = Counter(r[2] for r in rows)
    t = Table(title=f"Strings da sistemare (vs inglese del gioco) - {len(rows)}")
    t.add_column("Stato"); t.add_column("Conteggio", justify="right", style="bold")
    for s, n in by.most_common():
        t.add_row(s, str(n))
    console.print(t)
    out = config.reports_dir() / f"stringsdiff_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# strings-diff vs inglese del gioco - {len(rows)} file\n"]
    for dlc_, rel, st_, n_en, n_it in sorted(rows, key=lambda r: (r[0], r[2], r[1])):
        lines.append(f"  [{st_:9}] {dlc_}/Strings/{rel}  (EN={n_en} IT={n_it})")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")


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


@app.command("freshness", help="Freschezza liste Words: IT vs inglese del gioco + varianti di genere vs base.")
def freshness_cmd(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    game_data: Optional[str] = typer.Option(None, "--game-data", help="Cartella Data del gioco"),
):
    base_issues, var_issues, has_game = freshness_mod.check(dlc or None, game_data)
    if not has_game:
        console.print("[yellow]Gioco non trovato: salto il confronto con l'inglese "
                      "(usa --game-data o RIMWORLD_DATA). Controllo solo le varianti.[/]")

    t1 = Table(title="Base IT vs inglese del gioco  (EURISTICO: differenze spesso "
                     "benigne - sinonimi che collassano, liste riordinate, voci tenute "
                     "in inglese. Verificare il CONTENUTO prima di agire.)")
    t1.add_column("DLC"); t1.add_column("file"); t1.add_column("IT", justify="right")
    t1.add_column("EN", justify="right"); t1.add_column("", justify="left")
    for dlc, rel, it_n, en_n in base_issues:
        flag = "[red]indietro[/]" if it_n < en_n else "[yellow]in eccesso[/]"
        t1.add_row(dlc, rel, str(it_n), str(en_n), flag)
    if base_issues:
        console.print(t1)

    t2 = Table(title="Varianti di genere vs base (stale)")
    t2.add_column("DLC"); t2.add_column("file"); t2.add_column("base", justify="right")
    t2.add_column("M", justify="right"); t2.add_column("F", justify="right")
    t2.add_column("manca", justify="right")
    for dlc, rel, base, m, f, total in var_issues:
        t2.add_row(dlc, rel, str(base), str(m), str(f), str(base - total))
    if var_issues:
        console.print(t2)

    if not base_issues and not var_issues:
        console.print("[green]Tutto fresco: nessuna divergenza.[/]")
    else:
        console.print(f"[bold]{len(base_issues)} liste base divergenti, "
                      f"{len(var_issues)} varianti stale.[/]")


@app.command("args-check", help="Trova segnaposto {...} discordanti fra IT ed EN (es. {0} residuo che appare a schermo).")
def args_check(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
):
    hits = argscheck_mod.scan(dlc or None)
    from collections import Counter
    by = Counter(h.kind for h in hits)
    t = Table(title=f"Segnaposto discordanti IT vs EN - {len(hits)} stringhe")
    t.add_column("Tipo"); t.add_column("Conteggio", justify="right", style="bold")
    labels = {"extra-pos": "posizionale IN PIU' nell'IT (es. {0} residuo) — BUG probabile",
              "manca-pos": "posizionale MANCANTE nell'IT — BUG probabile",
              "manca-var": "variabile {NOME} di contenuto MANCANTE — da rivedere",
              "extra-var": "variabile {NOME} IN PIU' (spesso nome al posto del pronome: lecito)"}
    for k, n in by.most_common():
        t.add_row(labels.get(k, k), str(n))
    console.print(t)
    if not hits:
        console.print("[green]Nessuna discordanza di segnaposto.[/]")
        return
    out = config.reports_dir() / f"argscheck_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# args-check - {len(hits)} stringhe con segnaposto discordanti\n"]
    cur = None
    for h in sorted(hits, key=lambda h: (h.file, h.line or 0)):
        if h.file != cur:
            lines.append(f"\n=== {h.file} ==="); cur = h.file
        diff = []
        if h.extra_num: diff.append(f"+pos{{{','.join(h.extra_num)}}}")
        if h.miss_num:  diff.append(f"-pos{{{','.join(h.miss_num)}}}")
        if h.extra_var: diff.append(f"+var{{{','.join(h.extra_var)}}}")
        if h.miss_var:  diff.append(f"-var{{{','.join(h.miss_var)}}}")
        lines.append(f"  L{h.line:<5} [{' '.join(diff)}] {h.tag}")
        lines.append(f"     EN: {h.en}")
        lines.append(f"     IT: {h.it}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio (+ = in piu' nell'IT, - = mancante):[/] {out}")


@app.command("plural-check", help="Trova il plurale inglese [Simbolo]s nelle regole IT (es. 'razzos'/'cittadinos' a schermo).")
def plural_check(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
):
    hits = pluralcheck_mod.scan(dlc or None)
    console.print(f"[bold]Plurale inglese [..]s nelle stringhe IT:[/] {len(hits)} stringhe")
    if not hits:
        console.print("[green]Nessun plurale inglese residuo.[/]")
        return
    out = config.reports_dir() / f"pluralcheck_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# plural-check - {len(hits)} stringhe IT con plurale inglese [..]s\n"]
    cur = None
    for h in sorted(hits, key=lambda h: (h.file, h.line or 0)):
        if h.file != cur:
            lines.append(f"\n=== {h.file} ==="); cur = h.file
        syms = ", ".join("[" + s + "]s" for s in h.symbols) or "?"
        lines.append(f"  L{(h.line or 0):<5} {h.tag}")
        lines.append(f"     simboli: {syms}")
        lines.append(f"     IT: {h.it}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")


@app.command("clean", help="Voci morte dal TranslationReport: keyed inutili (rimovibili) + load-error def (diagnosi).")
def clean(
    report: Optional[Path] = typer.Option(None, "--report", "-r", help="Percorso del TranslationReport.txt"),
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
    game_data: Optional[str] = typer.Option(None, "--game-data"),
    apply_keyed: bool = typer.Option(False, "--apply-keyed", help="RIMUOVE le keyed orfane (assenti anche dall'inglese)"),
    apply_defs: bool = typer.Option(False, "--apply-defs", help="RIMUOVE le voci DefInjected dei load-error (iniezioni inerti)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Conferma la rimozione senza prompt"),
):
    rep_path = report or config.desktop_report()
    if not rep_path or not Path(rep_path).exists():
        console.print("[red]Report non trovato.[/] Generalo in gioco o passa --report.")
        raise typer.Exit(1)
    try:
        data = config.game_data(game_data)
    except FileNotFoundError:
        console.print("[red]Gioco non trovato[/] (serve l'inglese del gioco per l'incrocio): usa --game-data o RIMWORLD_DATA.")
        raise typer.Exit(1)

    dlcs = dlc or config.DLCS
    rep = report_mod.parse(rep_path)
    krows = clean_mod.scan_keyed(rep, dlcs, data)
    lrows = clean_mod.scan_load_errors(rep, dlcs)

    from collections import Counter
    kc = Counter(r.verdict for r in krows)
    t = Table(title=f"Keyed inutili - {len(krows)} (incrocio con l'inglese del gioco)")
    t.add_column("Verdetto"); t.add_column("Conteggio", justify="right", style="bold")
    vlabel = {"orfana": "orfana (assente anche in EN) -> RIMOVIBILE",
              "in-EN": "presente in EN -> falso positivo, TENERE",
              "assente": "gia' assente dal repo"}
    for v, n in kc.most_common():
        t.add_row(vlabel.get(v, v), str(n))
    console.print(t)

    lc = Counter(r.kind for r in lrows)
    if lrows:
        t2 = Table(title=f"Load-error def-injected - {len(lrows)} (solo diagnosi, rimappatura manuale)")
        t2.add_column("Tipo"); t2.add_column("Conteggio", justify="right", style="bold")
        for k, n in lc.most_common():
            t2.add_row(k, str(n))
        console.print(t2)

    out = config.reports_dir() / f"clean_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = ["# clean - keyed inutili + load-error def-injected\n"]
    lines.append("## KEYED INUTILI (orfana=rimovibile, in-EN=tenere, assente=gia' via)")
    cur = None
    for r in sorted(krows, key=lambda r: (r.verdict, r.rel or "", r.line or 0)):
        if r.verdict != cur:
            lines.append(f"\n### {r.verdict} ###"); cur = r.verdict
        loc = f"{r.rel}:{r.line}" if r.rel else "(non nel repo)"
        lines.append(f"  {r.key:40} {loc}")
        lines.append(f"     IT: {r.text}")
    lines.append("\n## LOAD-ERROR DEF-INJECTED (diagnosi)")
    cur = None
    for r in sorted(lrows, key=lambda r: (r.kind, r.rel or "")):
        if r.kind != cur:
            lines.append(f"\n### {r.kind} ###"); cur = r.kind
        loc = f"{r.rel}:{r.line}" if r.rel else f"(non in DefInjected repo; origine Defs: {r.src_file})"
        lines.append(f"  [{r.deftype}] {r.inject_path}")
        lines.append(f"     {r.detail}")
        lines.append(f"     repo: {loc}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")

    orphans = [r for r in krows if r.verdict == "orfana"]
    located_defs = [r for r in lrows if r.rel and r.line]
    if not apply_keyed and not apply_defs:
        if orphans:
            console.print(f"[bold]{len(orphans)} keyed orfane rimovibili.[/] "
                          f"Per rimuoverle: [cyan]rwit clean --apply-keyed --yes[/].")
        if located_defs:
            console.print(f"[bold]{len(located_defs)} voci DefInjected di load-error localizzate.[/] "
                          f"Per rimuoverle: [cyan]rwit clean --apply-defs --yes[/].")
        return
    if not yes:
        todo = []
        if apply_keyed:
            todo.append(f"{len(orphans)} keyed orfane")
        if apply_defs:
            todo.append(f"{len(located_defs)} voci DefInjected di load-error")
        console.print(f"[yellow]Rimuovero': {', '.join(todo)} (+ i commenti EN/UNUSED adiacenti).[/]")
        console.print("Rilancia con --yes per confermare. (git e' la rete di sicurezza)")
        raise typer.Exit(1)
    if apply_keyed:
        n, warns = clean_mod.apply_keyed(orphans)
        console.print(f"[green]Rimosse {n} voci keyed orfane.[/]")
        for w in warns:
            console.print(f"  [yellow]! {w}[/]")
    if apply_defs:
        n, warns = clean_mod.apply_defs(located_defs)
        console.print(f"[green]Rimosse {n} voci DefInjected di load-error.[/]")
        for w in warns:
            console.print(f"  [yellow]! {w}[/]")


@app.command("syntax-check", help="Linter sintassi motore: ternarie di genere + bilanciamento graffe/parentesi (rompono il parser).")
def syntax_check(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
):
    hits = syntaxcheck_mod.scan(dlc or None)
    from collections import Counter
    by = Counter(h.kind for h in hits)
    t = Table(title=f"Sintassi sospetta IT - {len(hits)} stringhe")
    t.add_column("Tipo"); t.add_column("Conteggio", justify="right", style="bold")
    labels = {"ternary-malformed": "ternaria di genere malformata (non 1?/1-2:)",
              "brace-unbalanced": "graffe {} sbilanciate",
              "bracket-unbalanced": "parentesi-simbolo [] sbilanciate"}
    for k, n in by.most_common():
        t.add_row(labels.get(k, k), str(n))
    console.print(t)
    if not hits:
        console.print("[green]Nessun problema di sintassi: ternarie e simboli ben formati.[/]")
        return
    out = config.reports_dir() / f"syntaxcheck_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# syntax-check - {len(hits)} stringhe con sintassi sospetta\n"]
    cur = None
    for h in sorted(hits, key=lambda h: (h.file, h.line or 0)):
        if h.file != cur:
            lines.append(f"\n=== {h.file} ==="); cur = h.file
        lines.append(f"  L{(h.line or 0):<5} [{h.kind}] {h.detail}")
        lines.append(f"     IT: {h.it}")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"[green]Dettaglio:[/] {out}")


@app.command("strip-basedesc", help="Rimuove le iniezioni morte *.baseDesc dalle BackstoryDef (il gioco 1.6 usa <description>). DRY-RUN salvo --apply.")
def strip_basedesc(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
    exclude: Optional[List[str]] = typer.Option(None, "--exclude", help="Salta file per nome (es. Solid_Child) - utile per non collidere con un'altra sessione"),
    apply: bool = typer.Option(False, "--apply", help="Scrive i file (default: solo anteprima)"),
):
    results = stripbasedesc_mod.run(dlc or None, set(exclude or []), apply=apply)
    total = sum(r.removed for r in results)
    mode = "RIMOSSE" if apply else "DA RIMUOVERE (anteprima)"
    t = Table(title=f"strip-basedesc - {total} righe {mode} in {len(results)} file")
    t.add_column("File"); t.add_column("baseDesc", justify="right", style="bold")
    for r in sorted(results, key=lambda r: -r.removed):
        t.add_row(r.rel, str(r.removed))
    console.print(t)
    if not results:
        console.print("[green]Nessun baseDesc morto: BackstoryDef gia' pulite.[/]")
        return
    if apply:
        console.print(f"[green]Fatto:[/] rimosse {total} righe morte. Ricostruisci il ledger: rwit ledger build")
    else:
        console.print("[yellow]Anteprima.[/] Riesegui con [bold]--apply[/] per scrivere i file.")


@app.command("gender-check", help="Linter concordanza di genere: articolo/aggettivo FISSO davanti a costrutto che flette ({gender ? o:a}).")
def gender_check(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc", help="Limita a una o piu DLC"),
):
    hits = gendercheck_mod.scan(dlc or None)
    t = Table(title=f"Concordanza di genere sospetta IT - {len(hits)} stringhe")
    t.add_column("DLC"); t.add_column("Conteggio", justify="right", style="bold")
    from collections import Counter
    for d, n in Counter(h.dlc for h in hits).most_common():
        t.add_row(d, str(n))
    console.print(t)
    if not hits:
        console.print("[green]Nessun problema: nessun articolo/aggettivo fisso davanti a un costrutto flesso.[/]")
        return
    out = config.reports_dir() / f"gendercheck_{datetime.now():%Y%m%d_%H%M}.txt"
    lines = [f"# gender-check - {len(hits)} stringhe con concordanza di genere sospetta\n"]
    cur = None
    for h in sorted(hits, key=lambda h: (h.file, h.line or 0)):
        if h.file != cur:
            lines.append(f"\n=== {h.file} ==="); cur = h.file
        lines.append(f"  L{(h.line or 0):<5} [{h.kind}] {h.detail}")
        lines.append(f"     IT: {h.it}")
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
    # avviso freschezza: liste base divergenti dal gioco / varianti di genere stale
    try:
        bi, vi, _ = freshness_mod.check(dlc or None)
        if vi:
            console.print(f"[yellow]⚠ Freschezza: {len(vi)} varianti di genere STALE "
                          f"(azionabile). Dettagli: [bold]rwit freshness[/].[/]")
        if bi:
            console.print(f"[dim]i {len(bi)} scostamenti base vs gioco sono euristici "
                          f"(spesso sinonimi/ordinamento): verificare il contenuto.[/]")
    except Exception:  # noqa: BLE001 - l'avviso non deve mai far fallire il build
        pass


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


@ledger_app.command("validate", help="Promuove a 'validated' (fissa la baseline degli hash). Filtra con --file/--tag per validare solo cio' che hai rivisto.")
def ledger_validate(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    file: Optional[List[str]] = typer.Option(None, "--file", help="Solo i file che combaciano (sottostringa, ripetibile)"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", help="Solo i tag che combaciano (sottostringa, ripetibile)"),
    list_only: bool = typer.Option(False, "--list", help="Elenca le voci ANCORA da validare (translated/modified) e esci, senza validare"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Conferma senza prompt"),
):
    if file or tag or list_only:
        keys = ledger_mod.keys_matching(files=file, tags=tag, dlcs=dlc or None)
        if list_only:
            console.print(f"[cyan]{len(keys)} voci ancora da validare[/] (translated/modified):")
            for _d, _f, tg in keys:
                console.print(f"  {tg}")
            return
        if not keys:
            console.print("[yellow]Nessuna riga 'translated'/'modified' combacia coi filtri.[/]")
            raise typer.Exit(1)
        if not yes:
            filt = f"file={file or '*'} tag={tag or '*'}" + (f" dlc={dlc}" if dlc else "")
            console.print(f"[yellow]Marchero 'validated' {len(keys)} righe ({filt}).[/]")
            console.print("Rilancia con --yes per confermare.")
            raise typer.Exit(1)
        n = ledger_mod.set_status_keys(keys, "validated")
        console.print(f"[green]Validate {n} stringhe.[/]")
        return
    target = ", ".join(dlc) if dlc else "TUTTE le DLC"
    if not yes:
        console.print(f"[yellow]Marchero 'validated' le stringhe tradotte in: {target}.[/]")
        console.print("Rilancia con --yes per confermare.")
        raise typer.Exit(1)
    n = ledger_mod.validate(dlc or None)
    console.print(f"[green]Validate {n} stringhe.[/]")


@ledger_app.command("keep", help="Marca come 'keep' (da NON tradurre: prestiti, nomi propri, sigle) le voci attualmente 'untranslated'.")
def ledger_keep(
    dlc: Optional[List[str]] = typer.Option(None, "--dlc"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Conferma senza prompt"),
):
    target = ", ".join(dlc) if dlc else "TUTTE le DLC"
    if not yes:
        console.print(f"[yellow]Marchero 'keep' (da-non-tradurre) le voci 'untranslated' in: {target}.[/]")
        console.print("Sono le stringhe IT == EN gia riviste (prestiti/nomi propri/format).")
        console.print("Rilancia con --yes per confermare.")
        raise typer.Exit(1)
    n = ledger_mod.set_keep(dlc or None)
    console.print(f"[green]Marcate 'keep' {n} stringhe (escluse dal worklist e contate come completate).[/]")


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


variants_app = typer.Typer(no_args_is_help=True, help="Genera le varianti morfologiche (genere/numero/articolo) via Morph-it!.")
app.add_typer(variants_app, name="variants")


@variants_app.command("adj", help="Genera i 5 file aggettivo (base + m/f x sing/plur) dai lemmi.")
def variants_adj(name: str, dlc: str = typer.Option("Core", "--dlc")):
    if not __import__("morphit").available():
        console.print("[yellow]Morph-it! assente in scripts/.tools/ — uso solo le regole.[/]")
    fb = variants_mod.gen_adjective(name, dlc)
    console.print(f"[green]Generato:[/] {dlc}/Strings/Words/Adjectives/{name}[*].txt")
    if fb:
        console.print(f"[yellow]Fallback a regole ({len(fb)}, da rivedere):[/] {', '.join(fb)}")


@variants_app.command("noun", help="Genera i bucket nome per articolo del plurale (I/Gli/Le) dai lemmi.")
def variants_noun(name: str, dlc: str = typer.Option("Core", "--dlc")):
    fb = variants_mod.gen_noun(name, dlc)
    console.print(f"[green]Generato:[/] {dlc}/Strings/Words/Nouns/{name}_(I|Gli|Le).txt")
    if fb:
        console.print(f"[yellow]Fallback a regole ({len(fb)}, da rivedere):[/] {', '.join(fb)}")


@variants_app.command("noun-gender", help="Spezza una lista nomi (singolari) per genere: _Singular_Masculine/_Feminine.")
def variants_noun_gender(name: str, dlc: str = typer.Option("Core", "--dlc")):
    if not __import__("morphit").available():
        console.print("[yellow]Morph-it! assente in scripts/.tools/ — uso solo le regole.[/]")
    fb = variants_mod.gen_noun_gender(name, dlc)
    console.print(f"[green]Generato:[/] {dlc}/Strings/Words/Nouns/{name}_Singular_(Masculine|Feminine).txt")
    if fb:
        console.print(f"[yellow]Fallback a regole ({len(fb)}, da rivedere):[/] {', '.join(fb)}")


@variants_app.command("def-article", help="Dai bucket di genere (_Male/_Female) crea i bucket per articolo determinativo singolare: _Def_Il/Lo/La/L.")
def variants_def_article(name: str, dlc: str = typer.Option("Core", "--dlc")):
    counts = variants_mod.gen_def_article(name, dlc)
    console.print(f"[green]Generato:[/] {dlc}/Strings/Words/Nouns/{name}_Def_(Il|Lo|La|L).txt")
    console.print(f"  conteggi (per pesare le <li>): {counts}")


def _safe(fn):
    try:
        fn()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    app()
