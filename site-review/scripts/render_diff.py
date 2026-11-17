#!/usr/bin/env python3
"""Compare raw HTML with the JS-rendered DOM (content visible only after JS).

Usage: render_diff.py URL --raw FILE --out DIR   -> DIR/render_diff.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_basics import parse_meta  # noqa: E402

HERE = Path(__file__).resolve().parent
SKIP_TAGS = {"script", "style", "noscript", "template", "head"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def _words(html: str) -> int:
    p = _Text()
    try:
        p.feed(html)
        p.close()
    except Exception:
        pass
    return len(re.findall(r"\w+", " ".join(p.parts)))


def _present(meta: dict) -> set[str]:
    out = set()
    if meta.get("title"):
        out.add("title")
    if meta.get("description"):
        out.add("description")
    if meta.get("canonical"):
        out.add("canonical")
    if meta.get("h1_count"):
        out.add("h1")
    return out


def compare(raw_html: str, rendered_html: str) -> dict:
    rw, nw = _words(raw_html), _words(rendered_html)
    ratio = 1.0 if nw == 0 else round(min(rw / nw, 1.0), 3)
    missing = _present(parse_meta(rendered_html)) - _present(parse_meta(raw_html))
    order = ["title", "description", "canonical", "h1"]
    return {"raw_words": rw, "rendered_words": nw, "ratio": ratio,
            "missing_in_raw": [x for x in order if x in missing]}


def to_findings(diff: dict, url: str) -> list[dict]:
    out = []
    if diff["rendered_words"] > 0 and diff["ratio"] < 0.5:
        out.append({
            "id": "seo-content-js-only", "module": "seo", "tags": ["seo", "code"], "severity": "high",
            "title": "Większość treści pojawia się dopiero po uruchomieniu JavaScriptu",
            "url": url,
            "evidence": {"type": "measurement",
                         "detail": f"surowy HTML: {diff['raw_words']} słów, po renderowaniu: {diff['rendered_words']} "
                                   f"(stosunek {diff['ratio']})"},
            "fix": "Renderuj treść po stronie serwera (SSR/SSG) albo prerenderuj kluczowe strony.",
            "impact": 3, "effort": "L", "source": "render_diff",
        })
    for el in diff["missing_in_raw"]:
        out.append({
            "id": f"seo-{el}-js-only", "module": "seo", "tags": ["seo", "code"], "severity": "medium",
            "title": f"Element {el} istnieje tylko po renderowaniu JS",
            "url": url,
            "evidence": {"type": "dom", "detail": f"{el} obecny w wyrenderowanym DOM, brak w surowym HTML"},
            "fix": f"Wstaw {el} w HTML generowanym na serwerze (metadane frameworka).",
            "impact": 2, "effort": "M", "source": "render_diff",
        })
    return out


def _dump_dom(url: str, timeout: int) -> subprocess.CompletedProcess:
    """Run Chrome --dump-dom in its own process group so a timeout kills Chrome and all its children."""
    cmd = ["bash", str(HERE / "chrome.sh"), "--headless=new", "--disable-gpu", "--virtual-time-budget=8000",
           "--dump-dom", url]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=120, help="seconds before giving up on Chrome")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    result: dict
    try:
        res = _dump_dom(a.url, a.timeout)
    except subprocess.TimeoutExpired:
        res = None
        result = {"available": False, "error": f"timeout: Chrome nie zwrócił DOM w {a.timeout} s", "findings": []}
    except OSError as e:
        res = None
        result = {"available": False, "error": f"{type(e).__name__}: {e}", "findings": []}
    if res is None:
        pass
    elif res.returncode != 0 or not res.stdout.strip():
        result = {"available": False, "error": (res.stderr or "pusty DOM").strip()[-500:], "findings": []}
    else:
        diff = compare(a.raw.read_text(encoding="utf-8"), res.stdout)
        result = {"available": True, **diff, "findings": to_findings(diff, a.url)}
    (a.out / "render_diff.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "findings"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
