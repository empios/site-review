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


# Module that owns a finding, from its id prefix. Shared ids (img-*, font-*) belong to speed.
OWNER = {"seo": "seo", "speed": "speed", "cro": "cro", "design": "design", "a11y": "design",
         "code": "code", "pl": "pl", "img": "speed", "font": "speed"}


def owner(f: dict) -> str | None:
    return OWNER.get(str(f.get("id", "")).split("-", 1)[0])


def dedupe(findings: list[dict]) -> list[dict]:
    """Merge findings with the same (id, url).

    The representative is the most severe finding that has evidence (or the most severe overall when none
    has evidence); the module comes from the id prefix, never from which file was read first.
    """
    groups: dict[tuple, list[dict]] = {}
    order: list[tuple] = []
    for f in findings:
        key = (f.get("id"), f.get("url"))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(f)
    out = []
    for key in order:
        group = groups[key]
        pool = [f for f in group if _has_evidence(f)] or group
        rep = copy.deepcopy(min(pool, key=lambda f: _rank(f.get("severity"))))
        if "code_location" not in rep:
            loc = next((f["code_location"] for f in group if "code_location" in f), None)
            if loc is not None:
                rep["code_location"] = copy.deepcopy(loc)
        rep["tags"] = sorted({t for f in group for t in (f.get("tags") or [])})
        rep["source"] = "+".join(sorted({s for f in group for s in str(f.get("source", "")).split("+") if s}))
        rep["module"] = owner(rep) or rep.get("module")
        if rep.get("confidence") is not None:
            rep["confidence"] = CONFIRMED if _has_evidence(rep) else UNVERIFIED
        out.append(rep)
    return out
