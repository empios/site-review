import unittest

from tests.helpers import FIXTURES
import findings
import render_diff

RAW = (FIXTURES / "csr" / "raw.html").read_text(encoding="utf-8")
REN = (FIXTURES / "csr" / "rendered.html").read_text(encoding="utf-8")


class RenderDiffTest(unittest.TestCase):
    def test_compare_csr(self):
        d = render_diff.compare(RAW, REN)
        self.assertLess(d["ratio"], 0.5)
        self.assertIn("h1", d["missing_in_raw"])
        self.assertIn("canonical", d["missing_in_raw"])
        self.assertNotIn("title", d["missing_in_raw"])

    def test_compare_ssr_same(self):
        d = render_diff.compare(REN, REN)
        self.assertEqual(d["ratio"], 1.0)
        self.assertEqual(d["missing_in_raw"], [])

    def test_compare_ignores_script_and_style_text(self):
        d = render_diff.compare("<html><body><script>var a = 'jeden dwa trzy';</script><p>raz</p></body></html>",
                                "<html><body><p>raz</p></body></html>")
        self.assertEqual(d["raw_words"], 1)

    def test_to_findings_csr(self):
        out = render_diff.to_findings(render_diff.compare(RAW, REN), "https://e.com/")
        ids = [f["id"] for f in out]
        self.assertIn("seo-content-js-only", ids)
        self.assertIn("seo-h1-js-only", ids)
        for f in out:
            self.assertEqual(findings.validate(f), [], f)
            self.assertTrue(f["evidence"]["detail"])

    def test_to_findings_ssr_empty(self):
        self.assertEqual(render_diff.to_findings(render_diff.compare(REN, REN), "https://e.com/"), [])


if __name__ == "__main__":
    unittest.main()


class RenderDiffCliTest(unittest.TestCase):
    def test_chrome_hang_writes_unavailable(self):
        import json, os, subprocess, sys, tempfile
        from pathlib import Path
        from tests.helpers import SCRIPTS
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp, "fake-chrome")
            marker = Path(tmp, "child.pid")
            fake.write_text(f"#!/bin/bash\nsleep 30 &\necho $! > {marker}\nwait\n")
            fake.chmod(0o755)
            raw = Path(tmp, "raw.html")
            raw.write_text(RAW)
            env = dict(os.environ, CHROME_PATH=str(fake))
            r = subprocess.run([sys.executable, str(SCRIPTS / "render_diff.py"), "https://e.com/", "--raw", str(raw),
                                "--out", tmp, "--timeout", "2"], capture_output=True, text=True, env=env, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            res = json.loads(Path(tmp, "render_diff.json").read_text())
            child = int(marker.read_text())
            import time
            time.sleep(0.5)
            alive = subprocess.run(["kill", "-0", str(child)], capture_output=True).returncode == 0
        self.assertFalse(alive, "Chrome child process left running after timeout")
        self.assertFalse(res["available"])
        self.assertIn("timeout", res["error"])
        self.assertEqual(res["findings"], [])
