"""Tests for the inflections@1 schema and tools/check_inflections.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_inflections  # noqa: E402
import lib  # noqa: E402
import schema as js  # noqa: E402

SCHEMA = lib.load_schema("inflections.v1.json")
ENTRY = SCHEMA["properties"]["entry"]
HEADER = {"schema": "inflections@1", "language": "japanese"}
GO = {
    "lemma": "行く", "reading": "いく", "m": "go", "class": "godan",
    "forms": [
        {"name": "dictionary", "text": "行く", "reading": "いく", "features": ["@present"]},
        {"name": "polite-past", "text": "行きました", "reading": "いきました", "features": ["@polite", "@past"]},
        {"name": "negative", "text": "行かない", "reading": "いかない", "features": ["@present", "not"]},
    ],
}
MEANINGS = [
    {"schema": "meaning@1"},
    {"id": "go", "kind": "content"}, {"id": "not", "kind": "content"},
    {"id": "@present", "kind": "grammar"}, {"id": "@past", "kind": "grammar"},
    {"id": "@polite", "kind": "grammar"},
]


def problems(*words, folder="japanese", header=HEADER):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "meaning").mkdir()
        (root / "meaning" / "meanings.jsonl").write_text(
            "\n".join(json.dumps(m) for m in MEANINGS) + "\n", encoding="utf-8")
        lang = root / "languages" / folder
        lang.mkdir(parents=True)
        (lang / "inflections.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in (header, *words)) + "\n", encoding="utf-8")
        return check_inflections.check(root)


def with_forms(word, *forms):
    return {**word, "forms": list(forms)}


class SchemaTest(unittest.TestCase):
    def test_a_word_follows_the_schema(self):
        self.assertEqual(js.errors(GO, ENTRY, SCHEMA), [])

    def test_a_form_needs_features_even_when_empty(self):
        bad = with_forms(GO, {"name": "stem", "text": "行き"})
        self.assertNotEqual(js.errors(bad, ENTRY, SCHEMA), [])

    def test_feature_ids_look_like_meaning_ids(self):
        bad = with_forms(GO, {"name": "dictionary", "text": "行く", "features": ["Past"]})
        self.assertNotEqual(js.errors(bad, ENTRY, SCHEMA), [])


class CheckTest(unittest.TestCase):
    def test_good_table_passes(self):
        self.assertEqual(problems(GO), [])

    def test_language_must_match_folder(self):
        self.assertTrue(any("not the folder" in p for p in problems(GO, folder="hangul")))

    def test_m_must_be_a_content_meaning(self):
        self.assertTrue(any("is not a meaning" in p for p in problems({**GO, "m": "walk"})))
        self.assertTrue(any("grammar meaning" in p for p in problems({**GO, "m": "@past"})))

    def test_features_must_be_meanings(self):
        bad = with_forms(GO, GO["forms"][0], {"name": "te", "text": "行って", "features": ["@gerund"]})
        self.assertTrue(any("'@gerund' is not a meaning" in p for p in problems(bad)))

    def test_dictionary_form_is_the_lemma(self):
        self.assertTrue(any("no form named dictionary" in p for p in problems(with_forms(GO, GO["forms"][1]))))
        wrong = with_forms(GO, {**GO["forms"][0], "text": "いく"})
        self.assertTrue(any("not the lemma" in p for p in problems(wrong)))

    def test_no_duplicates(self):
        self.assertTrue(any("listed twice" in p for p in problems(GO, GO)))
        twice = with_forms(GO, GO["forms"][0], GO["forms"][0])
        self.assertTrue(any("two forms 'dictionary'" in p for p in problems(twice)))

    def test_repo_tables_pass(self):
        self.assertEqual(check_inflections.check(), [])


if __name__ == "__main__":
    unittest.main()
