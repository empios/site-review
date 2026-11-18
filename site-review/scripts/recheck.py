"""Compare two audit runs by (id, url).

A previous finding missing from the current run counts as "fixed" only when this run actually looked
for it: its module ran (not skipped) and its page was audited. Otherwise it is "unchecked".
"""
from __future__ import annotations

from urllib.parse import urlparse

from findings import canonical_id, owner


def normalize_url(url: str | None) -> str | None:
    """Same page regardless of http/https, www./bare host, trailing slash, query or fragment."""
    if not url:
        return url
    p = urlparse(url if "://" in url else "https://" + url)
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    return host + path


def key(f):
    return (canonical_id(f.get("id")), normalize_url(f.get("url")))


_key = key


def _checked(f: dict, skipped_modules: set | None, audited_urls: set | None) -> bool:
    module = owner(f) or f.get("module")
    if skipped_modules and module in skipped_modules:
        return False
    url = f.get("url")
    if audited_urls is not None and url and normalize_url(url) not in {normalize_url(u) for u in audited_urls}:
        return False
    return True


def diff(prev: list[dict], curr: list[dict], skipped_modules: set | None = None,
         audited_urls: set | None = None) -> dict:
    pk = {_key(f) for f in prev}
    ck = {_key(f) for f in curr}
    gone = [f for f in prev if _key(f) not in ck]
    return {
        "fixed": [f for f in gone if _checked(f, skipped_modules, audited_urls)],
        "unchecked": [f for f in gone if not _checked(f, skipped_modules, audited_urls)],
        "still": [f for f in curr if _key(f) in pk],
        "new": [f for f in curr if _key(f) not in pk],
    }
