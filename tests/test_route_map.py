import unittest

from tests.helpers import FIXTURES
import locate_code
import route_map

R = FIXTURES / "repos"


class RouteMapTest(unittest.TestCase):
    def test_detect_next_app(self):
        self.assertEqual(route_map.detect_framework(str(R / "next-app")), "next-app")

    def test_detect_astro(self):
        self.assertEqual(route_map.detect_framework(str(R / "astro")), "astro")

    def test_detect_unknown(self):
        self.assertEqual(route_map.detect_framework(str(R / "unknown")), "unknown")

    def test_route_dynamic_segment(self):
        files = route_map.route_to_files(str(R / "next-app"), "/produkt/abc")
        self.assertIn("app/produkt/[slug]/page.tsx", files)
        self.assertIn("app/layout.tsx", files)

    def test_route_group_segment(self):
        files = route_map.route_to_files(str(R / "next-app"), "/koszyk")
        self.assertIn("app/(shop)/koszyk/page.tsx", files)

    def test_route_root(self):
        self.assertIn("app/page.tsx", route_map.route_to_files(str(R / "next-app"), "/"))

    def test_route_astro_catch_all(self):
        files = route_map.route_to_files(str(R / "astro"), "/blog/2024/wpis")
        self.assertIn("src/pages/blog/[...slug].astro", files)

    def test_route_unknown_empty(self):
        self.assertEqual(route_map.route_to_files(str(R / "unknown"), "/"), [])

    def test_locate_certain(self):
        loc = locate_code.locate(str(R / "next-app"), "/produkt/abc", ["<h1>Produkt</h1>"])
        self.assertEqual(loc["file"], "app/produkt/[slug]/page.tsx")
        self.assertEqual(loc["line"], 4)
        self.assertEqual(loc["confidence"], "pewne")

    def test_locate_probable_outside_route(self):
        loc = locate_code.locate(str(R / "next-app"), "/nieistnieje", ["Koszyk"])
        self.assertEqual(loc["confidence"], "prawdopodobne")
        self.assertEqual(loc["file"], "app/(shop)/koszyk/page.tsx")

    def test_locate_none_for_unknown_repo(self):
        self.assertIsNone(locate_code.locate(str(R / "unknown"), "/", ["Nie ma takiego tekstu"]))

    def test_locate_ignores_node_modules(self):
        self.assertIsNone(locate_code.locate(str(R / "next-app"), "/", ["TylkoWNodeModules"]))


if __name__ == "__main__":
    unittest.main()
