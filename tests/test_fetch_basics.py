import json
import subprocess
import sys
import tempfile
import unittest
import urllib.robotparser
from pathlib import Path

from tests.helpers import FIXTURES, SCRIPTS
from tests.sitehelper import Server
import fetch_basics

SITE = FIXTURES / "site"


def robots(lines):
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(lines)
    return rp


class FetchBasicsTest(unittest.TestCase):
    def test_parse_meta_basic(self):
        m = fetch_basics.parse_meta((SITE / "index.html").read_text(encoding="utf-8"))
        self.assertIsNone(m["canonical"])
        self.assertEqual(m["h1_count"], 1)
        self.assertEqual(m["lang"], "pl")
        self.assertEqual(m["description"], "Opis strony głównej")
        self.assertIn("/a", m["links"])
        self.assertEqual(m["hreflang"], [{"lang": "en", "href": "/en/"}])

    def test_parse_meta_robots_noindex(self):
        m = fetch_basics.parse_meta((SITE / "b.html").read_text(encoding="utf-8"))
        self.assertEqual(m["robots"], "noindex")
        self.assertEqual(m["h1_count"], 2)

    def test_select_pages_respects_robots(self):
        rp = robots(["User-agent: *", "Disallow: /private/"])
        pages = fetch_basics.select_pages("https://e.com/", [], ["/a", "/b", "/private/x"], 5, rp)
        self.assertIn("https://e.com/a", pages)
        self.assertIn("https://e.com/b", pages)
        self.assertNotIn("https://e.com/private/x", pages)
        self.assertEqual(pages[0], "https://e.com/")

    def test_select_pages_no_sitemap_uses_nav(self):
        pages = fetch_basics.select_pages("https://e.com/", [], ["/a", "https://other.com/x", "#top"], 5, robots([]))
        self.assertEqual(pages, ["https://e.com/", "https://e.com/a"])

    def test_select_pages_sitemap_first_and_cap(self):
        sm = [f"https://e.com/s{i}" for i in range(80)]
        pages = fetch_basics.select_pages("https://e.com/", sm, ["/a"], 100, robots([]))
        self.assertEqual(len(pages), 50)
        self.assertEqual(pages[1], "https://e.com/s0")

    def test_fetch_unreachable(self):
        r = fetch_basics.fetch("http://127.0.0.1:1/", timeout=2)
        self.assertIsNone(r["status"])
        self.assertTrue(r["error"])

    def test_fetch_redirect_loop(self):
        with Server(SITE) as s:
            r = fetch_basics.fetch(s.base + "/loop")
        self.assertEqual(r["error"], "redirect loop")

    def test_cli_writes_basics(self):
        with Server(SITE) as s, tempfile.TemporaryDirectory() as out:
            r = subprocess.run([sys.executable, str(SCRIPTS / "fetch_basics.py"), s.base + "/", "--out", out,
                                "--pages", "5", "--delay", "0"], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            b = json.loads(Path(out, "basics.json").read_text())
        self.assertEqual(len(b["pages"]), 3)
        self.assertTrue(b["pl_detected"])
        self.assertEqual(b["sitemap"]["status"], 404)
        self.assertEqual(b["status"], 200)

    def test_cli_unreachable_does_not_crash(self):
        with tempfile.TemporaryDirectory() as out:
            r = subprocess.run([sys.executable, str(SCRIPTS / "fetch_basics.py"), "http://127.0.0.1:1/",
                                "--out", out, "--delay", "0"], capture_output=True, text=True, timeout=60)
            b = json.loads(Path(out, "basics.json").read_text())
        self.assertEqual(r.returncode, 2)
        self.assertIsNone(b["status"])
        self.assertTrue(b["errors"])


    def test_cli_error_status_start_page_exits_4(self):
        for code in (403, 503):
            with Server(SITE) as s, tempfile.TemporaryDirectory() as out:
                r = subprocess.run([sys.executable, str(SCRIPTS / "fetch_basics.py"), s.base + f"/status/{code}",
                                    "--out", out, "--delay", "0"], capture_output=True, text=True, timeout=60)
                b = json.loads(Path(out, "basics.json").read_text())
            self.assertEqual(r.returncode, 4, code)
            self.assertEqual(b["status"], code)
            self.assertTrue(any(str(code) in e for e in b["errors"]))


if __name__ == "__main__":
    unittest.main()
