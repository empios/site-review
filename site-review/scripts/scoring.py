"""Deterministic scoring and prioritisation for site-review."""
from __future__ import annotations

from findings import CONFIRMED, MODULES, SEVERITIES

PENALTY = {"critical": 25, "high": 10, "medium": 4, "low": 1}
WEIGHTS = {"seo": 25, "speed": 20, "cro": 20, "design": 20, "code": 15}  # pl excluded
EFFORT_WEIGHT = {"S": 3, "M": 2, "L": 1}
SKIPPED = "pominięty"


def _confirmed(findings):
    return [f for f in findings if f.get("confidence") == CONFIRMED]


def module_scores(findings: list[dict], depth: dict[str, str]) -> dict[str, dict]:
    out = {}
    conf = _confirmed(findings)
    for m in MODULES:
        d = depth.get(m, SKIPPED)
        mine = [f for f in conf if f.get("module") == m]
        score = None if d == SKIPPED else max(0, 100 - sum(PENALTY.get(f.get("severity"), 0) for f in mine))
        out[m] = {"score": score, "depth": d, "count": len(mine)}
    return out


def overall(scores: dict) -> int | None:
    num = den = 0
    for m, w in WEIGHTS.items():
        s = (scores.get(m) or {}).get("score")
        if s is not None:
            num += s * w
            den += w
    return round(num / den) if den else None


def priority(f: dict) -> int:
    return int(f.get("impact", 1)) * EFFORT_WEIGHT.get(f.get("effort"), 1)


def quadrant(f: dict) -> str:
    if int(f.get("impact", 1)) < 2:
        return "drobiazg"
    return "quick win" if f.get("effort") == "S" else "duży projekt"


def _sev_rank(f):
    s = f.get("severity")
    return SEVERITIES.index(s) if s in SEVERITIES else len(SEVERITIES)


def top(findings: list[dict], n: int = 10) -> list[dict]:
    return sorted(_confirmed(findings), key=lambda f: (-priority(f), _sev_rank(f), str(f.get("id"))))[:n]
