import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, SCRIPTS
import crux
import findings
import lh_median
import trackers

LH = FIXTURES / "lh"


def load(*names):
    return [json.loads((LH / n).read_text()) for n in names]


class SpeedTest(unittest.TestCase):
    def test_median_three_runs(self):
        m = lh_median.median_run(load("lh-mobile-1.json", "lh-mobile-2.json", "lh-mobile-3.json"))
        self.assertEqual(m["performance"], 48)
        self.assertEqual(m["lcp_ms"], 4300)
        self.assertEqual(m["cls"], 0.08)
        self.assertEqual(m["tbt_ms"], 650)
        self.assertEqual(m["runs"], 3)

    def test_median_skips_broken(self):
        m = lh_median.median_run(load("lh-mobile-1.json", "lh-mobile-2.json", "lh-mobile-4.json"))
        self.assertEqual(m["runs"], 2)

    def test_median_none_when_all_broken(self):
        self.assertIsNone(lh_median.median_run(load("lh-mobile-4.json")))
        self.assertIsNone(lh_median.median_run([]))

    def test_speed_findings_thresholds(self):
        s = {"performance": 40, "lcp_ms": 4500, "cls": 0.05, "tbt_ms": 300, "fcp_ms": 1, "si_ms": 1, "runs": 3}
        out = lh_median.speed_findings(s, "https://e.com/", "mobile")
        by = {f["id"]: f for f in out}
        self.assertEqual(by["speed-lcp-mobile"]["severity"], "high")
        self.assertEqual(by["speed-tbt-mobile"]["severity"], "medium")
        self.assertNotIn("speed-cls-mobile", by)
        for f in out:
            self.assertEqual(findings.validate(f), [])
            self.assertEqual(f["source"], "lighthouse")

    def test_cli_all_runs_broken_marks_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lh-mobile-1.json").write_text('{"runtimeError": {}}')
            r = subprocess.run([sys.executable, str(SCRIPTS / "lh_median.py"), tmp, "--url", "https://e.com/"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            s = json.loads(Path(tmp, "speed.json").read_text())
        self.assertEqual(s["depth"], "pominięty")
        self.assertTrue(s["reason"])

    def test_trackers_before_consent(self):
        hosts = trackers.before_consent(load("lh-mobile-1.json")[0])
        self.assertIn("www.googletagmanager.com", hosts)
        self.assertIn("www.facebook.com", hosts)
        self.assertNotIn("cdn.e.com", hosts)

    def test_parse_psi(self):
        c = crux.parse_psi(json.loads((FIXTURES / "psi.json").read_text()))
        self.assertTrue(c["available"])
        self.assertEqual(c["lcp_p75"], 3800)
        self.assertEqual(c["inp_p75"], 250)
        self.assertEqual(c["cls_p75"], 0.12)
        self.assertEqual(c["category"], "SLOW")

    def test_parse_psi_no_data(self):
        self.assertFalse(crux.parse_psi({})["available"])

    def test_crux_cli_no_key(self):
        env = {k: v for k, v in os.environ.items() if k != "PSI_API_KEY"}
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(SCRIPTS / "crux.py"), "https://e.com/", "--out", tmp],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            c = json.loads(Path(tmp, "crux.json").read_text())
        self.assertFalse(c["available"])
        self.assertIn("PSI_API_KEY", c["reason"])


if __name__ == "__main__":
    unittest.main()
