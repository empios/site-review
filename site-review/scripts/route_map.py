"""Map a URL path to the source files that render it (file-based routers)."""
from __future__ import annotations

import json
from pathlib import Path

PAGE_EXT = {".tsx", ".ts", ".jsx", ".js", ".mdx", ".md", ".astro", ".vue", ".svelte"}


def _deps(repo: Path) -> dict:
    try:
        pkg = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}


def _first_dir(repo: Path, *cands: str) -> Path | None:
    for c in cands:
        if (repo / c).is_dir():
            return repo / c
    return None


def detect_framework(repo: str) -> str:
    r = Path(repo)
    d = _deps(r)
    if "next" in d:
        return "next-app" if _first_dir(r, "app", "src/app") else "next-pages"
    if "astro" in d:
        return "astro"
    if "@sveltejs/kit" in d:
        return "sveltekit"
    if "nuxt" in d:
        return "nuxt"
    if "vite" in d and "react" in d:
        return "vite-react"
    return "unknown"


def _routes_root(r: Path, fw: str) -> Path | None:
    return {
        "next-app": lambda: _first_dir(r, "app", "src/app"),
        "next-pages": lambda: _first_dir(r, "pages", "src/pages"),
        "astro": lambda: _first_dir(r, "src/pages"),
        "sveltekit": lambda: _first_dir(r, "src/routes"),
        "nuxt": lambda: _first_dir(r, "pages", "app/pages"),
    }.get(fw, lambda: None)()


def _is_page(fw: str, p: Path) -> bool:
    if p.suffix not in PAGE_EXT:
        return False
    if fw == "next-app":
        return p.stem == "page"
    if fw == "sveltekit":
        return p.name.startswith("+page") and p.suffix == ".svelte"
    if fw == "next-pages":
        return not p.stem.startswith("_") and "api" not in p.parts
    return True


def _segments(fw: str, root: Path, page: Path) -> list[str]:
    rel = list(page.relative_to(root).parts)
    if fw in ("next-app", "sveltekit"):
        segs = rel[:-1]
    else:
        stem = Path(rel[-1]).stem
        segs = rel[:-1] + ([] if stem == "index" else [stem])
    return [s for s in segs if not (s.startswith("(") and s.endswith(")")) and not s.startswith("@")]


def _match(pattern: list[str], parts: list[str]) -> int | None:
    """Return a specificity score (higher = more static) or None when it does not match."""
    if not pattern:
        return 0 if not parts else None
    head, rest = pattern[0], pattern[1:]
    if head.startswith("[[...") or head.startswith("[..."):
        min_len = 0 if head.startswith("[[") else 1
        for k in range(len(parts), min_len - 1, -1):
            sub = _match(rest, parts[k:])
            if sub is not None:
                return sub
        return None
    if not parts:
        return None
    if head.startswith("[") and head.endswith("]"):
        sub = _match(rest, parts[1:])
        return None if sub is None else sub + 1
    if head == parts[0]:
        sub = _match(rest, parts[1:])
        return None if sub is None else sub + 10
    return None


def route_to_files(repo: str, path: str) -> list[str]:
    r = Path(repo)
    fw = detect_framework(repo)
    root = _routes_root(r, fw)
    if root is None:
        return []
    parts = [p for p in path.split("?")[0].split("#")[0].split("/") if p]
    best: tuple[int, Path] | None = None
    for page in sorted(root.rglob("*")):
        if not page.is_file() or not _is_page(fw, page) or "node_modules" in page.parts:
            continue
        score = _match(_segments(fw, root, page), parts)
        if score is not None and (best is None or score > best[0]):
            best = (score, page)
    if best is None:
        return []
    files = [best[1]]
    if fw in ("next-app", "sveltekit"):
        d = best[1].parent
        while True:
            for lay in sorted(d.glob("layout.*" if fw == "next-app" else "+layout.svelte")):
                files.append(lay)
            if d == root:
                break
            d = d.parent
    return [str(f.relative_to(r)) for f in files]
