"""Tests for tools/importers/cedict.py (no network, no wordfreq)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importers"))
import cedict  # noqa: E402


class Cedict(unittest.TestCase):
    def test_pinyin(self):
        cases = {"xie4 xie5": "xièxie", "ni3 hao3": "nǐhǎo", "nu:3 ren2": "nǚrén", "di4 er4 ci4": "dì'èrcì",
                 "gou3": "gǒu", "liu2": "liú", "hui4": "huì", "Xi1 an1": "Xī'ān"}
        for numbered, want in cases.items():
            self.assertEqual(cedict.pinyin(numbered), want, numbered)

    def test_senses(self):
        self.assertEqual(cedict.senses(["surname Wang", "king", "(bound form) best", "variant of 旺[wang4]"]), ["king", "best"])
        self.assertEqual(cedict.senses("to finish (used with 得[de2] or 無|无[wu2])"), ["to finish (used with 得 or 无)"])
        self.assertEqual(cedict.senses(["a move in chess (Taiwan pr. [zhuo2])"]), ["a move in chess"])

    def test_pick_prefers_listed_reading(self):
        cands = [("了", "le5", ["(completed action marker)"]), ("了", "liao3", ["to finish", "to understand", "a", "b"])]
        trad, py, s, others = cedict.pick(cands, "了")
        self.assertEqual(py, "le5")
        self.assertEqual([o[1] for o in others], ["liao3"])
        self.assertEqual(cedict.pick(cands, "x")[1], "liao3")

    def test_build(self):
        header = {"schema": "vocab@1", "language": "chinese", "notes": ["Written for this project."],
                  "decks": [{"id": "food", "title": "Food"}, {"id": "freq-core", "title": "old"}]}
        entries = [{"id": "food/茶", "deck": "food", "word": "茶", "reading": "chá", "meaning": "tea"},
                   {"id": "freq-core/旧", "deck": "freq-core", "word": "旧", "reading": "jiù", "meaning": "old"}]
        dic = cedict.index([["茶", "茶", "cha2", "tea", [], []], ["書", "书", "Shu1", "abbr. for 書經", [], []],
                            ["書", "书", "shu1", ["book", "letter"], [], []], ["王", "王", "Wang2", "surname Wang", [], []],
                            ["稀", "稀", "xi1", "rare", [], []]])
        band = {"茶": "core", "书": "core", "稀": "rare"}.get
        head, out = cedict.build(header, entries, ["的", "茶", "王", "书", "ok", "稀"], dic, band)
        self.assertEqual([d["id"] for d in head["decks"]], ["food", "freq-core"])
        self.assertEqual([e["id"] for e in out], ["food/茶", "freq-core/书"])
        self.assertEqual(out[0]["freq"], "core")
        self.assertEqual(out[1]["reading"], "shū")
        self.assertEqual(out[1]["note"], "Traditional: 書.")
        self.assertNotIn("level", out[0])  # no HSK level from frequency (#41)
        self.assertNotIn("level", out[1])
        placed = [dict(entries[0], level={"hsk": "1"})]
        self.assertEqual(cedict.build(head, placed, ["茶"], dic, band)[1][0]["level"], {"hsk": "1"})  # hand levels stay
        self.assertEqual(cedict.build(head, out, ["茶", "书"], dic, band)[1], out)


if __name__ == "__main__":
    unittest.main()
