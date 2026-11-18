import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, SCRIPTS


class MergeTest(unittest.TestCase):
    def test_merge_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp, "run")
            shutil.copytree(FIXTURES / "run1", run)
            r = subprocess.run([sys.executable, str(SCRIPTS / "merge_findings.py"), "--run", str(run)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            report = json.loads((run / "report.json").read_text())
            self.assertIsInstance(report["overall"], int)
            self.assertEqual(len(report["invalid"]), 1)
            found = json.loads((run / "findings.json").read_text())
            self.assertEqual(sum(1 for x in found if x["id"] == "img-oversized"), 1)
            self.assertEqual(report["modules"]["code"]["depth"], "pominięty")
            self.assertIsNone(report["scores"]["code"]["score"])
            self.assertIsNone(report["recheck"])


    def test_new_ids_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp, "run")
            shutil.copytree(FIXTURES / "run1", run)
            p = run / "modules" / "speed.json"
            m = json.loads(p.read_text())
            m["new_ids"] = ["speed-something-new"]
            p.write_text(json.dumps(m))
            subprocess.run([sys.executable, str(SCRIPTS / "merge_findings.py"), "--run", str(run)], check=True,
                           capture_output=True)
            report = json.loads((run / "report.json").read_text())
        self.assertEqual(report["new_ids"], {"speed": ["speed-something-new"]})


    def _run_with_prev(self, finding_overrides):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp, "run")
            shutil.copytree(FIXTURES / "run1", run)
            p = run / "modules" / "seo.json"
            m = json.loads(p.read_text())
            m["findings"][0].update(finding_overrides)   # seo-canonical-missing
            p.write_text(json.dumps(m))
            prev = Path(tmp, "prev.json")
            prev.write_text(json.dumps([{"id": "seo-canonical-missing", "module": "seo", "severity": "medium",
                                         "url": "https://www.example.com"}]))
            subprocess.run([sys.executable, str(SCRIPTS / "merge_findings.py"), "--run", str(run), "--prev", str(prev)],
                           check=True, capture_output=True)
            return [x for x in json.loads((run / "findings.json").read_text()) if x["id"] == "seo-canonical-missing"][0]

    def test_recheck_keeps_previous_severity_without_reason(self):
        f = self._run_with_prev({"severity": "high"})
        self.assertEqual(f["severity"], "medium")
        self.assertTrue(f["severity_kept_from_prev"])

    def test_recheck_allows_severity_change_with_reason(self):
        f = self._run_with_prev({"severity": "high", "severity_changed_reason": "canonical teraz na 5 stronach"})
        self.assertEqual(f["severity"], "high")
        self.assertNotIn("severity_kept_from_prev", f)


    def test_quick_wins_have_titles(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp, "run")
            shutil.copytree(FIXTURES / "run1", run)
            subprocess.run([sys.executable, str(SCRIPTS / "merge_findings.py"), "--run", str(run)], check=True,
                           capture_output=True)
            qw = json.loads((run / "report.json").read_text())["quick_wins"]
        self.assertLessEqual(len(qw), 3)
        self.assertTrue(qw)
        self.assertEqual(set(qw[0]), {"id", "title", "url", "fix", "code_location"})
        self.assertEqual(qw[0]["id"], "img-oversized")  # highest priority quick win in run1


    def test_page_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp, "run")
            shutil.copytree(FIXTURES / "run1", run)
            ctx = json.loads((run / "context.json").read_text())
            ctx["pages"] = ["https://example.com/", "https://example.com/oferta"]
            (run / "context.json").write_text(json.dumps(ctx))
            seo = json.loads((run / "modules" / "seo.json").read_text())
            seo["pages_checked"] = ctx["pages"]
            (run / "modules" / "seo.json").write_text(json.dumps(seo))
            (run / "pages.json").write_text(json.dumps([
                {"url": "https://example.com/", "title": "Home", "status": 200, "lighthouse": {"lcp_ms": 1700}},
                {"url": "https://example.com/oferta", "title": "Oferta", "status": 200, "lighthouse": None}]))
            subprocess.run([sys.executable, str(SCRIPTS / "merge_findings.py"), "--run", str(run)], check=True,
                           capture_output=True)
            pages = json.loads((run / "report.json").read_text())["pages"]
        home, offer = pages
        self.assertEqual(home["modules"]["seo"], 1)            # seo-canonical-missing on the start page
        self.assertEqual(offer["modules"]["seo"], "bez uwag")    # checked, nothing found
        self.assertEqual(offer["modules"]["design"], "nie sprawdzono")  # design gave no pages_checked
        self.assertEqual(offer["modules"]["cro"], "pominięty")  # module not run in run1
        self.assertEqual(home["lighthouse"]["lcp_ms"], 1700)
        self.assertEqual(offer["title"], "Oferta")


if __name__ == "__main__":
    unittest.main()
