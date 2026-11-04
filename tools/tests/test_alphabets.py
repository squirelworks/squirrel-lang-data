"""Tests for alphabet@1, tools/check_alphabets.py and tools/gen_alphabets.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_alphabets  # noqa: E402
import check_schema  # noqa: E402
import gen_alphabets  # noqa: E402
import lib  # noqa: E402

CARD = {"char": "Γ γ", "roman": "g", "hint": "gamma", "example": "γάλα", "exampleRoman": "gála", "meaning": "milk",
        "speak": "", "ipa": "ɣ"}
COURSE = {"schema": "alphabet@1", "id": "greek", "title": "Greek", "native": "Ελληνικά", "lang": "el-GR", "langName": "Greek",
          "font": "\"Noto Sans\", sans-serif", "blurb": "24 letters.", "writeTip": "Top to bottom.",
          "notes": ["Hints are original."],
          "lessons": [{"title": "First letters", "group": "Letters", "cols": 4,
                       "chars": [CARD, None, {k: v for k, v in CARD.items() if k != "ipa"} | {"char": "Δ δ"}]}],
          "articles": [{"title": "About", "body": "<p>Greek.</p>"}]}
STROKES = [{"schema": "strokes@1", "set": "greek", "box": 100, "source": "Noto fonts", "license": "OFL"},
           *[{"char": c, "strokes": ["M1,1 L2,2"]} for c in "ΓγΔδ"]]


class Alphabets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "alphabet.v1.json").write_text((lib.ROOT / "schemas" / "alphabet.v1.json").read_text(encoding="utf-8"))
        (self.root / "strokes").mkdir()
        (self.root / "strokes" / "greek.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in STROKES), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, course, name="greek"):
        p = self.root / "alphabets" / f"{name}.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
        return p

    def test_good_file(self):
        p = self.write(COURSE)
        self.assertEqual(check_schema.check_file(p, self.root), [])
        self.assertEqual(check_alphabets.check(self.root), [])

    def test_schema_rejects(self):
        lesson = COURSE["lessons"][0]
        for bad in (dict(COURSE, dir="ltr"), dict(COURSE, lessons=[dict(lesson, forms=True)]),
                    dict(COURSE, lessons=[dict(lesson, chars=[{"char": "Γ"}])]), {k: v for k, v in COURSE.items() if k != "font"}):
            self.assertTrue(check_schema.check_file(self.write(bad), self.root), bad)

    def test_rules(self):
        lesson = COURSE["lessons"][0]
        cases = {
            "should be 'greek'": dict(COURSE, id="latin"),
            "taught twice": dict(COURSE, lessons=[lesson, lesson]),
            "no strokes": dict(COURSE, lessons=[dict(lesson, chars=[dict(CARD, char="Ζ ζ")])]),
            "isn't right to left": dict(COURSE, nonJoining="Γ"),
        }
        for want, course in cases.items():
            self.write(course)
            got = check_alphabets.check(self.root)
            self.assertTrue(any(want in p for p in got), f"{want}: {got}")
        (self.root / "strokes" / "greek.jsonl").unlink()
        self.write(COURSE)
        self.assertTrue(any("is missing" in p for p in check_alphabets.check(self.root)))

    def test_card(self):
        self.assertEqual(gen_alphabets.card(CARD), ["Γ γ", "g", "gamma", "γάλα", "gála", "milk", "", "ɣ"])
        self.assertEqual(gen_alphabets.card({"char": "A", "roman": "a", "hint": "", "example": "", "exampleRoman": "",
                                             "meaning": "", "speak": "", "exampleIpa": "a"}),
                         ["A", "a", "", "", "", "", "", "", "", "a"])
        self.assertIsNone(gen_alphabets.card(None))

    @unittest.skipUnless(subprocess.run(["which", "node"], capture_output=True).returncode == 0, "needs node")
    def test_generate(self):
        self.write(COURSE)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        apps = self.root / "apps"
        self.assertEqual(gen_alphabets.main(["--data", str(self.root), "--apps", str(apps)]), 0)
        self.assertEqual(gen_alphabets.main(["--data", str(self.root), "--apps", str(apps), "--check"]), 0)
        f = apps / gen_alphabets.OUT / "greek.js"
        js = f"global.window = global; eval(require('fs').readFileSync({json.dumps(str(f))}, 'utf8')); process.stdout.write(JSON.stringify(SG_SCRIPTS))"
        got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(len(got), 1)
        self.assertNotIn("schema", got[0])
        self.assertEqual(got[0]["lessons"][0]["chars"], [gen_alphabets.card(CARD), None, ["Δ δ", "g", "gamma", "γάλα", "gála", "milk", ""]])
        self.assertEqual(got[0]["articles"], COURSE["articles"])
        f.write_text("stale\n", encoding="utf-8")
        self.assertEqual(gen_alphabets.main(["--data", str(self.root), "--apps", str(apps), "--check"]), 1)


if __name__ == "__main__":
    unittest.main()
