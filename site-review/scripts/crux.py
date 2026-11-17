#!/usr/bin/env python3
"""Real-user (CrUX) field data via PageSpeed Insights API.

Usage: crux.py URL --out DIR   (needs PSI_API_KEY in env; without it writes available=false)
Only for public URLs: the URL is sent to Google.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def parse_psi(psi: dict) -> dict:
    le = (psi or {}).get("loadingExperience") or {}
    m = le.get("metrics") or {}
    if not m:
        return {"available": False, "lcp_p75": None, "inp_p75": None, "cls_p75": None, "category": None}

    def pct(k):
        return (m.get(k) or {}).get("percentile")

    cls = pct("CUMULATIVE_LAYOUT_SHIFT_SCORE")
    return {"available": True, "lcp_p75": pct("LARGEST_CONTENTFUL_PAINT_MS"),
            "inp_p75": pct("INTERACTION_TO_NEXT_PAINT"),
            "cls_p75": None if cls is None else round(cls / 100, 3),
            "category": le.get("overall_category")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("PSI_API_KEY")
    if not key:
        res = {"available": False, "reason": "brak klucza PSI_API_KEY"}
    else:
        q = urllib.parse.urlencode({"url": a.url, "key": key, "strategy": "mobile", "category": "performance"})
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=90) as r:
                res = parse_psi(json.loads(r.read().decode("utf-8")))
            if not res["available"]:
                res["reason"] = "brak danych CrUX dla tego adresu (za mały ruch)"
        except Exception as e:
            res = {"available": False, "reason": f"błąd PSI: {type(e).__name__}"}
    (a.out / "crux.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
