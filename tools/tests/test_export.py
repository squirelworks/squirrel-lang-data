"""Tests for tools/export.py, tools/check_export.py and the pack formats."""
import contextlib
import io
import json
import sqlite3
import sys
import tempfile
import zipfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import check_export  # noqa: E402
import export  # noqa: E402
import packs  # noqa: E402

META = {"schema": "meta@1", "id": "greek", "name": "Greek", "nativeName": "Ελληνικά", "code": "ell",
        "scripts": ["greek"], "characterKeys": ["greek"], "varieties": ["koine"]}
VARIETY = {"schema": "variety@1", "id": "koine", "parent": "greek", "kind": "historical",
           "name": "Koine Greek", "code": "grc", "period": {"label": "300 BCE to 300 CE"}}
VOCAB = [
    {"schema": "vocab@1", "language": "greek", "decks": [{"id": "greetings", "title": "Greetings"}, {"id": "food", "title": "Food"}]},
    {"id": "greetings/γεια", "deck": "greetings", "word": "γεια", "reading": "giá", "meaning": "hi"},
    {"id": "food/ψωμί", "deck": "food", "word": "ψωμί", "reading": "psomí", "meaning": "bread",
     "note": "Has\ta tab.", "level": {"cefr": "A1"}, "freq": "core"},
]
GRAMMAR = {"schema": "grammar@1", "language": "greek", "title": "Greek", "intro": "Intro.",
           "lessons": [{"id": "articles", "title": "Articles", "sections": [{"p": "ο, η, το"}]},
                       {"id": "verbs", "title": "Verbs", "sections": [{"p": "είμαι"}]}]}
CARDS = {"schema": "reference@1", "language": "greek", "entries": [{"id": "alphabet"}]}


def jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.out = Path(self.tmp.name) / "out"
        lang = self.root / "languages" / "greek"
        files = {
            "meta.json": json.dumps(META, ensure_ascii=False, indent=2) + "\n",
            "vocab.jsonl": jsonl(VOCAB),
            "grammar.json": json.dumps(GRAMMAR, ensure_ascii=False, indent=2) + "\n",
            "reference.json": json.dumps(CARDS) + "\n",  # a type the export has no special view for
            "strokes/greek.jsonl": jsonl([{"schema": "strokes@1"}]),  # a subfolder keeps its path
            "varieties/koine/meta.json": json.dumps(VARIETY, ensure_ascii=False) + "\n",
            "varieties/koine/vocab.jsonl": jsonl([dict(VOCAB[0], language="koine"), VOCAB[1]]),
        }
        for rel, text in files.items():
            (lang / rel).parent.mkdir(parents=True, exist_ok=True)
            (lang / rel).write_text(text, encoding="utf-8")
        (self.root / "LICENSE").write_text("CC BY-SA 4.0\n")
        (self.root / "SOURCES.md").write_text("# Sources\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        return packs.FORMATS["folder"].write(packs.load("greek", self.root), self.out)

    def test_folder_layout(self):
        dest = self.write()
        manifest = json.loads((dest / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["format"], "squirrel-pack@1")
        self.assertEqual(manifest["language"], "greek")
        for rel in ["meta.json", "vocab/vocab.jsonl", "vocab/decks/01-greetings.tsv", "vocab/decks/02-food.tsv",
                    "grammar/grammar.json", "grammar/lessons/01-articles.json", "grammar/lessons/02-verbs.json",
                    "reference/reference.json", "strokes/greek.jsonl", "varieties/koine/meta.json",
                    "varieties/koine/vocab/vocab.jsonl", "varieties/koine/vocab/decks/01-greetings.tsv",
                    "LICENSE.txt", "SOURCES.md", "README.md"]:
            self.assertIn(rel, manifest["files"], rel)
        counts = {c["kind"]: c["count"] for c in manifest["contents"]}
        self.assertEqual(counts, {"grammar": 2, "reference": 1, "strokes": 0, "vocab": 2})
        self.assertEqual(manifest["varieties"]["koine"]["kind"], "historical")
        food = (dest / "vocab/decks/02-food.tsv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(food[0], "word\treading\tmeaning\tnote\tlevel\tfreq")
        self.assertEqual(food[1], 'ψωμί\tpsomí\tbread\t"Has\ta tab."\tcefr:A1\tcore')
        self.assertEqual((dest / "meta.json").read_bytes(), (self.root / "languages/greek/meta.json").read_bytes())

    def test_check_passes_and_is_deterministic(self):
        problems, n = check_export.check(self.root)
        self.assertEqual((problems, n), ([], 1))

    def test_check_catches_damage(self):
        dest = self.write()
        fmt = packs.FORMATS["folder"]
        pack = packs.load("greek", self.root)
        (dest / "vocab/decks/02-food.tsv").write_text("word\tmeaning\n", encoding="utf-8")
        (dest / "reference/reference.json").unlink()
        problems = "\n".join(fmt.check(pack, dest, self.root))
        self.assertIn("reference.json is missing", problems)
        self.assertIn("deck files hold 1 words", problems)
        self.assertIn("pack.json files don't match", problems)

    def test_replaces_only_packs(self):
        self.write()
        (self.out / "greek" / "stale.txt").write_text("old")
        self.write()
        self.assertFalse((self.out / "greek" / "stale.txt").exists())
        (self.out / "greek" / "pack.json").unlink()
        with self.assertRaises(FileExistsError):
            self.write()

    def test_sqlite(self):
        dest = packs.FORMATS["sqlite"].write(packs.load("greek", self.root), self.out)
        db = sqlite3.connect(dest)
        self.assertEqual(db.execute("SELECT id, kind FROM languages ORDER BY id").fetchall(),
                         [("greek", "language"), ("koine", "historical")])
        self.assertEqual(db.execute("SELECT language, word, position FROM words ORDER BY language, position").fetchall(),
                         [("greek", "γεια", 1), ("greek", "ψωμί", 2), ("koine", "γεια", 1)])
        self.assertEqual(db.execute("SELECT word_id FROM word_levels WHERE system='cefr' AND level='A1'").fetchall(),
                         [("food/ψωμί",)])
        self.assertEqual(db.execute("SELECT id FROM lessons ORDER BY position").fetchall(), [("articles",), ("verbs",)])
        self.assertEqual(json.loads(db.execute("SELECT content FROM files WHERE path='reference.json'").fetchone()[0]), CARDS)
        self.assertEqual(dict(db.execute("SELECT key, value FROM pack"))["format"], "squirrel-pack@1")
        db.close()
        self.assertEqual(packs.FORMATS["sqlite"].check(packs.load("greek", self.root), dest, self.root), [])

    def test_sqlite_check_catches_damage(self):
        fmt = packs.FORMATS["sqlite"]
        pack = packs.load("greek", self.root)
        dest = fmt.write(pack, self.out)
        db = sqlite3.connect(dest)
        db.execute("DELETE FROM words WHERE id='food/ψωμί'")
        db.execute("DELETE FROM files WHERE path='strokes/greek.jsonl'")
        db.commit()
        db.close()
        problems = "\n".join(fmt.check(pack, dest, self.root))
        self.assertIn("1 rows in words for 2 words", problems)
        self.assertIn("strokes/greek.jsonl is missing", problems)

    def test_anki(self):
        fmt = packs.FORMATS["anki"]
        pack = packs.load("greek", self.root)
        dest = fmt.write(pack, self.out)
        self.assertEqual(fmt.check(pack, dest, self.root), [])
        with zipfile.ZipFile(dest) as z:
            (self.out / "c.anki2").write_bytes(z.read("collection.anki2"))
        db = sqlite3.connect(self.out / "c.anki2")
        decks = json.loads(db.execute("SELECT decks FROM col").fetchone()[0])
        names = sorted(d["name"] for d in decks.values())
        self.assertIn("SquirrelGo::Greek::02 Food", names)
        self.assertIn("SquirrelGo::Greek::Koine Greek::01 Greetings", names)
        notes = db.execute("SELECT flds, tags, guid FROM notes ORDER BY id").fetchall()
        self.assertEqual(len(notes), 3)
        self.assertEqual(notes[1][0].split("\x1f"), ["ψωμί", "psomí", "bread", "Has\ta tab.", "CEFR A1", "core"])
        self.assertEqual(notes[1][1], " greek::food cefr::A1 freq::core ")
        self.assertNotEqual(notes[0][2], notes[2][2])  # the variety's word is its own note
        self.assertEqual(db.execute("SELECT count(*) FROM cards").fetchone()[0], 6)
        db.close()
        self.assertEqual(fmt.write(pack, self.out).read_bytes(), dest.read_bytes())

    def test_anki_skips_languages_without_vocab(self):
        (self.root / "languages/greek/vocab.jsonl").unlink()
        (self.root / "languages/greek/varieties/koine/vocab.jsonl").unlink()
        pack = packs.load("greek", self.root)
        self.assertIsNone(packs.FORMATS["anki"].write(pack, self.out))
        self.assertEqual(packs.FORMATS["anki"].check(pack, None, self.root), [])

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(export.main(["--list"]), 0)
            self.assertEqual(export.main(["no-such-language"]), 2)
        self.assertIn("anki, folder, sqlite", out.getvalue())


if __name__ == "__main__":
    unittest.main()
