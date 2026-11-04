"""Tests for grammar@1, tools/check_grammar.py and tools/gen_grammar.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_grammar  # noqa: E402
import check_schema  # noqa: E402
import gen_grammar  # noqa: E402
import lib  # noqa: E402

DRILL = {"q": "＿ φοιτητής.", "en": "I am a student.", "options": ["Είμαι", "Είσαι"], "answer": "Είμαι", "why": "I."}
LESSON = {"id": "eimai", "title": "To be", "level": "absolute-beginner",
          "sections": [{"p": "The ending says who.", "examples": [["{Είμαι} εδώ.", "Íme edó.", "I am here."]]}],
          "drills": [DRILL]}
COURSE = {"schema": "grammar@1", "language": "greek", "notes": ["Written for this project.", ""],
          "title": "Greek first grammar", "intro": "Intro.", "lessons": [LESSON],
          "plan": [{"id": "aorist", "title": "The simple past", "level": "beginner", "after": ["eimai"]}]}


class Grammar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "grammar.v1.json").write_text((lib.ROOT / "schemas" / "grammar.v1.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, course, lang="greek"):
        p = self.root / "languages" / lang / "grammar.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
        return p

    def test_good_course(self):
        p = self.write(COURSE)
        self.assertEqual(check_schema.check_file(p, self.root) + check_grammar.check(self.root)[0], [])

    def test_schema_rejects(self):
        for bad in (dict(LESSON, level="expert"), dict(LESSON, sections=[]), dict(LESSON, drills=[dict(DRILL, options=["a"])])):
            p = self.write(dict(COURSE, lessons=[bad]))
            self.assertTrue(check_schema.check_file(p, self.root), bad)

    def test_rules(self):
        cases = {
            "should be 'greek'": dict(COURSE, language="latin"),
            "used twice": dict(COURSE, lessons=[LESSON, LESSON]),
            "not one of its options": dict(COURSE, lessons=[dict(LESSON, drills=[dict(DRILL, answer="Είναι")])]),
            "reuses an id": dict(COURSE, plan=[{"id": "eimai", "title": "Again"}]),
            "isn't a lesson": dict(COURSE, plan=[{"id": "x", "title": "X", "after": ["nope"]}]),
            "no drillData": dict(COURSE, lessons=[dict(LESSON, generate={"kind": "none", "count": 3})]),
        }
        for want, course in cases.items():
            self.write(course)
            self.assertIn(want, "\n".join(check_grammar.check(self.root)[0]), want)

    def test_generator(self):
        self.write(COURSE)
        self.write(dict(COURSE, language="klingon", drillData={"SUBJECTS": ["I"]}), "klingon")
        files = gen_grammar.build(self.root, "cmd")
        greek = files["greek/grammar.js"]
        self.assertIn("\n// Written for this project.\n//\n", greek)
        body = json.loads(greek.split("window.GRAMMAR.greek =", 1)[1].strip().rstrip(";"))
        self.assertEqual(list(body), ["title", "intro", "lessons", "plan"])
        self.assertIn('window.KLINGON_GRID = {\n  "SUBJECTS": [\n    "I"\n  ]\n};', files["klingon/grammar.js"])


if __name__ == "__main__":
    unittest.main()
