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


# Analytics that may be first-party (own domain) — matched on path, reported as host+path prefix.
FIRST_PARTY_ANALYTICS_PATHS = ("/_vercel/insights", "/_vercel/speed-insights", "/js/script.js", "/umami.js",
                               "/matomo.js", "/piwik.js", "/gtag/js", "/cdn-cgi/zaraz")
ANALYTICS_HOSTS = TRACKER_HOSTS + ("plausible.io", "cloud.umami.is", "matomo.cloud", "posthog.com",
                                   "mixpanel.com", "segment.com", "cdn.segment.com", "va.vercel-scripts.com")
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "fonts.bunny.net")


def _items(lh_report: dict) -> list[dict]:
    try:
        return lh_report["audits"]["network-requests"]["details"]["items"] or []
    except (KeyError, TypeError):
        return []


def _host_match(host: str, dom: str) -> bool:
    return host == dom or host.endswith("." + dom)


def analytics_detected(lh_report: dict) -> list[str]:
    """Analytics loaded on page load: third-party hosts and first-party script paths (e.g. Vercel Analytics)."""
    found = set()
    for i in _items(lh_report):
        u = i.get("url", "")
        p = urlparse(u)
        host = (p.hostname or "").lower()
        if _matches(u) or any(_host_match(host, d) for d in ANALYTICS_HOSTS if "/" not in d):
            found.add(host)
            continue
        for path in FIRST_PARTY_ANALYTICS_PATHS:
            if p.path.startswith(path):
                found.add(host + path)
    return sorted(found)


def external_fonts(lh_report: dict) -> list[str]:
    """Font hosts contacted on page load (sends the visitor's IP to a third party before any consent)."""
    hosts = {(urlparse(i.get("url", "")).hostname or "").lower() for i in _items(lh_report)}
    return sorted(h for h in hosts if any(_host_match(h, d) for d in FONT_HOSTS))


def before_consent(lh_report: dict) -> list[str]:
    try:
        items = lh_report["audits"]["network-requests"]["details"]["items"]
    except (KeyError, TypeError):
        return []
    return sorted({urlparse(i.get("url", "")).hostname for i in items if _matches(i.get("url", ""))} - {None})
