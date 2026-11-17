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
                "a11y-img-alt-missing", "pl-tracking-before-consent"]
        self.assertEqual([i for i in need if i not in cat], [])

    def test_delegation_covers_modules(self):
        text = (REF / "delegation.md").read_text(encoding="utf-8")
        for m in findings.MODULES:
            self.assertRegex(text, rf"(?m)^\| `{m}` \|")

    def test_pl_module_disclaimer(self):
        self.assertIn("nie jest poradą prawną", (REF / "pl.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
