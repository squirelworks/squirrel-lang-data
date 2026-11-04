"""Tests for vocab@1, tools/check_vocab.py and tools/gen_vocab.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_schema  # noqa: E402
import check_vocab  # noqa: E402
import gen_vocab  # noqa: E402
import lib  # noqa: E402

HEADER = {"schema": "vocab@1", "language": "greek", "notes": ["Written for this project."],
          "decks": [{"id": "greetings", "title": "Greetings"}, {"id": "food", "title": "Food"}]}
WORDS = [
    {"id": "greetings/γεια", "deck": "greetings", "word": "γεια", "reading": "giá", "meaning": "hi"},
    {"id": "food/ψωμί", "deck": "food", "word": "ψωμί", "reading": "psomí", "meaning": "bread",
     "note": "Neuter.", "level": {"cefr": "A1"}, "freq": "core"},
]


class Vocab(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "vocab.v1.json").write_text((lib.ROOT / "schemas" / "vocab.v1.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, header, words, lang="greek"):
        p = self.root / "languages" / lang / "vocab.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [header] + words), encoding="utf-8")
        return p

    def problems(self, p):
        return check_schema.check_file(p, self.root) + check_vocab.check(self.root)[0]

    def test_good_file(self):
        self.assertEqual(self.problems(self.write(HEADER, WORDS)), [])
        self.assertEqual(check_vocab.check(self.root)[1], {"greek": 1})

    def test_schema_rejects(self):
        self.assertTrue(self.problems(self.write(HEADER, [dict(WORDS[0], freq="often")])))
        self.assertTrue(self.problems(self.write(HEADER, [dict(WORDS[0], meaning="")])))
        self.assertTrue(self.problems(self.write(dict(HEADER, decks=[]), [])))

    def test_rules(self):
        cases = {
            "should be 'greek'": (dict(HEADER, language="latin"), WORDS),
            "not listed in the header": (HEADER, WORDS + [dict(WORDS[0], id="x/y", deck="verbs")]),
            "used twice": (HEADER, WORDS + [WORDS[1]]),
            "header order": (HEADER, list(reversed(WORDS))),
            "has no words": (HEADER, WORDS[:1]),
            "or none": (HEADER, [WORDS[0], {k: v for k, v in WORDS[1].items() if k != "reading"}]),
            "doesn't exist": (HEADER, [WORDS[0], dict(WORDS[1], varieties=["koine"])]),
        }
        for want, (header, words) in cases.items():
            p = self.write(header, words)
            found = "\n".join(check_vocab.check(self.root)[0])
            self.assertIn(want, found, want)
            p.unlink()

    def test_generator_shapes(self):
        self.write(HEADER, WORDS)
        latin = {"schema": "vocab@1", "language": "latin", "decks": [{"id": "verbs", "title": "Verbs"}]}
        self.write(latin, [{"id": "verbs/amō", "deck": "verbs", "word": "amō", "meaning": "I love"}], "latin")
        files = gen_vocab.build(self.root, "cmd")
        for lang, want in (("greek", [["γεια", "giá", "hi", ""]]), ("latin", [["amō", "I love", ""]])):
            text = files[f"{lang}/vocab.js"]
            self.assertTrue(text.startswith("// Generated from squirrel-lang-data "))
            body = text.split(f"window.LSD_DECKS.{lang} =", 1)[1].strip().rstrip(";")
            self.assertEqual(json.loads(body)[0]["words"], want)
        self.assertIn("// Written for this project.", files["greek/vocab.js"])


if __name__ == "__main__":
    unittest.main()
