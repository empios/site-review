"""Finding schema, evidence rule and de-duplication for site-review."""
from __future__ import annotations

import copy
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low")  # order = rank
MODULES = ("seo", "speed", "cro", "design", "code", "pl")
EFFORTS = ("S", "M", "L")
CONFIRMED = "potwierdzone"
UNVERIFIED = "do weryfikacji"

REQUIRED = ("id", "module", "severity", "title", "fix", "impact", "effort", "source")


def validate(f: dict) -> list[str]:
    errors = [f"missing field: {k}" for k in REQUIRED if f.get(k) in (None, "")]
    if f.get("module") not in (None, "") and f["module"] not in MODULES:
        errors.append(f"bad module: {f['module']!r}")
    if f.get("severity") not in (None, "") and f["severity"] not in SEVERITIES:
        errors.append(f"bad severity: {f['severity']!r}")
    imp = f.get("impact")
    if imp is not None and (not isinstance(imp, int) or isinstance(imp, bool) or not 1 <= imp <= 3):
        errors.append(f"bad impact: {imp!r} (expected int 1-3)")
    if f.get("effort") not in (None, "") and f["effort"] not in EFFORTS:
        errors.append(f"bad effort: {f['effort']!r}")
    return errors


def _has_evidence(f: dict) -> bool:
    ev = f.get("evidence")
    return isinstance(ev, dict) and bool(str(ev.get("detail") or "").strip())


def _code_location_ok(loc, repo: str | None) -> bool:
    if repo is None or not isinstance(loc, dict):
        return False
    file, line = loc.get("file"), loc.get("line")
    if not file or not isinstance(line, int) or line < 1:
        return False
    root = Path(repo).resolve()
    target = (root / file).resolve()
    return root in target.parents and target.is_file()


def apply_evidence_rule(f: dict, repo: str | None) -> dict:
    out = copy.deepcopy(f)
    out["confidence"] = CONFIRMED if _has_evidence(out) else UNVERIFIED
    if "code_location" in out and not _code_location_ok(out["code_location"], repo):
        del out["code_location"]
    return out


def _rank(sev: str) -> int:
    return SEVERITIES.index(sev) if sev in SEVERITIES else len(SEVERITIES)


def dedupe(findings: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    order: list[tuple] = []
    for f in findings:
        key = (f.get("id"), f.get("url"))
        if key not in merged:
            merged[key] = copy.deepcopy(f)
            order.append(key)
            continue
        cur = merged[key]
        tags = set(cur.get("tags") or []) | set(f.get("tags") or [])
        sources = set(str(cur.get("source", "")).split("+")) | set(str(f.get("source", "")).split("+"))
        if _rank(f.get("severity")) < _rank(cur.get("severity")):
            new = copy.deepcopy(f)
            for k in ("code_location",):
                if k in cur and k not in new:
                    new[k] = cur[k]
            cur = new
        elif "code_location" in f and "code_location" not in cur:
            cur["code_location"] = copy.deepcopy(f["code_location"])
        cur["tags"] = sorted(tags)
        cur["source"] = "+".join(sorted(s for s in sources if s))
        merged[key] = cur
    return [merged[k] for k in order]
