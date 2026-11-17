#!/usr/bin/env python3
"""Median of Lighthouse runs + speed findings.

Usage: lh_median.py DIR --url URL   (reads DIR/lh-{mobile,desktop}-N.json, writes DIR/speed.json)
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trackers  # noqa: E402

METRICS = {"lcp_ms": "largest-contentful-paint", "cls": "cumulative-layout-shift",
           "tbt_ms": "total-blocking-time", "fcp_ms": "first-contentful-paint", "si_ms": "speed-index"}
# (metric, needs-improvement threshold, poor threshold, label, fix)
THRESHOLDS = [
    ("lcp", "lcp_ms", 2500, 4000, "LCP",
     "Przyspiesz wyświetlenie największego elementu pierwszego ekranu: sprawdź, co go opóźnia "
     "(czas serwera, blokujące CSS/fonty, wielkość obrazu) i usuń największe opóźnienie."),
    ("cls", "cls", 0.1, 0.25, "CLS", "Zarezerwuj miejsce na obrazy, reklamy i fonty (width/height, aspect-ratio)."),
    ("tbt", "tbt_ms", 200, 600, "TBT", "Ogranicz JavaScript na starcie: dziel bundle, odrocz skrypty zewnętrzne."),
]


def _valid(rep: dict) -> bool:
    try:
        if rep.get("runtimeError"):
            return False
        float(rep["categories"]["performance"]["score"])
        return all(rep["audits"][a]["numericValue"] is not None for a in METRICS.values())
    except (KeyError, TypeError, ValueError):
        return False


def median_run(reports: list[dict]) -> dict | None:
    ok = [r for r in reports if isinstance(r, dict) and _valid(r)]
    if not ok:
        return None
    out = {"performance": round(statistics.median(r["categories"]["performance"]["score"] for r in ok) * 100)}
    for key, audit in METRICS.items():
        v = statistics.median(float(r["audits"][audit]["numericValue"]) for r in ok)
        out[key] = round(v, 3) if key == "cls" else round(v)
    out["runs"] = len(ok)
    return out


def speed_findings(summary: dict, url: str, form: str) -> list[dict]:
    out = []
    for short, key, ni, poor, label, fix in THRESHOLDS:
        v = summary.get(key)
        if v is None or v <= ni:
            continue
        sev = "high" if v > poor else "medium"
        unit = "" if key == "cls" else " ms"
        out.append({
            "id": f"speed-{short}-{form}", "module": "speed", "tags": ["speed"], "severity": sev,
            "title": f"{label} {v}{unit} ({form})", "url": url,
            "evidence": {"type": "measurement",
                         "detail": f"{label} mediana {v}{unit} z {summary.get('runs')} przebiegów Lighthouse ({form}); "
                                   f"próg dobry ≤ {ni}{unit}, słaby > {poor}{unit}"},
            "fix": fix, "impact": 3 if sev == "high" else 2, "effort": "M", "source": "lighthouse",
        })
    return out


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def summarize(run_dir: Path, url: str) -> dict:
    result = {"mobile": None, "desktop": None, "findings": [], "trackers_before_consent": [],
              "analytics_detected": [], "external_fonts_before_consent": [], "lh_scores": {},
              "median_run_file": {}, "depth": "pominięty", "reason": None}
    for form in ("mobile", "desktop"):
        files = sorted(p for p in run_dir.glob(f"lh-{form}-*.json") if re.fullmatch(rf"lh-{form}-\d+\.json", p.name))
        loaded = [(p.name, r) for p, r in ((p, _load(p)) for p in files) if r is not None]
        valid = [(n, r) for n, r in loaded if _valid(r)]
        s = median_run([r for _, r in loaded])
        result[form] = s
        if s:
            result["findings"] += speed_findings(s, url, form)
            # category scores: median per category across valid runs (same basis as the metrics)
            cats: dict[str, list[float]] = {}
            for _, r in valid:
                for k, v in (r.get("categories") or {}).items():
                    if isinstance(v, dict) and v.get("score") is not None:
                        cats.setdefault(k, []).append(float(v["score"]))
            result["lh_scores"][form] = {k: round(statistics.median(v) * 100) for k, v in cats.items()}
            # the run whose LCP is closest to the median LCP — read diagnostics (insights) from this file
            name, median_report = min(valid, key=lambda nr: (abs(float(
                nr[1]["audits"]["largest-contentful-paint"]["numericValue"]) - s["lcp_ms"]), nr[0]))
            result["median_run_file"][form] = name
            if form == "mobile":
                result["trackers_before_consent"] = trackers.before_consent(median_report)
                result["analytics_detected"] = trackers.analytics_detected(median_report)
                result["external_fonts_before_consent"] = trackers.external_fonts(median_report)
    if result["mobile"] or result["desktop"]:
        result["depth"] = "pełny"
    else:
        result["reason"] = "brak udanych przebiegów Lighthouse (sprawdź Chrome i dostęp do strony)"
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir", type=Path)
    ap.add_argument("--url", required=True)
    a = ap.parse_args(argv)
    r = summarize(a.dir, a.url)
    (a.dir / "speed.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mobile": r["mobile"], "desktop": r["desktop"], "depth": r["depth"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
