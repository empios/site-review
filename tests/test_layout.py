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
