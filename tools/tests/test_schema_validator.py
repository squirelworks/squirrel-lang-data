"""tools/schema.py agrees with the jsonschema package on this repo's schemas,
when that package is installed (it isn't needed to run the checks)."""
import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import lib  # noqa: E402
import schema as js  # noqa: E402

try:
    import jsonschema
except ImportError:
    jsonschema = None

SAMPLES = [
    {}, [], "x", 1, None,
    {"schema": "meta@1"},
    {"schema": "variety@1", "id": "a", "parent": "b", "kind": "historical", "name": "A", "code": "abc"},
    {"schema": "variety@1", "id": "a", "parent": "b", "kind": "regional", "name": "A", "code": "abc",
     "period": {"label": "x"}},
    {"schema": "meta@1", "id": "a", "name": "A", "nativeName": "A", "code": "abc", "scripts": ["x", "x"],
     "characterKeys": []},
    {"schema": "meta@1", "id": "A", "name": "", "nativeName": "A", "code": "abcd1234", "scripts": [],
     "characterKeys": [], "direction": "up", "extra": 1},
]


class Validator(unittest.TestCase):
    def test_types(self):
        self.assertEqual(js.errors(True, {"type": "integer"}), ["(top level): should be integer"])
        self.assertEqual(js.errors(3, {"type": ["string", "integer"]}), [])

    def test_unsupported_keyword_is_an_error(self):
        with self.assertRaises(ValueError):
            js.errors(1, {"maximum": 3})
        self.assertEqual(js.unknown_keywords({"properties": {"a": {"items": {"format": "date"}}}}), ["format"])

    def test_every_repo_schema_is_supported(self):
        for p in sorted((lib.ROOT / "schemas").glob("*.json")):
            self.assertEqual(js.unknown_keywords(json.loads(p.read_text(encoding="utf-8"))), [], p.name)

    @unittest.skipIf(jsonschema is None, "jsonschema not installed")
    def test_agrees_with_jsonschema(self):
        for p in sorted((lib.ROOT / "schemas").glob("*.json")):
            schema = json.loads(p.read_text(encoding="utf-8"))
            ref = jsonschema.Draft202012Validator(schema)
            for sample in SAMPLES + [json.loads(f.read_text(encoding="utf-8")) for f in lib.content_files()]:
                self.assertEqual(not js.errors(sample, schema), ref.is_valid(sample), (p.name, sample))


if __name__ == "__main__":
    unittest.main()
