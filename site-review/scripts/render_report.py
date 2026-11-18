#!/usr/bin/env python3
"""Render report.json + findings.json into a single HTML page.

Usage: render_report.py --run DIR --summary FILE [--template FILE]  -> DIR/report.html
Everything that comes from the audited site or from findings is HTML-escaped.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "report-template.html"
EMBED_MAX = 300 * 1024
EMBED_TOTAL = 8 * 1024 * 1024
MODULE_NAMES = {"seo": "SEO i indeksacja", "speed": "Szybkość", "cro": "Marketing i konwersja",
                "design": "Design i dostępność", "code": "Kod", "pl": "Zgodność PL"}
SEV_NAMES = {"critical": "krytyczne", "high": "wysokie", "medium": "średnie", "low": "niskie"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def e(v) -> str:
    return escape("" if v is None else str(v), quote=True)


class _Embedder:
    def __init__(self, run_dir: str):
        self.root = Path(run_dir).resolve()
        self.used = 0

    def img(self, rel: str | None) -> str:
        if not rel:
            return ""
        target = (self.root / rel).resolve()
        inside = self.root in target.parents
        mime = MIME.get(target.suffix.lower())
        if inside and mime and target.is_file():
            size = target.stat().st_size
            if size <= EMBED_MAX and self.used + size <= EMBED_TOTAL:
                self.used += size
                data = base64.b64encode(target.read_bytes()).decode("ascii")
                return f'<img class="shot" alt="Zrzut ekranu" src="data:{mime};base64,{data}">'
        return f'<p class="kv"><b>Plik dowodu:</b> <code>{e(rel)}</code></p>'


def _score_class(score) -> str:
    if score is None:
        return "s-none"
    return "s-good" if score >= 90 else "s-warn" if score >= 50 else "s-bad"


def _finding(f: dict, emb: _Embedder, tag: str = "div") -> str:
    ev = f.get("evidence") or {}
    loc = f.get("code_location")
    chips = [f'<span class="chip sev-{e(f.get("severity"))}">{e(SEV_NAMES.get(f.get("severity"), f.get("severity")))}</span>',
             f'<span class="chip">{e(MODULE_NAMES.get(f.get("module"), f.get("module")))}</span>']
    if f.get("quadrant"):
        chips.append(f'<span class="chip">{e(f["quadrant"])}</span>')
    chips.append(f'<span class="chip">wpływ {e(f.get("impact"))} · wysiłek {e(f.get("effort"))}</span>')
    parts = [f'<{tag} class="finding">', f'<div class="chips">{"".join(chips)}</div>',
             f'<h3>{e(f.get("title"))}</h3>']
    if f.get("url"):
        parts.append(f'<p class="kv"><b>Gdzie:</b> <code>{e(f["url"])}</code></p>')
    if ev.get("detail"):
        parts.append(f'<p class="kv"><b>Dowód:</b> {e(ev["detail"])}</p>')
    if ev.get("path"):
        parts.append(emb.img(ev["path"]))
    if loc:
        cands = ", ".join(f"<code>{e(c)}</code>" for c in (loc.get("candidates") or [])[1:])
        extra = f" (inne możliwe: {cands})" if cands else ""
        parts.append(f'<p class="kv"><b>Kod:</b> <code>{e(loc.get("file"))}:{e(loc.get("line"))}</code>'
                     f' — {e(loc.get("confidence"))}{extra}</p>')
    parts.append(f'<p class="kv"><b>Poprawka:</b> {e(f.get("fix"))}</p>')
    parts.append(f'<p class="kv muted">Źródło: {e(f.get("source"))}</p>')
    parts.append(f"</{tag}>")
    return "".join(parts)


def _summary(report: dict, summary: str) -> str:
    ov = report.get("overall")
    head = f'<p class="overall {_score_class(ov)}">{e(ov if ov is not None else "—")}<span class="muted">/100</span></p>'
    paras = "".join(f"<p>{e(p.strip())}</p>" for p in summary.strip().split("\n\n") if p.strip())
    return head + paras


def _scorecards(report: dict) -> str:
    out = []
    for m, name in MODULE_NAMES.items():
        s = (report.get("scores") or {}).get(m) or {}
        mod = (report.get("modules") or {}).get(m) or {}
        score = s.get("score")
        depth = s.get("depth") or mod.get("depth") or "pominięty"
        label = "zgodność" if m == "pl" else "ocena"
        meta = f"{e(depth)} · {e(label)}"
        if mod.get("reason"):
            meta += f"<br>{e(mod['reason'])}"
        out.append(f'<div class="card"><div class="name">{e(name)}</div>'
                   f'<div class="score {_score_class(score)}">{e(score if score is not None else "—")}</div>'
                   f'<div class="meta">{meta} · {e(s.get("count", 0))} znal.</div></div>')
    return "".join(out)


def _top(report: dict, emb: _Embedder) -> str:
    items = report.get("top") or []
    if not items:
        return '<p class="muted">Brak potwierdzonych znalezisk.</p>'
    return '<ol class="top">' + "".join(_finding(f, emb, "li") for f in items) + "</ol>"


def _modules(findings: list[dict], emb: _Embedder) -> str:
    out = []
    confirmed = [f for f in findings if f.get("confidence") == "potwierdzone"]
    for m, name in MODULE_NAMES.items():
        mine = sorted((f for f in confirmed if f.get("module") == m),
                      key=lambda f: (-int(f.get("priority") or 0), str(f.get("id"))))
        body = "".join(_finding(f, emb) for f in mine) or '<p class="muted">Brak znalezisk.</p>'
        out.append(f"<details><summary>{e(name)} ({len(mine)})</summary>{body}</details>")
    return "".join(out)


def _unverified(report: dict, emb: _Embedder) -> str:
    items = report.get("unverified") or []
    if not items:
        return '<p class="muted">Brak.</p>'
    return "".join(_finding(f, emb) for f in items)


def _method(report: dict, ctx: dict) -> str:
    rows = []
    for m, name in MODULE_NAMES.items():
        mod = (report.get("modules") or {}).get(m) or {}
        rows.append(f"<tr><td>{e(name)}</td><td>{e(mod.get('depth'))}</td><td>{e(mod.get('reason') or '')}</td></tr>")
    parts = ['<div class="table-wrap"><table><thead><tr><th>Obszar</th><th>Głębokość</th><th>Uwagi</th></tr></thead>'
             f"<tbody>{''.join(rows)}</tbody></table></div>"]
    if ctx.get("pages"):
        parts.append("<p class=\"kv\"><b>Sprawdzone strony:</b> " +
                     ", ".join(f"<code>{e(p)}</code>" for p in ctx["pages"]) + "</p>")
    if ctx.get("available_skills"):
        parts.append("<p class=\"kv\"><b>Użyte skille:</b> " + e(", ".join(ctx["available_skills"])) + "</p>")
    for note in ctx.get("notes") or []:
        parts.append(f'<p class="kv">{e(note)}</p>')
    inv = report.get("invalid") or []
    if inv:
        parts.append(f'<p class="kv muted">Odrzucone niepoprawne znaleziska: {len(inv)}.</p>')
    parts.append('<p class="kv muted">Ocena obszaru = 100 − kary (krytyczne 25, wysokie 10, średnie 4, niskie 1). '
                 "Wynik ogólny: średnia ważona (SEO 25, szybkość 20, marketing 20, design 20, kod 15); "
                 "obszary pominięte i zgodność PL poza średnią. Moduł PL nie jest poradą prawną.</p>")
    return "".join(parts)


def _recheck(report: dict) -> str:
    rc = report.get("recheck")
    if not rc:
        return ""
    fixed = "".join(f"<li>{e(f.get('title') or f.get('id'))}</li>" for f in rc.get("fixed") or [])
    return ('<section id="sec-recheck"><h2>Zmiany od poprzedniego audytu</h2><div class="chips">'
            f'<span class="chip s-good">Naprawione: {len(rc.get("fixed") or [])}</span>'
            f'<span class="chip">Nadal: {len(rc.get("still") or [])}</span>'
            f'<span class="chip s-bad">Nowe: {len(rc.get("new") or [])}</span>'
            f'<span class="chip">Nie sprawdzono: {len(rc.get("unchecked") or [])}</span></div>'
            + (f"<ul>{fixed}</ul>" if fixed else "") + "</section>")


def render(report: dict, findings: list[dict], summary: str, template: str, run_dir: str) -> str:
    ctx_path = Path(run_dir) / "context.json"
    try:
        ctx = json.loads(ctx_path.read_text(encoding="utf-8")) if ctx_path.is_file() else {}
    except ValueError:
        ctx = {}
    host = urlparse(ctx.get("url") or "").netloc or "strony"
    emb = _Embedder(run_dir)
    parts = {
        "title": e(f"Audyt {host}"),
        "subtitle": e(" · ".join(x for x in [ctx.get("url"), ctx.get("date")] if x)),
        "summary": _summary(report, summary),
        "recheck": _recheck(report),
        "scorecards": _scorecards(report),
        "top": _top(report, emb),
        "modules": _modules(findings, emb),
        "unverified": _unverified(report, emb),
        "method": _method(report, ctx),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: parts.get(m.group(1), ""), template)


def artifact_fragment(html: str) -> str:
    """The same page without <!doctype>/<html>/<head>/<body>: claude.ai Artifacts add their own skeleton."""
    title = re.search(r"<title>.*?</title>", html, re.S).group(0)
    style = re.search(r"<style>.*?</style>", html, re.S).group(0)
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    return f'{title}\n<meta name="claude:viewport-fit-sides" content="cover">\n{style}\n{body.strip()}\n'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    a = ap.parse_args(argv)
    report = json.loads((a.run / "report.json").read_text(encoding="utf-8"))
    findings = json.loads((a.run / "findings.json").read_text(encoding="utf-8"))
    html = render(report, findings, a.summary.read_text(encoding="utf-8"),
                  a.template.read_text(encoding="utf-8"), str(a.run))
    out = a.run / "report.html"
    out.write_text(html, encoding="utf-8")
    frag = a.run / "report.artifact.html"
    frag.write_text(artifact_fragment(html), encoding="utf-8")
    print(str(out))
    print(str(frag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
