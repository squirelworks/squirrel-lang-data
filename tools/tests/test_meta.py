"""Tests for the meta@1 and variety@1 schemas and tools/check_meta.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_meta  # noqa: E402
import check_schema  # noqa: E402
import lib  # noqa: E402
import schema as js  # noqa: E402

META = lib.load_schema("meta.v1.json")
VARIETY = lib.load_schema("variety.v1.json")

GREEK = {
    "schema": "meta@1", "id": "greek", "name": "Greek", "nativeName": "Ελληνικά",
    "code": "ell", "scripts": ["greek"], "characterKeys": ["greek"],
}
ANCIENT = {
    "schema": "variety@1", "id": "ancient-greek", "parent": "greek", "kind": "historical",
    "name": "Ancient Greek", "code": "grc", "period": {"label": "Classical", "from": -800, "to": -300},
}
CANTONESE = {
    "schema": "variety@1", "id": "cantonese", "parent": "chinese", "kind": "regional",
    "name": "Cantonese", "code": "yue", "romanization": ["jyutping"],
}


def with_(base, **changes):
    out = dict(base)
    for k, v in changes.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
    return out


class MetaSchema(unittest.TestCase):
    def ok(self, data, schema):
        self.assertEqual(js.errors(data, schema), [])

    def bad(self, data, schema):
        self.assertNotEqual(js.errors(data, schema), [])

    def test_standard_language(self):
        self.ok(GREEK, META)
        self.ok(with_(GREEK, varieties=["ancient-greek"], speech="el-GR", direction="ltr"), META)

    def test_standard_language_needs_its_fields(self):
        for k in ("id", "name", "nativeName", "code", "scripts", "characterKeys"):
            self.bad(with_(GREEK, **{k: None}), META)

    def test_language_has_no_variety_fields(self):
        self.bad(with_(GREEK, parent="x"), META)
        self.bad(with_(GREEK, kind="standard"), META)
        self.bad(with_(GREEK, data={"vocab": "vocab.js"}), META)

    def test_codes(self):
        self.ok(with_(GREEK, code="nucl1310"), META)  # Glottolog
        for code in ("el", "ELL", "ellx", "nucl131", "e11"):
            self.bad(with_(GREEK, code=code), META)

    def test_order_schema(self):
        self.ok(with_(GREEK, order="SOV"), META)
        self.bad(with_(GREEK, order="sideways"), META)

    def test_markers(self):
        self.ok(with_(GREEK, markers={"default": "before"}), META)
        self.ok(with_(GREEK, markers={"default": "before", "@possessive": "after"}), META)
        self.bad(with_(GREEK, markers={"@possessive": "after"}), META)  # needs default
        self.bad(with_(GREEK, markers={"default": "left"}), META)
        self.bad(with_(GREEK, markers={"default": "before", "@the": "around"}), META)

    def test_regional_variety(self):
        self.ok(CANTONESE, VARIETY)
        self.bad(with_(CANTONESE, parent=None), VARIETY)
        self.bad(with_(CANTONESE, kind="dialect"), VARIETY)
        self.bad(with_(CANTONESE, period={"label": "now"}), VARIETY)
        self.bad(with_(CANTONESE, reconstructed=True), VARIETY)

    def test_historical_stage(self):
        self.ok(ANCIENT, VARIETY)
        self.ok(with_(ANCIENT, reconstructed=True), VARIETY)
        self.bad(with_(ANCIENT, period=None), VARIETY)
        self.bad(with_(ANCIENT, period={"from": -800}), VARIETY)
        self.bad(with_(ANCIENT, period={"label": "x", "from": "800 BCE"}), VARIETY)

    def test_variety_overrides_only(self):
        # Everything beyond the required fields is optional and inherited.
        self.ok(with_(ANCIENT, scripts=["greek"], notes="Polytonic spelling."), VARIETY)
        self.bad(with_(ANCIENT, schema="meta@1"), VARIETY)


class MetaFolders(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        for name in ("meta.v1.json", "variety.v1.json"):
            (self.root / "schemas" / name).write_text((lib.ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, data):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p

    def problems(self):
        out = check_meta.check(self.root)
        for p in lib.content_files(self.root):
            out += check_schema.check_file(p, self.root)
        return out

    def test_good_tree(self):
        self.write("languages/greek/meta.json", with_(GREEK, varieties=["ancient-greek", "attic"]))
        self.write("languages/greek/varieties/ancient-greek/meta.json", ANCIENT)
        self.write("languages/greek/varieties/attic/meta.json",
                   with_(ANCIENT, id="attic", parent="ancient-greek", name="Attic Greek", code="atti1240"))
        self.assertEqual(self.problems(), [])

    def test_id_must_match_folder(self):
        self.write("languages/hellenic/meta.json", GREEK)
        self.assertTrue(any("folder" in p for p in self.problems()))

    def test_duplicate_ids(self):
        self.write("languages/greek/meta.json", with_(GREEK, varieties=["latin"]))
        self.write("languages/greek/varieties/latin/meta.json", with_(ANCIENT, id="latin"))
        self.write("languages/latin/meta.json", with_(GREEK, id="latin"))
        self.assertTrue(any("already used" in p for p in self.problems()))

    def test_unlisted_and_missing_varieties(self):
        self.write("languages/greek/meta.json", with_(GREEK, varieties=["koine"]))
        self.write("languages/greek/varieties/ancient-greek/meta.json", ANCIENT)
        found = "\n".join(self.problems())
        self.assertIn("varieties/ancient-greek/ is not listed", found)
        self.assertIn("varieties/koine/ doesn't exist", found)

    def test_variety_parent_must_be_its_language(self):
        self.write("languages/greek/meta.json", with_(GREEK, varieties=["cantonese"]))
        self.write("languages/greek/varieties/cantonese/meta.json", CANTONESE)
        self.assertTrue(any("parent 'chinese'" in p for p in self.problems()))

    def test_parent_loop(self):
        self.write("languages/greek/meta.json", with_(GREEK, varieties=["a", "b"]))
        self.write("languages/greek/varieties/a/meta.json", with_(ANCIENT, id="a", parent="b"))
        self.write("languages/greek/varieties/b/meta.json", with_(ANCIENT, id="b", parent="a"))
        self.assertTrue(any("loop" in p for p in self.problems()))

    def test_folder_without_meta(self):
        (self.root / "languages" / "empty").mkdir(parents=True)
        self.assertTrue(any("no meta.json" in p for p in self.problems()))

    def test_unknown_schema(self):
        self.write("languages/greek/meta.json", with_(GREEK, schema="meta@9"))
        self.assertTrue(any("schemas/meta.v9.json" in p for p in self.problems()))

    def test_markers_must_name_grammar_meanings(self):
        (self.root / "meaning").mkdir()
        (self.root / "meaning" / "meanings.jsonl").write_text(
            '{"schema": "meaning@1"}\n'
            '{"id": "@possessive", "kind": "grammar", "label": "possessive"}\n'
            '{"id": "cat", "kind": "content", "en": ["cat"]}\n', encoding="utf-8")
        self.write("languages/greek/meta.json",
                   with_(GREEK, markers={"default": "before", "@possessive": "after"}))
        self.assertEqual(check_meta.check(self.root), [])
        for bad in ("cat", "@nothing"):
            self.write("languages/greek/meta.json", with_(GREEK, markers={"default": "before", bad: "after"}))
            self.assertTrue(any("isn't a grammar meaning" in p for p in check_meta.check(self.root)), bad)

    def test_cases_name_meanings_and_grammar_cases(self):
        (self.root / "meaning").mkdir()
        (self.root / "meaning" / "meanings.jsonl").write_text(
            '{"schema": "meaning@1"}\n'
            '{"id": "@object", "kind": "grammar", "label": "object"}\n'
            '{"id": "@accusative", "kind": "grammar", "label": "accusative"}\n'
            '{"id": "from", "kind": "content", "en": ["from"]}\n', encoding="utf-8")
        self.write("languages/greek/meta.json",
                   with_(GREEK, cases={"@object": "@accusative", "from": "@accusative"}, order="SVO"))
        self.assertEqual(check_meta.check(self.root), [])
        self.write("languages/greek/meta.json", with_(GREEK, cases={"@nothing": "@accusative"}))
        self.assertTrue(any("isn't a meaning" in p for p in check_meta.check(self.root)))
        self.write("languages/greek/meta.json", with_(GREEK, cases={"@object": "from"}))
        self.assertTrue(any("isn't a grammar meaning" in p for p in check_meta.check(self.root)))


if __name__ == "__main__":
    unittest.main()
