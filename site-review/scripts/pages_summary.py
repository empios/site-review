#!/usr/bin/env python3
"""Collect per-page measurements into RUN/pages.json.

Usage: pages_summary.py RUN

Page 0 (start page) reads RUN/speed.json and RUN/render_diff.json; page i >= 1 reads RUN/pages/<i>/speed.json
and RUN/pages/<i>/render_diff.json. Mobile layout metrics come from RUN/shots/<i>/metrics.json.
Missing measurements are null — modules and the report show them as "not measured", never as clean.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _lighthouse(speed: dict | None) -> dict | None:
    if not speed or not speed.get("mobile"):
        return None
    m = speed["mobile"]
    scores = (speed.get("lh_scores") or {}).get("mobile") or {}
    return {"performance": scores.get("performance", m.get("performance")),
            "accessibility": scores.get("accessibility"), "seo": scores.get("seo"),
            "best_practices": scores.get("best-practices"),
            "lcp_ms": m.get("lcp_ms"), "cls": m.get("cls"), "tbt_ms": m.get("tbt_ms"), "runs": m.get("runs"),
            "findings": [f.get("id") for f in speed.get("findings") or []]}


def summarize(run: Path) -> list[dict]:
    basics = _load(run / "basics.json") or {}
    out = []
    for i, page in enumerate(basics.get("pages") or []):
        base = run if i == 0 else run / "pages" / str(i)
        speed = _load(base / "speed.json")
        render = _load(base / "render_diff.json")
        metrics = (_load(run / "shots" / str(i) / "metrics.json") or {}).get("375")
        out.append({
            "index": i,
            "url": page.get("url"),
            "status": page.get("status"),
            "title": (page.get("meta") or {}).get("title"),
            "lighthouse": _lighthouse(speed),
            "render_ratio": render.get("ratio") if render and render.get("available") else None,
            "missing_in_raw": render.get("missing_in_raw") if render and render.get("available") else None,
            "mobile": {k: metrics.get(k) for k in ("innerWidth", "horizontalScroll", "invisibleElements")}
            if metrics else None,
            "trackers_before_consent": (speed or {}).get("trackers_before_consent"),
            "external_fonts_before_consent": (speed or {}).get("external_fonts_before_consent"),
            "analytics_detected": (speed or {}).get("analytics_detected"),
            "data_dir": str(base.relative_to(run)) if base != run else ".",
        })
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    run = Path(argv[0])
    pages = summarize(run)
    (run / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    measured = sum(1 for p in pages if p["lighthouse"])
    print(json.dumps({"pages": len(pages), "with_lighthouse": measured}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
