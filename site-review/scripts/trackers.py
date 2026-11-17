"""Detect marketing/analytics trackers loaded on page load (before any consent click)."""
from __future__ import annotations

from urllib.parse import urlparse

TRACKER_HOSTS = (
    "google-analytics.com", "googletagmanager.com", "connect.facebook.net", "facebook.com/tr",
    "doubleclick.net", "analytics.tiktok.com", "hotjar.com", "clarity.ms", "linkedin.com/px",
    "snap.licdn.com",
)


def _matches(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    hp = host + p.path
    for pat in TRACKER_HOSTS:
        if "/" in pat:
            dom, path = pat.split("/", 1)
            if (host == dom or host.endswith("." + dom)) and hp[len(host):].startswith("/" + path):
                return True
        elif host == pat or host.endswith("." + pat):
            return True
    return False


def before_consent(lh_report: dict) -> list[str]:
    try:
        items = lh_report["audits"]["network-requests"]["details"]["items"]
    except (KeyError, TypeError):
        return []
    return sorted({urlparse(i.get("url", "")).hostname for i in items if _matches(i.get("url", ""))} - {None})
