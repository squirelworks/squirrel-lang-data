"""Tests for tools/importers/hangul.py, freq.py and krdict.py (no network, no wordfreq)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importers"))
import freq  # noqa: E402
import krdict  # noqa: E402
from hangul import romanize  # noqa: E402


class Romanize(unittest.TestCase):
    def test_revised_romanization(self):
        cases = {
            "한국어": "hangugeo", "감사합니다": "gamsahamnida", "고맙습니다": "gomapseumnida",
            "안녕히 가세요": "annyeonghi gaseyo", "괜찮아요": "gwaenchanayo", "같이": "gachi",
            "시작하다": "sijakhada", "좋다": "jota", "신라": "silla", "설날": "seollal", "독립": "dongnip",
            "종로": "jongno", "학교": "hakgyo", "국물": "gungmul", "몰라요": "mollayo", "값이": "gapsi",
            "라면": "ramyeon",
        }
        for word, want in cases.items():
            self.assertEqual(romanize(word), want, word)


class Freq(unittest.TestCase):
    def test_bands(self):
        self.assertEqual([freq.tag(z) for z in (6, 4.5, 4.49, 3.5, 2)], ["core", "core", "common", "common", "rare"])


XML = """<?xml version="1.0" encoding="UTF-8"?>
<LexicalResource><Lexicon>
<LexicalEntry att="id" val="1"><feat att="homonym_number" val="0" /><feat att="lexicalUnit" val="단어" />
<feat att="partOfSpeech" val="명사" /><Lemma><feat att="writtenForm" val="학교" /></Lemma><feat att="origin" val="學校" />
<feat att="vocabularyLevel" val="초급" /><Sense att="id" val="1"><Equivalent><feat att="language" val="영어" />
<feat att="lemma" val="school" /><feat att="definition" val="A <b>place</b>." /></Equivalent></Sense></LexicalEntry>
</Lexicon></LexicalResource>
"""


class Import(unittest.TestCase):
    def test_parse_escapes_raw_angle_brackets(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.xml"
            p.write_text(XML, encoding="utf-8")
            [w] = list(krdict.entries_in(p))
        self.assertEqual((w["word"], w["level"], w["origin"], w["english"]), ("학교", "초급", "學校", ["school"]))

    def test_meaning(self):
        self.assertEqual(krdict.meaning(["edge; verge", "Edge", "rim", "side", "brink"]), "edge; verge; rim; side")

    def test_build(self):
        header = {"schema": "vocab@1", "language": "hangul", "notes": ["Written for this project."],
                  "decks": [{"id": "places", "title": "Places"}, {"id": "nikl-advanced", "title": "old"}]}
        entries = [{"id": "places/역", "deck": "places", "word": "역", "reading": "yeok", "meaning": "station"},
                   {"id": "nikl-advanced/옛", "deck": "nikl-advanced", "word": "옛", "reading": "yet", "meaning": "old"}]
        w = lambda word, level, eng, hn="0", unit="단어", pos="명사", origin="": {  # noqa: E731
            "word": word, "unit": unit, "pos": pos, "level": level, "origin": origin, "homonym": hn, "english": eng}
        words = [w("역", "중급", ["station"], origin="驛"), w("역", "초급", ["role"], "2"), w("학교", "초급", ["school"], origin="學校"),
                 w("장", "고급", ["chapter"], "3"), w("장", "고급", ["sauce"], "5"), w("-가", "중급", ["expert"], pos="접사"),
                 w("눈", "초급", []), w("먹고 살다", "중급", ["make a living"], unit="구"), w("모르다", "없음", ["not know"])]
        head, out, skipped = krdict.build(header, entries, words, lambda word: "common")
        self.assertEqual([d["id"] for d in head["decks"]], ["places", "nikl-beginner", "nikl-advanced"])
        self.assertEqual(head["source"], krdict.SOURCE)
        self.assertEqual(skipped, 1)
        by_id = {e["id"]: e for e in out}
        self.assertEqual(by_id["places/역"]["level"], {"nikl": "beginner"})
        self.assertEqual(by_id["nikl-beginner/학교"], {"id": "nikl-beginner/학교", "deck": "nikl-beginner", "word": "학교",
                         "reading": "hakgyo", "meaning": "school", "level": {"nikl": "beginner"}, "note": "Hanja: 學校",
                         "freq": "common"})
        self.assertIn("nikl-advanced/장", by_id)
        self.assertIn("nikl-advanced/장/5", by_id)
        self.assertEqual(len(out), 4)
        self.assertEqual(krdict.build(head, out, words, lambda word: "common")[1], out)


if __name__ == "__main__":
    unittest.main()
