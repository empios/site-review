import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import SCRIPTS
import pages_summary


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def make_run(tmp: str) -> Path:
    run = Path(tmp)
    write(run / "basics.json", {"pages": [
        {"url": "https://e.com/", "status": 200, "meta": {"title": "Home"}},
        {"url": "https://e.com/oferta", "status": 200, "meta": {"title": "Oferta"}},
        {"url": "https://e.com/kontakt", "status": 404, "meta": {"title": "Nie znaleziono"}}]})
    write(run / "speed.json", {"mobile": {"performance": 93, "lcp_ms": 1700, "cls": 0.0, "tbt_ms": 0, "runs": 3},
                               "lh_scores": {"mobile": {"performance": 93, "accessibility": 95, "seo": 100}},
                               "trackers_before_consent": [], "external_fonts_before_consent": ["fonts.gstatic.com"],
                               "analytics_detected": ["e.com/_vercel/insights"], "findings": []})
    write(run / "render_diff.json", {"available": True, "ratio": 1.0, "missing_in_raw": []})
    write(run / "pages" / "1" / "speed.json", {"mobile": {"performance": 61, "lcp_ms": 4800, "cls": 0.2, "tbt_ms": 300,
                                                          "runs": 1},
                                               "lh_scores": {"mobile": {"performance": 61, "accessibility": 82}},
                                               "trackers_before_consent": ["www.googletagmanager.com"],
                                               "external_fonts_before_consent": [], "analytics_detected": [],
                                               "findings": [{"id": "speed-lcp-mobile"}]})
    write(run / "pages" / "1" / "render_diff.json", {"available": True, "ratio": 0.3, "missing_in_raw": ["h1"]})
    write(run / "shots" / "0" / "metrics.json", {"375": {"innerWidth": 375, "horizontalScroll": False,
                                                         "invisibleElements": 0}})
    write(run / "shots" / "1" / "metrics.json", {"375": {"innerWidth": 375, "horizontalScroll": True,
                                                         "invisibleElements": 2}})
    return run


class PagesSummaryTest(unittest.TestCase):
    def test_summary_per_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = pages_summary.summarize(make_run(tmp))
        self.assertEqual([p["url"] for p in pages], ["https://e.com/", "https://e.com/oferta", "https://e.com/kontakt"])
        home, offer, contact = pages
        self.assertEqual(home["lighthouse"]["lcp_ms"], 1700)
        self.assertEqual(home["lighthouse"]["accessibility"], 95)
        self.assertEqual(offer["lighthouse"]["lcp_ms"], 4800)
        self.assertEqual(offer["lighthouse"]["runs"], 1)
        self.assertEqual(offer["lighthouse"]["accessibility"], 82)
        self.assertEqual(offer["trackers_before_consent"], ["www.googletagmanager.com"])
        self.assertEqual(offer["render_ratio"], 0.3)
        self.assertTrue(offer["mobile"]["horizontalScroll"])
        self.assertIsNone(contact["lighthouse"])
        self.assertEqual(contact["status"], 404)
        self.assertEqual(home["title"], "Home")

    def test_cli_writes_pages_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(tmp)
            r = subprocess.run([sys.executable, str(SCRIPTS / "pages_summary.py"), str(run)], capture_output=True,
                               text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(json.loads((run / "pages.json").read_text())), 3)
