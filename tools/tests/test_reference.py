"""Tests for reference@1, tools/check_reference.py and tools/gen_reference.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_reference  # noqa: E402
import check_schema  # noqa: E402
import gen_reference  # noqa: E402
import lib  # noqa: E402

CARD = {"id": "wa-ga", "topic": "grammar", "title": "は and が", "level": "beginner",
        "body": ["Paragraph with {highlight}."], "examples": [{"t": "私{は}学生です。", "r": "watashi wa", "e": "I'm a student."}],
        "table": {"head": ["Particle", "Marks"], "rows": [["を", "object"]]}, "tags": ["particles"], "sources": ["Wiktionary"]}
REF = {"schema": "reference@1", "language": "japanese", "entries": [CARD]}


class Reference(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "reference.v1.json").write_text((lib.ROOT / "schemas" / "reference.v1.json").read_text(encoding="utf-8"))
        (self.root / "SOURCES.md").write_text("| Source | Used for |\n|---|---|\n| Wiktionary | x |\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, ref):
        p = self.root / "languages" / "japanese" / "reference.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(ref, ensure_ascii=False), encoding="utf-8")
        return p

    def test_good(self):
        p = self.write(REF)
        self.assertEqual(check_schema.check_file(p, self.root) + check_reference.check(self.root)[0], [])
        self.assertEqual(check_schema.check_file(self.write(dict(REF, entries=[dict(CARD, body="One paragraph.")])), self.root), [])

    def test_schema_rejects(self):
        for bad in (dict(CARD, topic="history"), dict(CARD, level="expert"), dict(CARD, examples=[{"r": "x"}])):
            self.assertTrue(check_schema.check_file(self.write(dict(REF, entries=[bad])), self.root), bad)

    def test_rules(self):
        cases = {
            "should be 'japanese'": dict(REF, language="korean"),
            "used twice": dict(REF, entries=[CARD, CARD]),
            "has 1 cells": dict(REF, entries=[dict(CARD, table={"head": ["a", "b"], "rows": [["x"]]})]),
            "isn't listed": dict(REF, entries=[dict(CARD, sources=["Nowhere"])]),
        }
        for want, ref in cases.items():
            self.write(ref)
            self.assertIn(want, "\n".join(check_reference.check(self.root)[0]), want)

    def test_generator(self):
        self.write(REF)
        out = json.loads(gen_reference.build(self.root)["japanese/reference.json"])
        self.assertEqual(out, {"id": "japanese", "entries": [CARD]})


if __name__ == "__main__":
    unittest.main()
