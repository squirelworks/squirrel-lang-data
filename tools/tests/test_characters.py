"""Tests for characters@1, cjk@1, cjk-readings@1, tools/check_characters.py,
tools/gen_characters.py and tools/importers/cjk_unihan.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "importers"))
import check_characters  # noqa: E402
import check_schema  # noqa: E402
import cjk_unihan  # noqa: E402
import gen_characters  # noqa: E402
import lib  # noqa: E402

ARABIC = [{"schema": "characters@1", "language": "arabic", "script": "arabic", "name": "Arabic"},
          {"char": "ب", "roman": "b", "info": "Connects both sides", "example": "باب",
           "forms": {"isolated": "ب", "initial": "بـ", "medial": "ـبـ", "final": "ـب"}}]
HANGUL = [{"schema": "characters@1", "language": "hangul", "script": "hangul", "name": "Hangul"},
          {"char": "ㄱ", "roman": "g/k", "info": "basic consonant", "example": "가", "group": "Consonants"},
          {"char": "ㄴ", "roman": "n", "info": "basic consonant", "example": "나", "group": "Consonants"},
          {"char": "ㅏ", "roman": "a", "info": "basic vowel", "example": "아", "group": "Vowels"}]
KLINGON = [{"schema": "characters@1", "language": "klingon", "script": "klingon", "name": "Klingon (pIqaD)"},
           {"char": "", "roman": "a", "info": "vowel"}]
TABLE = [{"schema": "cjk@1"}, {"char": "日", "radical": "日", "strokes": 4}, {"char": "人", "radical": "人", "strokes": 2},
         {"char": "你", "radical": "人", "strokes": 7}, {"char": "学", "radical": "子", "strokes": 8}]
KANJI = [{"schema": "cjk-readings@1", "language": "japanese", "tradition": "kanji", "name": "Kanji"},
         {"char": "日", "roman": "ニチ", "info": "day", "level": "N5", "on": "ニチ / ジツ", "kun": "ひ", "grade": "1", "frequency": "1"},
         {"char": "人", "roman": "ニチ", "info": "person (not really ニチ)", "grade": "1"},
         {"char": "学", "roman": "ニチ", "info": "study"}]
HANZI = [{"schema": "cjk-readings@1", "language": "chinese", "tradition": "hanzi", "name": "Hanzi"},
         {"char": "你", "roman": "nǐ", "info": "you", "pinyin": "nǐ", "hsk": 1},
         {"char": "学", "roman": "xué", "info": "learn", "pinyin": "xué", "hsk": 1, "traditional": "學"}]


class Characters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        for s in ("characters", "cjk", "cjk-readings"):
            (self.root / "schemas" / f"{s}.v1.json").write_text((lib.ROOT / "schemas" / f"{s}.v1.json").read_text(encoding="utf-8"))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, rows):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return p

    def write_all(self, **over):
        files = {"languages/arabic/characters/arabic.jsonl": ARABIC, "languages/hangul/characters/hangul.jsonl": HANGUL,
                 "languages/klingon/characters/klingon.jsonl": KLINGON, "cjk/characters.jsonl": TABLE,
                 "languages/japanese/characters/kanji.jsonl": KANJI, "languages/chinese/characters/hanzi.jsonl": HANZI}
        files.update(over)
        return [self.write(rel, rows) for rel, rows in files.items() if rows is not None]

    def problems(self, paths):
        return [p for f in paths for p in check_schema.check_file(f, self.root)] + check_characters.check(self.root)

    def test_good_files(self):
        self.assertEqual(self.problems(self.write_all()), [])

    def test_schema_rejects(self):
        cases = [
            {"languages/arabic/characters/arabic.jsonl": [ARABIC[0], dict(ARABIC[1], forms={"isolated": "ب"})]},
            {"languages/arabic/characters/arabic.jsonl": [ARABIC[0], dict(ARABIC[1], roman="")]},
            {"languages/japanese/characters/kanji.jsonl": [KANJI[0], dict(KANJI[1], level="N6")]},
            {"languages/japanese/characters/kanji.jsonl": [KANJI[0], dict(KANJI[1], grade="7")]},
            {"languages/chinese/characters/hanzi.jsonl": [HANZI[0], dict(HANZI[1], hsk=7)]},
            {"cjk/characters.jsonl": [TABLE[0], dict(TABLE[1], strokes="4")]},
        ]
        for over in cases:
            self.assertTrue(self.problems(self.write_all(**over)), over)

    def test_rules(self):
        cases = {
            "should be 'arabic'": {"languages/arabic/characters/arabic.jsonl": [dict(ARABIC[0], language="persian"), ARABIC[1]]},
            "the file name": {"languages/arabic/characters/arabic.jsonl": [dict(ARABIC[0], script="naskh"), ARABIC[1]]},
            "is also": {"languages/persian/characters/arabic.jsonl": [dict(ARABIC[0], language="persian"), ARABIC[1]]},
            "listed twice": {"languages/arabic/characters/arabic.jsonl": ARABIC + [ARABIC[1]]},
            "is split": {"languages/hangul/characters/hangul.jsonl": [HANGUL[0], HANGUL[1], HANGUL[3], HANGUL[2]]},
            "belong in languages/chinese": {"languages/chinese/characters/hanzi.jsonl": None,
                                            "languages/taiwanese/characters/hanzi.jsonl": [dict(HANZI[0], language="taiwanese"), *HANZI[1:]]},
            "is not in cjk": {"cjk/characters.jsonl": TABLE[:3]},
            "no readings": {"cjk/characters.jsonl": TABLE + [{"char": "月", "radical": "月", "strokes": 4}]},
            "0 strokes": {"cjk/characters.jsonl": TABLE + [{"char": "月", "radical": "月", "strokes": 0}],
                          "languages/chinese/characters/hanzi.jsonl": HANZI + [{"char": "月", "roman": "yuè", "info": "moon"}]},
            "isn't a character table": {"languages/arabic/characters/arabic.jsonl": [dict(ARABIC[0], schema="vocab@1")]},
        }
        for want, over in cases.items():
            for f in [*self.root.glob("languages/*/characters/*.jsonl"), *self.root.glob("cjk/*.jsonl")]:
                f.unlink()
            self.write_all(**over)
            got = check_characters.check(self.root)
            self.assertTrue(any(want in p for p in got), f"{want}: {got}")

    def load_js(self, files, expr):
        script = "global.window = global;" + "".join(
            f"eval(require('fs').readFileSync({json.dumps(str(f))}, 'utf8'));" for f in files)
        out = subprocess.run(["node", "-e", script + f"process.stdout.write(JSON.stringify({expr}))"],
                             capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    @unittest.skipUnless(subprocess.run(["which", "node"], capture_output=True).returncode == 0, "needs node")
    def test_generate(self):
        self.write_all()
        out = self.root / "out"
        self.assertEqual(gen_characters.main(["--data", str(self.root), "--out", str(out),
                                              "--kanji-app", str(self.root / "app" / "kanji.js")]), 0)
        self.assertEqual(gen_characters.main(["--data", str(self.root), "--out", str(out), "--check"]), 0)
        text = (out / "klingon" / "characters.js").read_text(encoding="utf-8")
        self.assertIn('"\\uF8D0"', text)
        self.assertIn("    // Consonants\n", (out / "hangul" / "characters.js").read_text(encoding="utf-8"))
        files = [out / f for f in ("arabic/characters.js", "hangul/characters.js", "klingon/characters.js",
                                   "cjk/characters.js", "japanese/kanji.js", "chinese/hanzi.js")]
        got = self.load_js(files, "{s: SCRIPTS, t: LSD_CJK, r: LSD_CJK_READINGS}")
        self.assertEqual(got["s"]["hangul"]["chars"][0], {"char": "ㄱ", "roman": "g/k", "info": "basic consonant", "example": "가"})
        self.assertEqual(got["s"]["arabic"]["chars"][0]["forms"]["medial"], "ـبـ")
        self.assertEqual(got["s"]["klingon"]["chars"][0]["char"], "")
        self.assertEqual(got["t"]["学"], {"uses": ["hanzi", "kanji"], "radical": "子", "strokes": 8})
        self.assertEqual(got["t"]["你"]["uses"], ["hanzi"])
        self.assertEqual(got["r"]["hanzi"]["chars"]["学"], {"roman": "xué", "info": "learn", "pinyin": "xué", "hsk": 1, "traditional": "學"})
        self.assertEqual(got["r"]["kanji"]["groups"], [{"reading": "ニチ (ニチ)", "note": "3 total", "chars": [
            {"char": "日", "roman": "ニチ"}, {"char": "人", "roman": "ニチ"}, {"char": "学", "roman": "ニチ"}]}])
        app = self.load_js([self.root / "app" / "kanji.js"], "SCRIPTS.kanji")
        self.assertEqual(list(app["chars"][0]), ["char", "roman", "info", "level", "on", "kun", "radical", "strokes", "grade", "frequency"])
        self.assertEqual(app["chars"][1], {"char": "人", "roman": "ニチ", "info": "person (not really ニチ)", "radical": "人", "strokes": "2", "grade": "1"})
        self.assertEqual(app["groups"], got["r"]["kanji"]["groups"])
        (out / "cjk" / "characters.js").write_text("window.LSD_CJK = {};\n", encoding="utf-8")
        self.assertEqual(gen_characters.main(["--data", str(self.root), "--out", str(out), "--check"]), 1)

    def test_on_groups_order(self):
        chars = {c: {"roman": r} for c, r in [("a", "カ"), ("b", "キ"), ("c", "キ"), ("d", "カ"), ("e", "キ"),
                                              ("f", "カ"), ("g", "ク"), ("h", "ク"), ("i", ""), ("j", ""), ("k", "")]}
        self.assertEqual([g["reading"] for g in gen_characters.on_groups(chars)], ["カ (カ)", "キ (キ)"])


class Unihan(unittest.TestCase):
    UNIHAN = {
        "Unihan_Readings.txt": ["U+4F60\tkMandarin\tnǐ", "U+4F60\tkDefinition\tyou, second person pronoun",
                                "U+5B66\tkMandarin\txué", "U+5B66\tkDefinition\tlearning, knowledge; school",
                                "U+5B78\tkHangul\t학:0E", "U+5B78\tkDefinition\tlearning, knowledge; school; science",
                                "U+5B66\tkHangul\t학:0", "U+4EBA\tkHangul\t인:0E", "U+4EBA\tkDefinition\tman; people; mankind; someone else"],
        "Unihan_IRGSources.txt": ["U+4F60\tkRSUnicode\t9.5", "U+4F60\tkTotalStrokes\t7", "U+5B66\tkRSUnicode\t39.5",
                                  "U+5B66\tkTotalStrokes\t8", "U+5B78\tkRSUnicode\t39.13", "U+5B78\tkTotalStrokes\t16"],
        "Unihan_Variants.txt": ["U+5B66\tkTraditionalVariant\tU+5B78"],
    }

    def test_entries(self):
        with tempfile.TemporaryDirectory() as d:
            for name, lines in self.UNIHAN.items():
                (Path(d) / name).write_text("# comment\n" + "\n".join(lines) + "\n", encoding="utf-8")
            u = cjk_unihan.read_unihan(d)
        words = [{"simplified": "学", "level": ["new-2"], "frequency": 5}, {"simplified": "你们", "level": ["new-1"], "frequency": 9},
                 {"simplified": "好", "level": ["old-1"]}]
        level_of = cjk_unihan.hsk_chars(words)
        self.assertEqual(level_of, {"你": 1, "们": 1, "学": 2})
        hanzi = cjk_unihan.hanzi_entries(u, level_of)
        self.assertEqual(hanzi, [{"char": "你", "roman": "nǐ", "info": "you, second person pronoun", "pinyin": "nǐ", "hsk": 1},
                                 {"char": "学", "roman": "xué", "info": "learning, knowledge; school", "pinyin": "xué", "hsk": 2,
                                  "traditional": "學"}])
        hanja = cjk_unihan.hanja_entries(u)
        self.assertEqual([h["char"] for h in hanja], ["人", "學"])
        self.assertEqual(hanja[0], {"char": "人", "roman": "인", "info": "man; people; mankind; someone else", "hangul": "인"})
        rows = [{"char": "人", "radical": "人", "strokes": 2}, {"char": "月", "radical": "月", "strokes": 4}]
        table = cjk_unihan.table_rows(rows, dict.fromkeys(["人", "你", "学", "學"]), u)
        self.assertEqual(table, [rows[0], {"char": "你", "radical": "人", "strokes": 7},
                                 {"char": "学", "radical": "子", "strokes": 8}, {"char": "學", "radical": "子", "strokes": 16}])


if __name__ == "__main__":
    unittest.main()
