"""Tests for strokes@1, tools/check_strokes.py and tools/gen_strokes.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_schema  # noqa: E402
import check_strokes  # noqa: E402
import gen_strokes  # noqa: E402
import lib  # noqa: E402

GREEK = [{"schema": "strokes@1", "set": "greek", "box": 100, "notes": ["Drawn over Noto Sans."],
          "source": "Noto fonts", "license": "SIL Open Font License 1.1"},
         {"char": "Γ", "strokes": ["M30,15 L30,85", "M30,15 L72,15"]},
         {"char": "ο", "strokes": ["M50,40 Q30,40 30,62 Q30,84 50,84 Q70,84 70,62 Q70,40 50,40 Z"]}]
KANJI = [{"schema": "strokes@1", "set": "kanji", "box": 109, "source": "KanjiVG", "license": "CC BY-SA 3.0"},
         {"char": "一", "strokes": ["M11,54.2c3.2,0.6,6.2,0.8,9.7,0.5c20.6-1.5,50.4-5.1,68.6-5.2"], "labels": [[4, 50]]},
         {"char": "二", "strokes": ["M24,30h60", "M12,76c20-2,60-4,86-3"], "labels": [[20, 26], [8, 72]]}]
TABLE = [{"schema": "cjk@1"}, {"char": "一", "radical": "一", "strokes": 1}, {"char": "二", "radical": "二", "strokes": 2}]


class Strokes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "schemas").mkdir()
        (self.root / "schemas" / "strokes.v1.json").write_text((lib.ROOT / "schemas" / "strokes.v1.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, rows):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return p

    def test_good_files(self):
        files = [self.write("strokes/greek.jsonl", GREEK), self.write("strokes/kanji.jsonl", KANJI)]
        self.write("cjk/characters.jsonl", TABLE)
        self.assertEqual([p for f in files for p in check_schema.check_file(f, self.root)], [])
        self.assertEqual(check_strokes.check(self.root), [])

    def test_schema_rejects(self):
        for rows in ([dict(GREEK[0], box=50), GREEK[1]], [GREEK[0], dict(GREEK[1], strokes=[])],
                     [KANJI[0], dict(KANJI[1], labels=[[4]])]):
            self.assertTrue(check_schema.check_file(self.write("strokes/x.jsonl", rows), self.root), rows)

    def test_paths(self):
        bad = {
            "M11,54c3.60,5.8": "c needs 6 numbers",   # the lost-minus-sign bug
            "L10,10": "doesn't start with M",
            "M10,10 A5,5 0 0 1 20,20": "unsupported command A",
            "M10,10 L150,10": "leaves the 100 x 100 box",
            "M10,10 L20,#": "L needs 2 numbers",
        }
        for d, want in bad.items():
            self.assertIn(want, check_strokes.path_problem(d, 100) or "", d)
        for d in ("M10,10 L20,20 Z", "m10,10l5,5h3v-2", "M1e1,10 Q20,30 40,10 T80,10", "M10 10 C20 20 30 30 40 40 S60 60 70 70"):
            self.assertIsNone(check_strokes.path_problem(d, 100), d)

    def test_rules(self):
        self.write("cjk/characters.jsonl", TABLE)
        cases = {
            "should be 'greek'": ("strokes/greek.jsonl", [dict(GREEK[0], set="latin"), *GREEK[1:]]),
            "listed twice": ("strokes/greek.jsonl", GREEK + [GREEK[1]]),
            "stroke 2 doesn't start": ("strokes/greek.jsonl", [GREEK[0], dict(GREEK[1], strokes=["M1,1", "L2,2"])]),
            "but 1 labels": ("strokes/kanji.jsonl", [KANJI[0], dict(KANJI[2], labels=[[1, 1]])]),
            "cjk/characters.jsonl says 2": ("strokes/kanji.jsonl", [KANJI[0], dict(KANJI[2], strokes=["M1,1"], labels=[[1, 1]])]),
        }
        for want, (rel, rows) in cases.items():
            for f in self.root.glob("strokes/*.jsonl"):
                f.unlink()
            self.write(rel, rows)
            got = check_strokes.check(self.root)
            self.assertTrue(any(want in p for p in got), f"{want}: {got}")

    def test_known_counts_must_still_differ(self):
        self.write("cjk/characters.jsonl", TABLE + [{"char": "巨", "radical": "工", "strokes": 5}])
        self.write("strokes/kanji.jsonl", KANJI + [{"char": "巨", "strokes": ["M1,1"] * 5, "labels": [[1, 1]] * 5}])
        self.assertTrue(any("no longer differs" in p for p in check_strokes.check(self.root)))

    @unittest.skipUnless(subprocess.run(["which", "node"], capture_output=True).returncode == 0, "needs node")
    def test_generate(self):
        self.write("strokes/greek.jsonl", GREEK)
        self.write("strokes/kanji.jsonl", KANJI)
        self.write("strokes/zhuyin.jsonl", [dict(GREEK[0], set="zhuyin"), {"char": "ㄅ", "strokes": ["M35,17 L27,37"]}])
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        apps = self.root / "apps"
        self.assertEqual(gen_strokes.main(["--data", str(self.root), "--apps", str(apps)]), 0)
        self.assertEqual(gen_strokes.main(["--data", str(self.root), "--apps", str(apps), "--check"]), 0)
        c = "squirrelgo-characters"
        greek = apps / c / "squirrelgo-alphabets/www/data/strokes/greek.js"
        kanji = apps / c / "squirrelgo-kanji/www/data/strokes.js"
        both = [apps / c / f"squirrelgo-bopomofo/{d}/data/strokes/zhuyin.js" for d in ("www", gen_strokes.ANDROID)]
        self.assertTrue(all(p.is_file() for p in both))
        self.assertIn("// Drawn over Noto Sans.", greek.read_text(encoding="utf-8"))
        js = ("global.window = global;" + "".join(f"eval(require('fs').readFileSync({json.dumps(str(f))}, 'utf8'));" for f in (greek, kanji, both[1]))
              + "process.stdout.write(JSON.stringify([SG_STROKES, KANJI_STROKES]))")
        sg, kj = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(sg["greek"]["Γ"], GREEK[1]["strokes"])
        self.assertEqual(sg["zhuyin"], {"ㄅ": ["M35,17 L27,37"]})
        self.assertEqual(kj["二"], [KANJI[2]["strokes"], KANJI[2]["labels"]])
        greek.write_text("stale\n", encoding="utf-8")
        self.assertEqual(gen_strokes.main(["--data", str(self.root), "--apps", str(apps), "--check"]), 1)


if __name__ == "__main__":
    unittest.main()
