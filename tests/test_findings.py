import tempfile
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
import findings


def make(**kw):
    f = {
        "id": "seo-canonical-missing",
        "module": "seo",
        "tags": ["seo"],
        "severity": "high",
        "title": "Brak canonical",
        "url": "https://example.com/",
        "evidence": {"type": "dom", "detail": "no <link rel=canonical>"},
        "fix": "Dodaj canonical",
        "impact": 2,
        "effort": "S",
        "source": "fallback",
    }
    f.update(kw)
    return f


class FindingsTest(unittest.TestCase):
    def test_validate_ok(self):
        self.assertEqual(findings.validate(make()), [])

    def test_validate_bad_impact(self):
        errors = findings.validate(make(impact=5))
        self.assertTrue(any("impact" in e for e in errors))

    def test_evidence_missing_marks_unverified(self):
        f = make()
        del f["evidence"]
        self.assertEqual(findings.apply_evidence_rule(f, None)["confidence"], "do weryfikacji")

    def test_evidence_present_marks_confirmed(self):
        self.assertEqual(findings.apply_evidence_rule(make(), None)["confidence"], "potwierdzone")

    def test_code_location_dropped_without_repo(self):
        f = make(code_location={"file": "app/page.tsx", "line": 3, "confidence": "pewne"})
        self.assertNotIn("code_location", findings.apply_evidence_rule(f, None))

    def test_code_location_dropped_when_file_missing(self):
        with tempfile.TemporaryDirectory() as repo:
            f = make(code_location={"file": "app/page.tsx", "line": 3, "confidence": "pewne"})
            self.assertNotIn("code_location", findings.apply_evidence_rule(f, repo))

    def test_code_location_kept_when_file_exists(self):
        with tempfile.TemporaryDirectory() as repo:
            p = Path(repo, "app")
            p.mkdir()
            (p / "page.tsx").write_text("a\nb\nc\n")
            f = make(code_location={"file": "app/page.tsx", "line": 3, "confidence": "pewne"})
            self.assertIn("code_location", findings.apply_evidence_rule(f, repo))

    def test_dedupe_merges_tags_and_max_severity(self):
        a = make(id="img-oversized", module="speed", tags=["speed"], severity="medium", source="lighthouse")
        b = make(id="img-oversized", module="design", tags=["design"], severity="high", source="fallback")
        out = findings.dedupe([a, b])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["severity"], "high")
        self.assertEqual(out[0]["tags"], ["design", "speed"])
        self.assertEqual(out[0]["source"], "fallback+lighthouse")


if __name__ == "__main__":
    unittest.main()
