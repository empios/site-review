"""Compare two audit runs by (id, url)."""
from __future__ import annotations


def _key(f):
    return (f.get("id"), f.get("url"))


def diff(prev: list[dict], curr: list[dict]) -> dict:
    pk = {_key(f) for f in prev}
    ck = {_key(f) for f in curr}
    return {
        "fixed": [f for f in prev if _key(f) not in ck],
        "still": [f for f in curr if _key(f) in pk],
        "new": [f for f in curr if _key(f) not in pk],
    }
