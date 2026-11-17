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
