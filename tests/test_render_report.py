import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, SCRIPTS, SKILL
import merge_findings
import render_report

TEMPLATE = (SKILL / "assets" / "report-template.html").read_text(encoding="utf-8")


def build(tmp: str):
    run = Path(tmp, "run")
    shutil.copytree(FIXTURES / "run1", run)
    report = merge_findings.merge(run, None, None)
    found = json.loads((run / "findings.json").read_text())
    return run, report, found


class RenderReportTest(unittest.TestCase):
    def test_escapes_untrusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            found[0]["title"] = "<script>alert(1)</script>"
            report = copy.deepcopy(report)
            report["top"][0]["title"] = "<script>alert(1)</script>"
            html = render_report.render(report, found, "Podsumowanie <b>x</b> {{modules}}", TEMPLATE, str(run))
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)
        self.assertIn("Podsumowanie &lt;b&gt;x&lt;/b&gt; {{modules}}", html)  # not substituted
        self.assertEqual(html.count("{{"), 1)

    def test_sections_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            html = render_report.render(report, found, "S", TEMPLATE, str(run))
        ids = ["sec-summary", "sec-scores", "sec-top", "sec-modules", "sec-unverified", "sec-method"]
        pos = [html.index(f'id="{i}"') for i in ids]
        self.assertEqual(pos, sorted(pos))

    def test_skipped_module_shows_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            html = render_report.render(report, found, "S", TEMPLATE, str(run))
        self.assertIn("brak repo", html)
        self.assertIn("pominięty", html)

    def test_large_screenshot_not_embedded(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            ev = run / "evidence"
            ev.mkdir()
            (ev / "big.png").write_bytes(b"\x89PNG" + b"0" * 400_000)
            (ev / "small.png").write_bytes(b"\x89PNG" + b"0" * 1000)
            found[0]["evidence"] = {"type": "screenshot", "detail": "duży", "path": "evidence/big.png"}
            found[2]["evidence"] = {"type": "screenshot", "detail": "mały", "path": "evidence/small.png"}
            html = render_report.render(report, found, "S", TEMPLATE, str(run))
        self.assertEqual(html.count("data:image/png;base64"), 1)
        self.assertIn("evidence/big.png", html)

    def test_screenshot_outside_run_dir_not_embedded(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            outside = Path(tmp, "secret.png")
            outside.write_bytes(b"\x89PNG" + b"1" * 100)
            found[0]["evidence"] = {"type": "screenshot", "detail": "x", "path": "../secret.png"}
            html = render_report.render(report, found, "S", TEMPLATE, str(run))
        self.assertNotIn("data:image", html)

    def test_recheck_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, report, found = build(tmp)
            mk = lambda i: {"id": i, "title": i, "url": "u"}
            report["recheck"] = {"fixed": [mk("a"), mk("b")], "still": [mk("c")], "new": [mk("d"), mk("e"), mk("f")]}
            html = render_report.render(report, found, "S", TEMPLATE, str(run))
        self.assertIn('id="sec-recheck"', html)
        self.assertIn("Naprawione: 2", html)
        self.assertIn("Nadal: 1", html)
        self.assertIn("Nowe: 3", html)

    def test_cli_writes_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, _, _ = build(tmp)
            (run / "summary.txt").write_text("Streszczenie testowe", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "render_report.py"), "--run", str(run),
                                "--summary", str(run / "summary.txt")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            html = (run / "report.html").read_text(encoding="utf-8")
        self.assertIn("Streszczenie testowe", html)
        self.assertIn("<title>", html)


if __name__ == "__main__":
    unittest.main()
