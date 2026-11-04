"""Tests for vocab-links@1, tools/check_vocab_links.py and
tools/gen_vocab_links.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_schema  # noqa: E402
import check_vocab_links  # noqa: E402
import gen_vocab_links  # noqa: E402
import lib  # noqa: E402

MEANINGS = [
    {"schema": "meaning@1"},
    {"id": "i", "kind": "content", "en": ["I", "me"]},
    {"id": "go", "kind": "content", "en": ["go", "went"]},
    {"id": "@polite", "kind": "grammar", "label": "polite ending", "en": []},
]
VOCAB = [
    {"schema": "vocab@1", "language": "hangul", "decks": [{"id": "people", "title": "People"}, {"id": "verbs", "title": "Verbs"}]},
    {"id": "people/저", "deck": "people", "word": "저", "reading": "jeo", "meaning": "I (humble)"},
    {"id": "verbs/가요", "deck": "verbs", "word": "가요", "reading": "gayo", "meaning": "go (polite)"},
]
LINKS = [
    {"schema": "vocab-links@1", "language": "hangul", "notes": ["Written for this project."]},
    {"vocab": "people/저", "meanings": ["i"]},
    {"vocab": "verbs/가요", "meanings": ["go"]},
]
COLUMN = [
    {"schema": "columns@1", "language": "hangul", "sep": " "},
    {"sentence": "i-go", "t": [["저", "jeo", "i"], ["가요", "gayo", "go+@polite"]], "end": "."},
]


class VocabLinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        src = lib.ROOT / "schemas" / "vocab-links.v1.json"
        (self.root / "schemas" / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        self.put("meaning/meanings.jsonl", MEANINGS)
        self.put("languages/hangul/vocab.jsonl", VOCAB)
        self.links = self.put("meaning/vocab-links/hangul.jsonl", LINKS)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, rows):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return p

    def test_good_file(self):
        self.assertEqual(check_schema.check_file(self.links, self.root), [])
        self.assertEqual(check_vocab_links.check(self.root), ([], []))

    def test_schema_rejects(self):
        bad = {
            "no meanings": {"vocab": "people/저", "meanings": []},
            "vocab id without a deck": {"vocab": "저", "meanings": ["i"]},
            "extra field": {"vocab": "people/저", "meanings": ["i"], "level": "A1"},
            "meaning listed twice": {"vocab": "people/저", "meanings": ["i", "i"]},
        }
        for what, row in bad.items():
            self.put("meaning/vocab-links/hangul.jsonl", [LINKS[0], row])
            self.assertTrue(check_schema.check_file(self.links, self.root), what)

    def test_rules(self):
        cases = {
            "should be 'hangul'": [dict(LINKS[0], language="korean")] + LINKS[1:],
            "is not in languages/hangul/vocab.jsonl": LINKS + [{"vocab": "people/나", "meanings": ["i"]}],
            "is linked twice": LINKS + [LINKS[2]],
            "is out of order": [LINKS[0], LINKS[2], LINKS[1]],
            "'@polite' is not a content meaning": [LINKS[0], {"vocab": "people/저", "meanings": ["i", "@polite"]}],
            "'walk' is not a content meaning": [LINKS[0], {"vocab": "people/저", "meanings": ["walk"]}],
        }
        for want, rows in cases.items():
            self.put("meaning/vocab-links/hangul.jsonl", rows)
            self.assertIn(want, "\n".join(check_vocab_links.check(self.root)[0]), want)
        self.put("meaning/vocab-links/klingon.jsonl", [dict(LINKS[0], language="klingon")])
        self.assertIn("there is no languages/klingon/vocab.jsonl", "\n".join(check_vocab_links.check(self.root)[0]))

    def test_reports_unlinked_column_words(self):
        self.put("meaning/columns/hangul.jsonl", COLUMN)
        self.assertEqual(check_vocab_links.check(self.root), ([], []))
        self.put("meaning/vocab-links/hangul.jsonl", LINKS[:2])
        problems, info = check_vocab_links.check(self.root)
        self.assertEqual(problems, [])
        self.assertIn("verbs/가요 (go)", "\n".join(info))

    def test_generator(self):
        files = gen_vocab_links.build(self.root, "cmd")
        self.assertEqual(sorted(files), ["vocab-links.js"])
        text = files["vocab-links.js"]
        self.assertTrue(text.startswith("// Generated from squirrel-lang-data "))
        self.assertIn('window.TL_VOCAB_LINKS = {\n  "hangul": {\n    "people/저": ["i"],\n    "verbs/가요": ["go"],\n  },\n};', text)


if __name__ == "__main__":
    unittest.main()
