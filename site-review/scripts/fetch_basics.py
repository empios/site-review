#!/usr/bin/env python3
"""Fetch the basics of a site: redirects, headers, robots.txt, sitemap, page meta.

Usage: fetch_basics.py URL --out DIR [--pages 5] [--delay 1]
Writes DIR/basics.json and raw HTML into DIR/raw/.
Exit 2 when the start URL is unreachable, 4 when it answers with an HTTP error (4xx/5xx, e.g. a WAF block).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

UA = "site-review/0.1"
DELAY = 1.0
MAX_PAGES = 50
MAX_REDIRECTS = 10
MAX_BODY = 5 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def fetch(url: str, timeout: int = 15) -> dict:
    chain = [url]
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        req = urllib.request.Request(current, headers={"User-Agent": UA})
        try:
            with _OPENER.open(req, timeout=timeout) as resp:
                status, headers, body = resp.status, dict(resp.headers), resp.read(MAX_BODY)
        except urllib.error.HTTPError as e:
            status, headers = e.code, dict(e.headers or {})
            body = e.read(MAX_BODY) if e.fp else b""
            e.close()
        except Exception as e:  # network errors, timeouts, bad URLs
            return {"status": None, "headers": {}, "body": "", "chain": chain, "error": f"{type(e).__name__}: {e}"}
        if 300 <= status < 400 and headers.get("Location"):
            current = urllib.parse.urljoin(current, headers["Location"])
            chain.append(current)
            continue
        return {"status": status, "headers": headers, "body": body.decode("utf-8", "replace"),
                "chain": chain, "error": None}
    return {"status": None, "headers": {}, "body": "", "chain": chain, "error": "redirect loop"}


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.m = {"title": None, "description": None, "canonical": None, "robots": None, "lang": None,
                  "h1_count": 0, "hreflang": [], "og": {}, "links": []}
        self._in_title = False
        self._title = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and a.get("lang"):
            self.m["lang"] = a["lang"].strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self.m["h1_count"] += 1
        elif tag == "a" and a.get("href"):
            self.m["links"].append(a["href"].strip())
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel and self.m["canonical"] is None:
                self.m["canonical"] = a.get("href", "").strip() or None
            if "alternate" in rel and a.get("hreflang"):
                self.m["hreflang"].append({"lang": a["hreflang"], "href": a.get("href", "")})
        elif tag == "meta":
            name = a.get("name", "").lower()
            prop = a.get("property", "").lower()
            if name == "description":
                self.m["description"] = a.get("content", "").strip()
            elif name == "robots":
                self.m["robots"] = a.get("content", "").strip()
            elif prop.startswith("og:"):
                self.m["og"][prop[3:]] = a.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            if self.m["title"] is None:
                self.m["title"] = "".join(self._title).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title.append(data)


def parse_meta(html: str) -> dict:
    p = _MetaParser()
    try:
        p.feed(html)
        p.close()
    except Exception:
        pass
    return p.m


def _normalize(start: str, link: str) -> str | None:
    if not link or link.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    u = urllib.parse.urljoin(start, link)
    u, _ = urllib.parse.urldefrag(u)
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https") or p.netloc != urllib.parse.urlparse(start).netloc:
        return None
    return u


def select_pages(start: str, sitemap_urls: list[str], nav_links: list[str], n: int,
                 robots: urllib.robotparser.RobotFileParser) -> list[str]:
    n = max(1, min(n, MAX_PAGES))
    pages = [start]
    for link in list(sitemap_urls) + list(nav_links):
        if len(pages) >= n:
            break
        u = _normalize(start, link)
        if not u or u in pages or u.rstrip("/") == start.rstrip("/"):
            continue
        if not robots.can_fetch(UA, u):
            continue
        pages.append(u)
    return pages


def _sitemap_locs(xml: str) -> tuple[str, list[str]]:
    try:
        root = ET.fromstring(xml.encode("utf-8"))
    except ET.ParseError:
        return "invalid", []
    kind = root.tag.split("}")[-1]
    locs = [el.text.strip() for el in root.iter() if el.tag.split("}")[-1] == "loc" and el.text]
    return kind, locs


def collect(url: str, out: Path, pages: int = 5, delay: float = DELAY) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"
    raw_dir.mkdir(exist_ok=True)
    errors: list[str] = []
    first = fetch(url)
    basics = {"start_url": url, "final_url": first["chain"][-1], "chain": first["chain"], "status": first["status"],
              "headers": first["headers"], "robots": None, "sitemap": None, "pages": [], "errors": errors,
              "pl_detected": False}
    if first["error"] or first["status"] is None:
        errors.append(f"start: {first['error']}")
        return basics
    if first["status"] >= 400:
        errors.append(f"start: HTTP {first['status']} (strona startowa zwraca błąd — może to blokada botów/WAF)")
    final = first["chain"][-1]
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(final))

    time.sleep(delay)
    rb = fetch(origin + "/robots.txt")
    basics["robots"] = {"status": rb["status"], "body": rb["body"][:20000] if rb["status"] == 200 else ""}
    rp = urllib.robotparser.RobotFileParser()
    if rb["status"] == 200:
        rp.parse(rb["body"].splitlines())
    else:
        rp.parse([])
        rp.allow_all = True

    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rb["body"] if rb["status"] == 200 else "")
    sm_url = sm_urls[0] if sm_urls else origin + "/sitemap.xml"
    time.sleep(delay)
    sm = fetch(sm_url)
    locs: list[str] = []
    if sm["status"] == 200:
        kind, found = _sitemap_locs(sm["body"])
        if kind == "sitemapindex":
            for child in found[:3]:
                time.sleep(delay)
                c = fetch(child)
                if c["status"] == 200:
                    locs += _sitemap_locs(c["body"])[1]
        else:
            locs = found
    basics["sitemap"] = {"url": sm_url, "status": sm["status"], "urls": locs[:500]}

    start_meta = parse_meta(first["body"])
    chosen = select_pages(final, locs, start_meta["links"], pages, rp)
    for i, page in enumerate(chosen):
        if i == 0:
            res, meta = first, start_meta
        else:
            time.sleep(delay)
            res = fetch(page)
            meta = parse_meta(res["body"]) if res["body"] else None
            if res["error"]:
                errors.append(f"{page}: {res['error']}")
        raw_path = raw_dir / f"page-{i}.html"
        raw_path.write_text(res["body"], encoding="utf-8")
        basics["pages"].append({"url": page, "status": res["status"], "headers": res["headers"],
                                "meta": meta, "raw_html_path": str(raw_path)})
    lang = (start_meta.get("lang") or "").lower()
    host = urllib.parse.urlparse(final).hostname or ""
    basics["pl_detected"] = lang.startswith("pl") or host.endswith(".pl")
    return basics


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--delay", type=float, default=DELAY)
    a = ap.parse_args(argv)
    b = collect(a.url, a.out, a.pages, a.delay)
    (a.out / "basics.json").write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": b["status"], "pages": len(b["pages"]), "errors": b["errors"]}, ensure_ascii=False))
    if b["status"] is None:
        return 2
    return 4 if b["status"] >= 400 else 0


if __name__ == "__main__":
    sys.exit(main())
