import re
import unittest

from tests.helpers import SKILL


class LayoutTest(unittest.TestCase):
    def test_skill_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"))
        self.assertIn("name: site-review", text)
        m = re.search(r"^description: (.+)$", text, re.M)
        self.assertIsNotNone(m)
        self.assertLessEqual(len(m.group(1)), 1024)


if __name__ == "__main__":
    unittest.main()


class SkillBodyTest(unittest.TestCase):
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_skill_references_exist(self):
        paths = set(re.findall(r"((?:references|scripts|assets)/[\w.\-]+\.(?:md|py|sh|html))", self.text))
        self.assertGreaterEqual(len(paths), 10)
        missing = [p for p in sorted(paths) if not (SKILL / p).is_file()]
        self.assertEqual(missing, [])

    def test_skill_length(self):
        self.assertLessEqual(len(self.text.splitlines()), 500)

    def test_skill_mentions_flags(self):
        for flag in ("--quick", "--pages", "--only", "--pl", "--no-pl", "--recheck"):
            self.assertIn(flag, self.text)

    def test_skill_states_safety_limits(self):
        for phrase in ("bez logowania", "nie wysyłaj formularzy", "robots.txt"):
            self.assertIn(phrase, self.text.lower())


class SkillOperationalTest(unittest.TestCase):
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_http_error_start_page_handled(self):
        self.assertIn("Kod wyjścia 4", self.text)

    def test_long_steps_have_timeout_guidance(self):
        self.assertIn("600000", self.text)
        self.assertIn("lh_median.py", self.text.split("lighthouse_runs.sh", 1)[1][:600])

    def test_crux_only_for_public_urls(self):
        step = [l for l in self.text.splitlines() if "scripts/crux.py" in l and "START_URL" in l][0]
        self.assertIn("publiczn", step)


class SkillRunSetupTest(unittest.TestCase):
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_start_url_defined_as_final_url(self):
        self.assertIn("`START_URL` = `basics.json.final_url`", self.text)

    def test_stable_run_dir_with_seconds(self):
        self.assertIn("~/.site-review/<host>/", self.text)
        self.assertIn("YYYY-MM-DD-HHMMSS", self.text)
        self.assertNotIn("<scratchpad>/site-review", self.text)

    def test_publishes_artifact_fragment(self):
        self.assertIn("report.artifact.html", self.text)

    def test_module_format_and_new_ids_mentioned(self):
        self.assertIn("references/module-format.md", self.text)
        self.assertIn("new_ids", self.text)


class SkillQuickWinsTest(unittest.TestCase):
    def test_quick_wins_from_report(self):
        self.assertIn("report.json.quick_wins", (SKILL / "SKILL.md").read_text(encoding="utf-8"))
