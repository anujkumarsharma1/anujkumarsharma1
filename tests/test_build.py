"""Standard-library tests: python -m unittest discover -s tests"""
import datetime as dt
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import build  # noqa: E402
from fixture import NOW, snapshot  # noqa: E402
from mm import data, svgkit  # noqa: E402


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

    def test_every_panel_is_valid_svg_and_referenced(self):
        files, block = build.render_all(snapshot(), self.cfg, NOW)
        self.assertIn("assets/generated/hero.svg", files)
        for path, text in files.items():
            root = ET.fromstring(text)
            self.assertTrue(root.tag.endswith("svg"), path)
            self.assertLess(len(text), 400_000, f"{path} is too heavy for a README")
            self.assertIsNone(re.search(r"\b(nan|inf)\b", text.lower()), f"{path} has NaN/inf")
            self.assertIn(path, block, f"{path} is rendered but not shown")

    def test_empty_account_still_renders(self):
        snap = snapshot(busy=0.0)
        snap["github"].update(events=[], repos=[], commits_all_time=0, contributions_all_time=0)
        snap.pop("codeforces")
        snap.pop("medium")
        files, _ = build.render_all(snap, self.cfg, NOW)
        for text in files.values():
            ET.fromstring(text)

    def test_build_writes_only_inside_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("intro\n<!-- mm:start -->\nold\n<!-- mm:end -->\noutro\n")
            build.main(["--fixture", "--out", tmp])
            text = readme.read_text()
            self.assertTrue(text.startswith("intro\n<!-- mm:start -->"))
            self.assertTrue(text.endswith("<!-- mm:end -->\noutro\n"))
            self.assertNotIn("\nold\n", text)
            again = build.update_readme(text, text.split("<!-- mm:start -->\n")[1].split("\n<!-- mm:end -->")[0])
            self.assertEqual(text, again)

    def test_fixture_cannot_overwrite_real_profile(self):
        with self.assertRaises(SystemExit):
            build.main(["--fixture"])


class DataTest(unittest.TestCase):
    def test_streaks(self):
        daily = {"2026-09-20": 1, "2026-09-21": 2, "2026-09-22": 0, "2026-09-23": 1,
                 "2026-09-24": 1, "2026-09-25": 3, "2026-09-26": 1, "2026-09-27": 1}
        self.assertEqual(data.streaks(daily, dt.date(2026, 9, 28)), (5, 5))
        self.assertEqual(data.streaks(daily, dt.date(2026, 9, 27)), (5, 5))
        self.assertEqual(data.streaks(daily, dt.date(2026, 9, 30)), (0, 5))
        self.assertEqual(data.streaks({}, dt.date(2026, 9, 30)), (0, 0))

    def test_rank_ladder(self):
        self.assertEqual(data.rank(0)[1], "RECRUIT")
        idx, name, prog, left, nxt = data.rank(400)
        self.assertEqual((name, nxt, left), ("SERGEANT", "STAFF SERGEANT", 100))
        self.assertAlmostEqual(prog, 0.5)
        self.assertEqual(data.rank(10_000)[1:], ("GENERAL", 1.0, 0, None))

    def test_languages_share(self):
        repos = [{"languages": {"Go": 300, "Python": 100}}, {"languages": {"Python": 100}}]
        self.assertEqual(data.languages(repos), [("Go", 0.6), ("Python", 0.4)])
        self.assertEqual(data.languages(repos, ignore=["Go"]), [("Python", 1.0)])

    def test_event_mapping(self):
        push = {"type": "PushEvent", "payload": {"size": 3}, "repo": {"name": "a/kavach"},
                "created_at": "2026-09-27T00:00:00Z"}
        self.assertEqual(data._event(push)["n"], 3)
        closed = {"type": "PullRequestEvent", "payload": {"action": "closed",
                                                          "pull_request": {"merged": False}},
                  "repo": {"name": "a/b"}}
        self.assertIsNone(data._event(closed))
        self.assertIsNone(data._event({"type": "WatchEvent", "repo": {"name": "a/b"}}))


class TextTest(unittest.TestCase):
    def test_fit_and_wrap_respect_width(self):
        f = svgkit.font("ui")
        long = "Finds payloads hidden in the least-significant bits of model weights " * 3
        for line in svgkit.wrap(long, "ui", 13, 300, max_lines=2):
            self.assertLessEqual(f.width(line, 13), 300.5)
        self.assertLessEqual(f.width(svgkit.fit(long, "ui", 13, 120), 13), 120.5)

    def test_unknown_glyphs_do_not_crash(self):
        svg = svgkit.Svg(100, 20, "t")
        svg.add(svg.text("emoji 🚀 and 日本", 0, 10))
        ET.fromstring(svg.render())


if __name__ == "__main__":
    unittest.main()
