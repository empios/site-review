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
