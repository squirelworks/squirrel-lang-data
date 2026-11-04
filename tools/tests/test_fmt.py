"""Tests for tools/fmt.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import fmt  # noqa: E402
import lib  # noqa: E402


class Format(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "meta.v1.json").write_text((lib.ROOT / "schemas" / "meta.v1.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_schema_key_order_and_short_lists(self):
        p = self.root / "meta.json"
        p.write_text(json.dumps({"code": "ell", "id": "greek", "zzz": 1, "schema": "meta@1", "scripts": ["greek"]}))
        self.assertEqual(fmt.format_file(p, self.root),
                         '{\n  "schema": "meta@1",\n  "id": "greek",\n  "code": "ell",\n'
                         '  "scripts": ["greek"],\n  "zzz": 1\n}\n')

    def test_long_lists_and_objects_wrap(self):
        self.assertEqual(fmt.dumps([{"a": 1}]), '[\n  {\n    "a": 1\n  }\n]')
        long = ["x" * 30] * 3
        self.assertTrue(fmt.dumps({"k": long}).startswith('{\n  "k": [\n'))

    def test_jsonl_one_entry_per_line(self):
        p = self.root / "list.jsonl"
        p.write_text('{"schema": "list@1"}\n\n{"b": 2,\n "a": "é"}\n'.replace(",\n", ", "))
        self.assertEqual(fmt.format_file(p, self.root), '{"schema": "list@1"}\n{"b": 2, "a": "é"}\n')


if __name__ == "__main__":
    unittest.main()
