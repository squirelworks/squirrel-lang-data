"""The sqlite format: a language's content as one SQLite database.

    <out>/<id>.sqlite

Tables (every language and variety in the pack is in the same tables, told
apart by `language`):

    pack        key, value: format, language, dataCommit, license, the
                license text and SOURCES.md
    languages   id, parent, kind, name, nativeName, code, meta (JSON):
                the language first, then its varieties
    decks       language, id, position, title
    words       language, id, deck, position, word, reading, meaning, note,
                freq, level (JSON), varieties (JSON)
    word_levels language, word_id, system, level: one row per level tag, for
                queries like "every JLPT N5 word"
    courses     language, title, intro, notes, plan, drillData (JSON where
                not text)
    lessons     language, id, position, title, particle, summary, level,
                lesson (the whole lesson as JSON)
    files       path, kind, schema, content: every file of the language
                folder exactly as in the repo, so content types without
                their own table are still there

JSON columns hold the value as in the repo. Rows are inserted in a fixed
order with no timestamps, so exporting the same commit twice gives the same
bytes.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib  # noqa: E402

from . import PACK_FORMAT  # noqa: E402

SCHEMA = """
CREATE TABLE pack (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE languages (id TEXT PRIMARY KEY, parent TEXT, kind TEXT, name TEXT, nativeName TEXT,
                        code TEXT, meta TEXT NOT NULL);
CREATE TABLE decks (language TEXT NOT NULL, id TEXT NOT NULL, position INTEGER NOT NULL, title TEXT,
                    PRIMARY KEY (language, id));
CREATE TABLE words (language TEXT NOT NULL, id TEXT NOT NULL, deck TEXT NOT NULL, position INTEGER NOT NULL,
                    word TEXT NOT NULL, reading TEXT, meaning TEXT NOT NULL, note TEXT, freq TEXT,
                    level TEXT, varieties TEXT, PRIMARY KEY (language, id));
CREATE TABLE word_levels (language TEXT NOT NULL, word_id TEXT NOT NULL, system TEXT NOT NULL,
                          level TEXT NOT NULL, PRIMARY KEY (language, word_id, system));
CREATE TABLE courses (language TEXT PRIMARY KEY, title TEXT, intro TEXT, notes TEXT, plan TEXT,
                      drillData TEXT);
CREATE TABLE lessons (language TEXT NOT NULL, id TEXT NOT NULL, position INTEGER NOT NULL, title TEXT,
                      particle TEXT, summary TEXT, level TEXT, lesson TEXT NOT NULL,
                      PRIMARY KEY (language, id));
CREATE TABLE files (path TEXT PRIMARY KEY, kind TEXT, schema TEXT, content BLOB NOT NULL);
CREATE INDEX words_deck ON words (language, deck, position);
CREATE INDEX word_levels_level ON word_levels (system, level);
"""


def _j(value):
    return None if value is None else json.dumps(value, ensure_ascii=False)


def _insert(db, node, prefix):
    meta = node["meta"]
    lang = meta["id"]
    db.execute("INSERT INTO languages VALUES (?,?,?,?,?,?,?)",
               (lang, meta.get("parent"), meta.get("kind", "language"), meta.get("name"),
                meta.get("nativeName"), meta.get("code"), _j(meta)))
    db.execute("INSERT INTO files VALUES (?,?,?,?)", (prefix + "meta.json", "meta" if prefix == "" else "variety",
                                                       meta.get("schema"), node["metaText"].encode("utf-8")))
    for c in node["content"]:
        db.execute("INSERT INTO files VALUES (?,?,?,?)",
                   (prefix + c["rel"], c["kind"], c["schema"], c["text"].encode("utf-8")))
        if c["kind"] == "vocab":
            header, words = c["data"]
            for n, d in enumerate(header.get("decks", []), start=1):
                db.execute("INSERT INTO decks VALUES (?,?,?,?)", (lang, d["id"], n, d.get("title")))
            for n, w in enumerate(words, start=1):
                db.execute("INSERT INTO words VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           (lang, w["id"], w["deck"], n, w["word"], w.get("reading"), w["meaning"],
                            w.get("note"), w.get("freq"), _j(w.get("level")), _j(w.get("varieties"))))
                for system, level in sorted((w.get("level") or {}).items()):
                    db.execute("INSERT INTO word_levels VALUES (?,?,?,?)", (lang, w["id"], system, level))
        elif c["kind"] == "grammar":
            g = c["data"]
            db.execute("INSERT INTO courses VALUES (?,?,?,?,?,?)",
                       (lang, g.get("title"), g.get("intro"), _j(g.get("notes")), _j(g.get("plan")),
                        _j(g.get("drillData"))))
            for n, l in enumerate(g.get("lessons", []), start=1):
                db.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?)",
                           (lang, l["id"], n, l.get("title"), l.get("particle"), l.get("summary"),
                            l.get("level"), _j(l)))
    for o in node["other"]:
        db.execute("INSERT INTO files VALUES (?,?,?,?)", (prefix + o["rel"], None, None, o["bytes"]))
    for v in node["varieties"]:
        _insert(db, v, f"{prefix}varieties/{v['meta']['id']}/")


def write(pack, out_dir):
    """Write out_dir/<id>.sqlite, replacing an earlier export. Returns its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{pack['id']}.sqlite"
    tmp = dest.with_name(dest.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    db = sqlite3.connect(tmp)
    try:
        db.executescript(SCHEMA)
        rows = [("format", PACK_FORMAT), ("language", pack["id"]), ("dataCommit", pack["commit"]),
                ("license", "CC-BY-SA-4.0"), ("licenseText", pack["license"]), ("sources", pack["sources"])]
        db.executemany("INSERT INTO pack VALUES (?,?)", rows)
        _insert(db, pack, "")
        db.commit()
    finally:
        db.close()
    os.replace(tmp, dest)
    return dest


def check(pack, dest, root):
    """Problems with a written database, found by reading the repo again."""
    problems = []
    db = sqlite3.connect(f"file:{dest}?mode=ro", uri=True)
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            problems.append("the database fails SQLite's integrity check")
        stored = dict(db.execute("SELECT path, content FROM files"))
        src = root / "languages" / pack["id"]
        on_disk = {p.relative_to(src).as_posix(): p for p in sorted(src.rglob("*")) if p.is_file()}
        for rel, p in on_disk.items():
            if rel not in stored:
                problems.append(f"{p.relative_to(root)} is missing from the files table")
            elif bytes(stored[rel]) != p.read_bytes():
                problems.append(f"{p.relative_to(root)} differs in the files table")
        for rel in sorted(set(stored) - set(on_disk)):
            problems.append(f"files table has {rel}, which isn't in the repo")
        for rel, p in on_disk.items():
            lang = rel.split("/")[1] if rel.startswith("varieties/") else pack["id"]
            if p.name == "vocab.jsonl":
                want = len(lib.read(p)[1])
                got = db.execute("SELECT count(*) FROM words WHERE language=?", (lang,)).fetchone()[0]
                if got != want:
                    problems.append(f"{p.relative_to(root)}: {got} rows in words for {want} words")
            elif p.name == "grammar.json":
                want = len(lib.read(p).get("lessons", []))
                got = db.execute("SELECT count(*) FROM lessons WHERE language=?", (lang,)).fetchone()[0]
                if got != want:
                    problems.append(f"{p.relative_to(root)}: {got} rows in lessons for {want} lessons")
    finally:
        db.close()
    return problems
