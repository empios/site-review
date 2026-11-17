import json
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, SCRIPTS
from tests.sitehelper import Server


def chrome_available() -> bool:
    r = subprocess.run(["bash", str(SCRIPTS / "chrome.sh"), "--print-path"], capture_output=True)
    return r.returncode == 0 and shutil.which("node") is not None


def png_size(p: Path) -> tuple[int, int]:
    w, h = struct.unpack(">II", p.read_bytes()[16:24])
    return w, h


@unittest.skipUnless(chrome_available(), "Chrome or Node not available")
class ScreenshotsTest(unittest.TestCase):
    def test_true_mobile_viewport_and_metrics(self):
        with Server(FIXTURES / "acceptance" / "site") as s, tempfile.TemporaryDirectory() as out:
            r = subprocess.run(["bash", str(SCRIPTS / "screenshots.sh"), s.base + "/", out],
                               capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            m = json.loads(Path(out, "metrics.json").read_text())
            self.assertEqual(m["375"]["innerWidth"], 375)
            self.assertFalse(m["375"]["horizontalScroll"])
            self.assertEqual(m["1440"]["innerWidth"], 1440)
            for name in ("shot-375.png", "shot-768.png", "shot-1440.png", "shot-375-dark.png"):
                self.assertTrue(Path(out, name).is_file(), name)
            self.assertEqual(png_size(Path(out, "shot-375.png"))[0], 375)

    def test_no_viewport_meta_reports_wide_layout(self):
        # fixtures/site has no <meta name=viewport>: a real phone lays it out at ~980 px
        with Server(FIXTURES / "site") as s, tempfile.TemporaryDirectory() as out:
            r = subprocess.run(["bash", str(SCRIPTS / "screenshots.sh"), s.base + "/", out],
                               capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            m = json.loads(Path(out, "metrics.json").read_text())
            folds = {n: Path(out, n).stat().st_size for n in ("shot-375-fold.jpg", "shot-1440-fold.jpg")
                     if Path(out, n).is_file()}
        self.assertGreater(m["375"]["innerWidth"], 375)
        self.assertEqual(sorted(folds), ["shot-1440-fold.jpg", "shot-375-fold.jpg"])
        for name, size in folds.items():
            self.assertLess(size, 300 * 1024, name)  # must fit render_report.EMBED_MAX

    def test_scroll_reveal_content_is_visible(self):
        # content revealed by IntersectionObserver must be shown before the full-page capture
        with Server(FIXTURES / "reveal") as s, tempfile.TemporaryDirectory() as out:
            r = subprocess.run(["bash", str(SCRIPTS / "screenshots.sh"), s.base + "/", out],
                               capture_output=True, text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            m = json.loads(Path(out, "metrics.json").read_text())
        for w in ("375", "1440"):
            self.assertEqual(m[w]["invisibleElements"], 0, w)

    def test_unreachable_url_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as out:
            r = subprocess.run(["bash", str(SCRIPTS / "screenshots.sh"), "http://127.0.0.1:1/", out],
                               capture_output=True, text=True, timeout=180)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
