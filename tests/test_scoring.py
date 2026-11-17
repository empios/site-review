import unittest

from tests import helpers  # noqa: F401
import recheck
import scoring

C = "potwierdzone"


def f(id_, module="seo", severity="medium", impact=2, effort="M", confidence=C, url="https://e.com/"):
    return {"id": id_, "module": module, "severity": severity, "impact": impact,
            "effort": effort, "confidence": confidence, "url": url}


FULL = {m: "pełny" for m in ("seo", "speed", "cro", "design", "code", "pl")}


class ScoringTest(unittest.TestCase):
    def test_module_score_penalties(self):
        s = scoring.module_scores([f("a", severity="critical"), f("b"), f("c")], FULL)
        self.assertEqual(s["seo"]["score"], 67)

    def test_score_floor_zero(self):
        s = scoring.module_scores([f(str(i), severity="critical") for i in range(5)], FULL)
        self.assertEqual(s["seo"]["score"], 0)

    def test_unverified_not_counted(self):
        s = scoring.module_scores([f("a", severity="critical", confidence="do weryfikacji")], FULL)
        self.assertEqual(s["seo"]["score"], 100)

    def test_skipped_module_none(self):
        depth = dict(FULL, code="pominięty")
        s = scoring.module_scores([], depth)
        self.assertIsNone(s["code"]["score"])
        self.assertEqual(s["code"]["depth"], "pominięty")

    def test_overall_excludes_pl_and_skipped(self):
        scores = {"seo": {"score": 80}, "speed": {"score": 60}, "pl": {"score": 0},
                  "code": {"score": None}, "cro": {"score": 100}, "design": {"score": 100}}
        self.assertEqual(scoring.overall(scores), 85)

    def test_priority_and_quadrant(self):
        a = f("a", impact=3, effort="S")
        b = f("b", impact=1, effort="L")
        self.assertEqual(scoring.priority(a), 9)
        self.assertEqual(scoring.quadrant(a), "quick win")
        self.assertEqual(scoring.priority(b), 1)
        self.assertEqual(scoring.quadrant(b), "drobiazg")
        self.assertEqual(scoring.quadrant(f("c", impact=2, effort="L")), "duży projekt")

    def test_top_limits_and_orders(self):
        items = [f(f"x{i}", impact=1, effort="L") for i in range(11)] + [f("best", impact=3, effort="S")]
        top = scoring.top(items)
        self.assertEqual(len(top), 10)
        self.assertEqual(top[0]["id"], "best")

    def test_top_skips_unverified(self):
        top = scoring.top([f("u", impact=3, effort="S", confidence="do weryfikacji")])
        self.assertEqual(top, [])

    def test_recheck_diff(self):
        d = recheck.diff([f("A"), f("B")], [f("B"), f("C")])
        self.assertEqual([x["id"] for x in d["fixed"]], ["A"])
        self.assertEqual([x["id"] for x in d["still"]], ["B"])
        self.assertEqual([x["id"] for x in d["new"]], ["C"])

    def test_recheck_no_prev(self):
        d = recheck.diff([], [f("A")])
        self.assertEqual([x["id"] for x in d["new"]], ["A"])
        self.assertEqual(d["fixed"], [])


if __name__ == "__main__":
    unittest.main()
