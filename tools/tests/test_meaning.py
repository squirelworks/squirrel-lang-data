"""Tests for meaning@1, sentences@1, phrasings@1, columns@1,
tools/check_meaning.py and tools/gen_meaning.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_meaning  # noqa: E402
import check_schema  # noqa: E402
import gen_meaning  # noqa: E402
import lib  # noqa: E402

MEANINGS = [
    {"schema": "meaning@1"},
    {"id": "i", "kind": "content", "en": ["I", "me"], "group": "People"},
    {"id": "bus", "kind": "content", "en": ["bus"], "group": "Things"},
    {"id": "go", "kind": "content", "en": ["go", "went"], "group": "Doing"},
    {"id": "school", "kind": "content", "en": ["school"], "group": "Places"},
    {"id": "@means", "kind": "grammar", "label": "by means of", "en": ["by"], "group": "Grammar"},
    {"id": "@polite", "kind": "grammar", "label": "polite ending", "en": [], "group": "Grammar"},
]
SENTENCES = [
    {"schema": "sentences@1", "packs": [{"id": "travel", "title": "Getting around"}]},
    {"id": "go-bus", "pack": "travel", "en": "I go by bus.", "also": ["I take the bus."], "m": ["i", "bus", "go"]},
]
PHRASINGS = [
    {"schema": "phrasings@1"},
    {"m": "go", "with": ["bus"], "en": ["take", "ride"], "note": "Going by a vehicle."},
]
COLUMN = [
    {"schema": "columns@1", "language": "japanese", "notes": ["Written for this project."], "sep": ""},
    {"sentence": "go-bus", "t": [["バス", "バス", "bus"], ["で", "で", "@means"], ["行きます", "いきます", "go+@polite"]], "implied": ["i"], "end": "。"},
]


class Meaning(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        for name in ("meaning", "sentences", "phrasings", "columns"):
            src = lib.ROOT / "schemas" / f"{name}.v1.json"
            (self.root / "schemas" / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        (self.root / "languages" / "japanese").mkdir(parents=True)
        self.files = {}
        self.put("meanings.jsonl", MEANINGS)
        self.put("sentences.jsonl", SENTENCES)
        self.put("phrasings.jsonl", PHRASINGS)
        self.put("columns/japanese.jsonl", COLUMN)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, rows):
        p = self.root / "meaning" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        self.files[rel] = p
        return p

    def schema_problems(self):
        return [e for p in self.files.values() for e in check_schema.check_file(p, self.root)]

    def test_good_files(self):
        self.assertEqual(self.schema_problems(), [])
        self.assertEqual(check_meaning.check(self.root)[0], [])

    def test_schema_rejects(self):
        bad = {
            "grammar without a label": ("meanings.jsonl", MEANINGS + [{"id": "@x", "kind": "grammar", "en": []}]),
            "content id starting with @": ("meanings.jsonl", MEANINGS + [{"id": "@y", "kind": "content", "en": ["y"]}]),
            "content with no English": ("meanings.jsonl", MEANINGS + [{"id": "z", "kind": "content", "en": []}]),
            "phrasing with en and optional": ("phrasings.jsonl", [PHRASINGS[0], dict(PHRASINGS[1], optional=True)]),
            "phrasing with neither": ("phrasings.jsonl", [PHRASINGS[0], {"m": "go", "with": ["bus"]}]),
            "bad separator": ("columns/japanese.jsonl", [dict(COLUMN[0], sep="-"), COLUMN[1]]),
        }
        for what, (rel, rows) in bad.items():
            self.put(rel, rows)
            self.assertTrue(self.schema_problems(), what)
            self.setUp()

    def test_rules(self):
        cases = {
            "used twice": ("meanings.jsonl", MEANINGS + [MEANINGS[1]]),
            "not listed in the header": ("sentences.jsonl", SENTENCES + [dict(SENTENCES[1], id="x", pack="daily")]),
            "is not a content meaning": ("sentences.jsonl", [SENTENCES[0], dict(SENTENCES[1], m=["i", "@means"])]),
            "its own with list": ("phrasings.jsonl", [PHRASINGS[0], dict(PHRASINGS[1], **{"with": ["go"]})]),
            "should be 'japanese'": ("columns/japanese.jsonl", [dict(COLUMN[0], language="korean"), COLUMN[1]]),
            "rendered twice": ("columns/japanese.jsonl", COLUMN + [COLUMN[1]]),
            "not in sentences.jsonl": ("columns/japanese.jsonl", COLUMN + [dict(COLUMN[1], sentence="nope")]),
            "unknown meaning": ("columns/japanese.jsonl", [COLUMN[0], dict(COLUMN[1], t=[["バス", "バス", "bus"], ["行く", "いく", "go+walk"]])]),
            "drops i": ("columns/japanese.jsonl", [COLUMN[0], {k: v for k, v in COLUMN[1].items() if k != "implied"}]),
            "adds school": ("columns/japanese.jsonl", [COLUMN[0], dict(COLUMN[1], t=COLUMN[1]["t"] + [["学校", "がっこう", "school"]])]),
            "should be [text, reading, meanings]": ("columns/japanese.jsonl", [COLUMN[0], dict(COLUMN[1], t=[["バス", "バス", "bus", "x"]] + COLUMN[1]["t"][1:])]),
            "there is no languages/": ("columns/klingon.jsonl", [dict(COLUMN[0], language="klingon"), COLUMN[1]]),
        }
        for want, (rel, rows) in cases.items():
            self.put(rel, rows)
            found = "\n".join(check_meaning.check(self.root)[0])
            self.assertIn(want, found, want)
            self.setUp()

    def test_generator(self):
        files = gen_meaning.build(self.root, "cmd")
        self.assertEqual(sorted(files), ["japanese.js", "matrix.js"])
        m = files["matrix.js"]
        self.assertTrue(m.startswith("// Generated from squirrel-lang-data "))
        self.assertIn('  // People\n  "i": "I|me",', m)
        self.assertIn('"@means": "(by means of)by",', m)
        self.assertIn('"@polite": "(polite ending)",', m)
        self.assertIn('{"id": "go-bus", "pack": "travel", "en": "I go by bus.", "m": ["i", "bus", "go"], "also": ["I take the bus."]}', m)
        self.assertIn('  // Going by a vehicle.\n  {"m": "go", "with": ["bus"], "en": "take|ride"},', m)
        j = files["japanese.js"]
        self.assertIn("window.TL_LANGS.japanese = {\n  sep: \"\",\n  r: {", j)
        self.assertIn('"go-bus": {"end": "。", "implied": ["i"], "t": [["バス", "バス", "bus"]', j)
        self.assertIn("// Written for this project.", j)


if __name__ == "__main__":
    unittest.main()
