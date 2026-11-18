#!/usr/bin/env python3
"""Merge module outputs into findings.json and report.json.

Usage: merge_findings.py --run DIR [--repo PATH] [--prev FILE]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import findings as fnd  # noqa: E402
import recheck  # noqa: E402
import scoring  # noqa: E402


def page_coverage(run: Path, merged: list[dict], modules: dict, checked: dict) -> list[dict]:
    """Per page and module: number of confirmed findings, "bez uwag" (checked, clean), "nie sprawdzono", "pominięty"."""
    ctx_path, pages_path = run / "context.json", run / "pages.json"
    ctx = json.loads(ctx_path.read_text(encoding="utf-8")) if ctx_path.is_file() else {}
    measured = {recheck.normalize_url(p.get("url")): p
                for p in (json.loads(pages_path.read_text(encoding="utf-8")) if pages_path.is_file() else [])}
    urls = ctx.get("pages") or [p.get("url") for p in measured.values()]
    confirmed = [f for f in merged if f.get("confidence") == fnd.CONFIRMED]
    out = []
    for url in urls:
        key = recheck.normalize_url(url)
        info = measured.get(key, {})
        row = {"url": url, "title": info.get("title"), "status": info.get("status"),
               "lighthouse": info.get("lighthouse"), "mobile": info.get("mobile"), "modules": {}}
        for m in fnd.MODULES:
            if modules.get(m, {}).get("depth") == scoring.SKIPPED:
                row["modules"][m] = "pominięty"
                continue
            n = sum(1 for f in confirmed if f.get("module") == m and recheck.normalize_url(f.get("url")) == key)
            row["modules"][m] = n if n else ("bez uwag" if key in checked.get(m, set()) else "nie sprawdzono")
        out.append(row)
    return out


def merge(run: Path, repo: str | None, prev: Path | None) -> dict:
    modules, raw, invalid, new_ids, checked = {}, [], [], {}, {}
    for path in sorted((run / "modules").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("module") or path.stem
        modules[name] = {"depth": data.get("depth", scoring.SKIPPED), "reason": data.get("reason")}
        if data.get("new_ids"):
            new_ids[name] = sorted(set(data["new_ids"]))
        checked[name] = {recheck.normalize_url(u) for u in data.get("pages_checked") or []}
        for f in data.get("findings") or []:
            errs = fnd.validate(f)
            if errs:
                invalid.append({"finding": f, "errors": errs})
            else:
                raw.append(fnd.apply_evidence_rule(f, repo))
    for m in fnd.MODULES:
        modules.setdefault(m, {"depth": scoring.SKIPPED, "reason": "moduł nie został uruchomiony"})

    merged = fnd.dedupe(raw)
    prev_list = json.loads(prev.read_text(encoding="utf-8")) if prev and prev.is_file() else None
    if prev_list:
        # Stable scores across runs: a problem seen before keeps its previous severity unless the module
        # says why it changed (severity_changed_reason). Judgement calls must not move the score by themselves.
        prev_sev = {recheck.key(p): p.get("severity") for p in prev_list if p.get("severity")}
        for f in merged:
            old = prev_sev.get(recheck.key(f))
            if old and old != f.get("severity") and not f.get("severity_changed_reason"):
                f["severity"] = old
                f["severity_kept_from_prev"] = True
    depth = {m: v["depth"] for m, v in modules.items()}
    scores = scoring.module_scores(merged, depth)
    quadrants: dict[str, list] = {"quick win": [], "duży projekt": [], "drobiazg": []}
    for f in merged:
        f["priority"] = scoring.priority(f)
        f["quadrant"] = scoring.quadrant(f)
        if f["confidence"] == fnd.CONFIRMED:
            quadrants[f["quadrant"]].append(f["id"])

    skipped = {m for m, v in modules.items() if v["depth"] == scoring.SKIPPED}
    audited = None
    ctx_path = run / "context.json"
    if ctx_path.is_file():
        pages = json.loads(ctx_path.read_text(encoding="utf-8")).get("pages")
        audited = set(pages) if pages else None
    report = {
        "pages": page_coverage(run, merged, modules, checked),
        "scores": scores,
        "overall": scoring.overall(scores),
        "top": scoring.top(merged),
        "quadrants": quadrants,
        "quick_wins": [{"id": f["id"], "title": f.get("title"), "url": f.get("url"), "fix": f.get("fix"),
                        "code_location": f.get("code_location")}
                       for f in scoring.top([f for f in merged if f["quadrant"] == "quick win"], 3)],
        "unverified": [f for f in merged if f["confidence"] != fnd.CONFIRMED],
        "invalid": invalid,
        "recheck": recheck.diff(prev_list, merged, skipped, audited) if prev_list is not None else None,
        "modules": modules,
        "new_ids": new_ids,
    }
    (run / "findings.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    (run / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--repo")
    ap.add_argument("--prev", type=Path)
    a = ap.parse_args(argv)
    r = merge(a.run, a.repo, a.prev)
    print(json.dumps({"overall": r["overall"], "invalid": len(r["invalid"]),
                      "unverified": len(r["unverified"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
