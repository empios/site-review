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


if __name__ == "__main__":
    unittest.main()
