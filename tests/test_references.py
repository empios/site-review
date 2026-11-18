import re
import unittest

from tests.helpers import SKILL
import findings

REF = SKILL / "references"
MODULE_FILES = ["seo", "speed", "cro", "design", "code", "pl"]
ALL = MODULE_FILES + ["finding-ids", "delegation", "scoring", "url-to-code"]
ID_RE = re.compile(r"`([a-z0-9]+(?:-[a-z0-9<>]+)+)`")
ROW_ID_RE = re.compile(r"(?m)^\| `([^`]+)` \|")  # first table cell = finding id


def section(text: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def catalog() -> set[str]:
    return set(ID_RE.findall((REF / "finding-ids.md").read_text(encoding="utf-8")))


class ReferencesTest(unittest.TestCase):
    def test_all_reference_files_exist(self):
        for name in ALL:
            self.assertTrue((REF / f"{name}.md").is_file(), name)

    def test_module_files_have_sections(self):
        for name in MODULE_FILES:
            text = (REF / f"{name}.md").read_text(encoding="utf-8")
            for s in ("Instrukcja dla subagenta", "Delegacja", "Checklista"):
                self.assertTrue(section(text, s).strip(), f"{name}: brak sekcji {s}")

    def test_checklist_ids_in_catalog(self):
        cat = catalog()
        for name in MODULE_FILES:
            ids = ROW_ID_RE.findall(section((REF / f"{name}.md").read_text(encoding="utf-8"), "Checklista"))
            self.assertGreaterEqual(len(ids), 8, name)
            missing = [i for i in ids if i not in cat]
            self.assertEqual(missing, [], f"{name}: id spoza katalogu")

    def test_script_and_acceptance_ids_in_catalog(self):
        cat = catalog()
        need = ["seo-content-js-only", "seo-<elem>-js-only", "speed-lcp-<form>", "speed-cls-<form>",
                "speed-tbt-<form>", "seo-canonical-missing", "seo-noindex", "img-oversized",
                "a11y-img-alt-missing", "pl-tracking-before-consent",
                # ids invented by modules in the first real run (codeworks-it.pl), now catalogued
                "speed-redirect", "pl-external-fonts", "cro-cta-phone-only", "cro-contact-email-private",
                "cro-cta-offpage-link"]
        self.assertEqual([i for i in need if i not in cat], [])

    def test_delegation_covers_modules(self):
        text = (REF / "delegation.md").read_text(encoding="utf-8")
        for m in findings.MODULES:
            self.assertRegex(text, rf"(?m)^\| `{m}` \|")

    def test_pl_module_disclaimer(self):
        self.assertIn("nie jest poradą prawną", (REF / "pl.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class LighthouseAuditNamesTest(unittest.TestCase):
    """Every Lighthouse audit named in the references (written as `lh:<audit-id>`) must exist in LH 13 output."""

    def test_named_audits_exist_in_lighthouse_13(self):
        import json
        from tests.helpers import FIXTURES
        known = set(json.loads((FIXTURES / "lh" / "lh13-audit-ids.json").read_text()))
        named = set()
        for name in ("speed", "design", "seo", "cro", "code", "pl"):
            named |= set(re.findall(r"`lh:([a-z0-9-]+)`", (REF / f"{name}.md").read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(named), 12)
        self.assertEqual(sorted(named - known), [])


class ModuleFormatTest(unittest.TestCase):
    def test_module_format_doc_referenced_everywhere(self):
        doc = (REF / "module-format.md").read_text(encoding="utf-8")
        for word in ("evidence.type", "needles", "tags", "new_ids", "całej witryny"):
            self.assertIn(word, doc)
        for name in MODULE_FILES:
            self.assertIn("module-format.md", (REF / f"{name}.md").read_text(encoding="utf-8"), name)

    def test_evidence_types_documented_match_code(self):
        doc = (REF / "module-format.md").read_text(encoding="utf-8")
        for t in findings.EVIDENCE_TYPES:
            self.assertIn(f"`{t}`", doc)

    def test_seo_site_wide_rule(self):
        self.assertNotIn("Jeden wpis na stronę (`url`).", (REF / "seo.md").read_text(encoding="utf-8"))


class RecheckStabilityDocsTest(unittest.TestCase):
    def test_retired_aliases_documented(self):
        cat = (REF / "finding-ids.md").read_text(encoding="utf-8")
        self.assertIn("Dawne identyfikatory", cat)
        for old, new in findings.ALIASES.items():
            self.assertIn(f"`{old}`", cat)
            self.assertIn(new, cat)
        self.assertIn("`cro-cta-destination-mismatch`", cat)

    def test_severity_change_reason_documented(self):
        self.assertIn("severity_changed_reason", (REF / "module-format.md").read_text(encoding="utf-8"))

    def test_external_fonts_single_finding(self):
        pl = (REF / "pl.md").read_text(encoding="utf-8")
        self.assertNotIn("każdy host z `speed.json` → `external_fonts_before_consent`", pl)
        self.assertIn("jedno znalezisko `pl-external-fonts`", pl)

    def test_design_delegation_matches_table(self):
        self.assertNotIn("frontend-design", section((REF / "design.md").read_text(encoding="utf-8"), "Delegacja"))

    def test_no_inline_module_templates_without_format_ref(self):
        seo = (REF / "seo.md").read_text(encoding="utf-8")
        self.assertNotIn('`{"module": "seo", "depth": ..., "reason": ..., "findings": [...]}`', seo)


class SubpageCoverageDocsTest(unittest.TestCase):
    def test_modules_walk_every_page(self):
        for name in ("seo", "speed", "cro", "design", "pl"):
            text = (REF / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn("pages.json", text, name)
            self.assertIn("pages_checked", text, name)

    def test_module_format_documents_pages_checked(self):
        self.assertIn("`pages_checked`", (REF / "module-format.md").read_text(encoding="utf-8"))
