"""Tests for tools/importers/kana.py and tools/importers/jlpt_tanos.py (no network, no wordfreq)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importers"))
import jlpt_tanos  # noqa: E402
from kana import romaji  # noqa: E402


class Romaji(unittest.TestCase):
    def test_hepburn(self):
        cases = {
            "がっこう": "gakkō", "おおきい": "ōkii", "せんせい": "sensei", "きょう": "kyō",
            "じゅう": "jū", "ゆうびんきょく": "yūbinkyoku", "おばあさん": "obāsan",
            "きんえん": "kin'en", "こんや": "kon'ya", "まっちゃ": "matcha", "ちょっと": "chotto",
            "ラーメン": "rāmen", "パスポート": "pasupōto", "ティッシュ": "tisshu", "フォーク": "fōku",
        }
        for kana, want in cases.items():
            self.assertEqual(romaji(kana), want, kana)

    def test_verb_ending(self):
        self.assertEqual(romaji("おもう", verb=True), "omou")
        self.assertEqual(romaji("ありがとう"), "arigatō")


class Import(unittest.TestCase):
    def test_meaning(self):
        self.assertEqual(jlpt_tanos.meaning("greeting,salutation"), "greeting; salutation")
        self.assertEqual(jlpt_tanos.meaning("unfortunately,Sorry, but...."), "unfortunately; Sorry, but....")
        self.assertEqual(jlpt_tanos.meaning("remnant, fragment"), "remnant; fragment")
        self.assertEqual(jlpt_tanos.meaning("10,000 yen"), "10,000 yen")

    def test_build(self):
        header = {"schema": "vocab@1", "language": "japanese", "notes": ["Written for this project."],
                  "decks": [{"id": "people", "title": "People"}, {"id": "jlpt-n1", "title": "old"}]}
        entries = [
            {"id": "people/友達", "deck": "people", "word": "友達", "reading": "tomodachi", "meaning": "friend", "note": "ともだち"},
            {"id": "jlpt-n1/古い", "deck": "jlpt-n1", "word": "古い", "reading": "furui", "meaning": "old"},
        ]
        row = lambda kana, kanji, d: {"kana": kana, "kanji": kanji, "waller_definition": d}  # noqa: E731
        lists = {5: [row("ともだち", "友達", "friend"), row("あした", "明日", "tomorrow"), row("あす", "明日", "tomorrow"),
                     row("バツ", "ｘ", "")],
                 4: [row("あした", "明日", "tomorrow")], 3: [], 2: [], 1: [row("おもう", "思う", "to think")]}
        head, out, skipped = jlpt_tanos.build(header, entries, lists, lambda w: "common")
        self.assertEqual([d["id"] for d in head["decks"]], ["people", "jlpt-n5", "jlpt-n1"])
        self.assertEqual(head["source"], jlpt_tanos.SOURCE)
        self.assertEqual(skipped, 1)
        by_id = {e["id"]: e for e in out}
        self.assertEqual(by_id["people/友達"]["level"], {"jlpt": "N5"})
        self.assertNotIn("jlpt-n5/友達", by_id)
        self.assertNotIn("jlpt-n1/古い", by_id)
        self.assertEqual(by_id["jlpt-n5/明日"]["note"], "あした")
        self.assertEqual(by_id["jlpt-n5/明日/あす"]["reading"], "asu")
        self.assertEqual(by_id["jlpt-n1/思う"]["reading"], "omou")
        self.assertEqual(sum(e["word"] == "明日" for e in out), 2)
        self.assertTrue(all(e["freq"] == "common" for e in out))
        again = jlpt_tanos.build(head, out, lists, lambda w: "common")
        self.assertEqual(again[1], out)

    def test_kana_rows_and_greetings(self):
        header = {"schema": "vocab@1", "language": "japanese", "notes": [], "decks": [{"id": "food", "title": "Food"}]}
        entries = [
            {"id": "food/美味しい", "deck": "food", "word": "美味しい", "reading": "oishii", "meaning": "delicious",
             "note": "おいしい", "level": {"jlpt": "N1"}},
            {"id": "food/三", "deck": "food", "word": "三", "reading": "san", "meaning": "three", "note": "さん"},
            {"id": "food/こんにちは", "deck": "food", "word": "こんにちは", "reading": "konnichiwa", "meaning": "hello"},
        ]
        row = lambda kana, kanji, d: {"kana": kana, "kanji": kanji, "waller_definition": d}  # noqa: E731
        lists = {5: [row("おいしい", "", "delicious"), row("さん", "", "Mr or Mrs")], 4: [],
                 3: [row("こんにちは", "", "hello"), row("ありがとう", "", "Thank you")], 2: [],
                 1: [row("おいしい", "美味しい", "delicious,tasty"), row("こんにちは", "今日は", "hello")]}
        head, out, _ = jlpt_tanos.build(header, entries, lists, lambda w: "common")
        by_id = {e["id"]: e for e in out}
        self.assertEqual(by_id["food/美味しい"]["level"], {"jlpt": "N5"})
        self.assertNotIn("level", by_id["food/三"])
        self.assertIn("jlpt-n5/さん", by_id)
        self.assertEqual(by_id["food/こんにちは"]["level"], {"jlpt": "N5"})
        self.assertIn("jlpt-n5/ありがとう", by_id)
        self.assertEqual(by_id["jlpt-n1/今日は"]["reading"], "konnichiwa")


if __name__ == "__main__":
    unittest.main()
