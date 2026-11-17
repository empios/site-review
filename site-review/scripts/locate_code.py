#!/usr/bin/env python3
"""Find where in the repo a finding lives. Never guesses: no hit -> null.

Usage: locate_code.py REPO --path /url/path --needle TEXT [--needle TEXT ...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_map import route_to_files  # noqa: E402

SEARCH_DIRS = ("src", "app", "pages", "components")
SKIP_DIRS = {"node_modules", ".next", "dist", "build", ".git", ".svelte-kit", ".astro", ".nuxt", ".output",
             "coverage", ".turbo", ".vercel"}
TEXT_EXT = {".tsx", ".ts", ".jsx", ".js", ".mjs", ".cjs", ".astro", ".vue", ".svelte", ".html", ".md", ".mdx",
            ".php", ".css", ".scss", ".json"}
MAX_FILE = 1024 * 1024


def _hits(repo: Path, rel: str, needles: list[str]) -> list[tuple[str, int]]:
    p = repo / rel
    try:
        if p.stat().st_size > MAX_FILE:
            return []
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for i, line in enumerate(lines, 1):
        if any(n and n in line for n in needles):
            out.append((rel, i))
    return out


def _walk(repo: Path):
    for f in sorted(repo.iterdir()):
        if f.is_file() and f.suffix in TEXT_EXT and f.name not in ("package.json", "package-lock.json"):
            yield f
    for d in SEARCH_DIRS:
        base = repo / d
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if f.is_file() and f.suffix in TEXT_EXT and not (set(f.relative_to(repo).parts) & SKIP_DIRS):
                yield f


def locate(repo: str, url_path: str, needles: list[str]) -> dict | None:
    r = Path(repo)
    needles = [n for n in needles if n and n.strip()]
    if not needles or not r.is_dir():
        return None
    route_hits = [h for rel in route_to_files(repo, url_path) for h in _hits(r, rel, needles)]
    if len({f for f, _ in route_hits}) == 1:
        f, line = route_hits[0]
        return {"file": f, "line": line, "confidence": "pewne", "candidates": [f"{f}:{line}"]}
    seen: list[tuple[str, int]] = []
    for f in _walk(r):
        rel = str(f.relative_to(r))
        for h in _hits(r, rel, needles):
            if h[0] not in {s[0] for s in seen}:
                seen.append(h)
        if len(seen) >= 3:
            break
    if not seen:
        return None
    f, line = seen[0]
    return {"file": f, "line": line, "confidence": "prawdopodobne", "candidates": [f"{a}:{b}" for a, b in seen]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo")
    ap.add_argument("--path", default="/")
    ap.add_argument("--needle", action="append", default=[])
    a = ap.parse_args(argv)
    print(json.dumps(locate(a.repo, a.path, a.needle), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
