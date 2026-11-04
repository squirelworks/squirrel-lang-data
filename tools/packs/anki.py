"""The anki format: a language's vocabulary as an Anki deck package.

    <out>/<id>.apkg

Open it in Anki (File > Import), AnkiDroid or AnkiMobile. Each vocabulary deck
becomes a subdeck, in teaching order:

    SquirrelGo::<Language>::NN <deck title>
    SquirrelGo::<Language>::<Variety>::NN <deck title>

Every word is one note with two cards: Recognize (the word; answer: reading,
meaning and note) and Recall (the meaning; answer: the word). Notes are
tagged with their deck, their levels (jlpt::N5, hsk::1) and their frequency
(freq::core). The top deck's description carries the license and credits.

A language with no vocabulary gets no package. Note ids, GUIDs and timestamps
are derived from the language and word ids, never from the clock, so the
same commit always gives the same bytes, and importing a newer package
updates the notes from an older one instead of adding them twice.

The package is the classic .apkg layout (a zip holding collection.anki2 and
an empty media map), which every current Anki client imports. The layout
follows the open source genanki library (MIT).
"""
import hashlib
import html
import json
import os
import sqlite3
import tempfile
import zipfile

REPO = "https://github.com/squirelworks/squirrel-lang-data"
STAMP = 1700000000  # a fixed modification time, so exports are reproducible
FIELDS = ["Word", "Reading", "Meaning", "Note", "Level", "Frequency"]
CSS = """.card { font-family: sans-serif; font-size: 22px; text-align: center; }
.word { font-size: 44px; }
.reading { color: #666; }
.note, .tags { font-size: 16px; color: #666; }"""
FRONT_RECOGNIZE = '<div class="word">{{Word}}</div>'
BACK_RECOGNIZE = ('{{FrontSide}}<hr id="answer">{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}'
                  '<div>{{Meaning}}</div>{{#Note}}<div class="note">{{Note}}</div>{{/Note}}'
                  '{{#Level}}<div class="tags">{{Level}}</div>{{/Level}}')
FRONT_RECALL = "<div>{{Meaning}}</div>"
BACK_RECALL = ('{{FrontSide}}<hr id="answer"><div class="word">{{Word}}</div>'
               '{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}'
               '{{#Note}}<div class="note">{{Note}}</div>{{/Note}}')

SCHEMA = """
CREATE TABLE col (id integer primary key, crt integer not null, mod integer not null, scm integer not null,
  ver integer not null, dty integer not null, usn integer not null, ls integer not null, conf text not null,
  models text not null, decks text not null, dconf text not null, tags text not null);
CREATE TABLE notes (id integer primary key, guid text not null, mid integer not null, mod integer not null,
  usn integer not null, tags text not null, flds text not null, sfld integer not null, csum integer not null,
  flags integer not null, data text not null);
CREATE TABLE cards (id integer primary key, nid integer not null, did integer not null, ord integer not null,
  mod integer not null, usn integer not null, type integer not null, queue integer not null, due integer not null,
  ivl integer not null, factor integer not null, reps integer not null, lapses integer not null,
  left integer not null, odue integer not null, odid integer not null, flags integer not null, data text not null);
CREATE TABLE revlog (id integer primary key, cid integer not null, usn integer not null, ease integer not null,
  ivl integer not null, lastIvl integer not null, factor integer not null, time integer not null,
  type integer not null);
CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""
DCONF = {"1": {
    "autoplay": True, "id": 1, "maxTaken": 60, "mod": 0, "name": "Default", "replayq": True, "timer": 0, "usn": 0,
    "lapse": {"delays": [10], "leechAction": 0, "leechFails": 8, "minInt": 1, "mult": 0},
    "new": {"bury": True, "delays": [1, 10], "initialFactor": 2500, "ints": [1, 4, 7], "order": 0, "perDay": 20,
            "separate": True},
    "rev": {"bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1, "maxIvl": 36500, "minSpace": 1, "perDay": 100},
}}
CONF = {"activeDecks": [1], "addToCur": True, "collapseTime": 1200, "curDeck": 1, "curModel": None,
        "dueCounts": True, "estTimes": True, "newBury": True, "newSpread": 0, "nextPos": 1,
        "sortBackwards": False, "sortType": "noteFld", "timeLim": 0}

BASE91 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&()*+,-./:;<=>?@[]^_`{|}~"


def _hash(*parts):
    return int.from_bytes(hashlib.sha256("\x1f".join(parts).encode("utf-8")).digest()[:8], "big")


def _id(*parts):
    """A stable id in the range Anki uses for decks and note types."""
    return (1 << 30) + _hash(*parts) % (1 << 30)


def _guid(*parts):
    n, out = _hash(*parts), ""
    while n:
        n, r = divmod(n, len(BASE91))
        out = BASE91[r] + out
    return out


def _deck(did, name, desc=""):
    return {"collapsed": False, "conf": 1, "desc": desc, "dyn": 0, "extendNew": 0, "extendRev": 50, "id": did,
            "lrnToday": [0, 0], "mod": STAMP, "name": name, "newToday": [0, 0], "revToday": [0, 0],
            "timeToday": [0, 0], "usn": -1}


def _model(mid, name, did):
    tmpl = lambda n, q, a: {"name": n, "ord": 0, "qfmt": q, "afmt": a, "bqfmt": "", "bafmt": "",  # noqa: E731
                            "bfont": "", "bsize": 0, "did": None}
    tmpls = [tmpl("Recognize", FRONT_RECOGNIZE, BACK_RECOGNIZE), tmpl("Recall", FRONT_RECALL, BACK_RECALL)]
    for n, t in enumerate(tmpls):
        t["ord"] = n
    return {"css": CSS, "did": did, "id": str(mid), "latexPost": "\\end{document}",
            "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage{amssymb,amsmath}\n"
                        "\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n",
            "latexsvg": False, "mod": STAMP, "name": name, "req": [[0, "all", [0]], [1, "all", [2]]], "sortf": 0,
            "tags": [], "tmpls": tmpls, "type": 0, "usn": -1, "vers": [],
            "flds": [{"name": f, "ord": i, "font": "Arial", "media": [], "rtl": False, "size": 20, "sticky": False}
                     for i, f in enumerate(FIELDS)]}


def _tag(text):
    return "".join(c if c.isalnum() or c in "-_:." else "_" for c in text)


def _vocab_nodes(node, path):
    """(deck path, language id, vocab data) for a node and its varieties."""
    out = []
    for c in node["content"]:
        if c["kind"] == "vocab" and c["rel"] == "vocab.jsonl":
            out.append((path, node["meta"]["id"], c["data"]))
    for v in node["varieties"]:
        out += _vocab_nodes(v, path + [v["meta"].get("name", v["meta"]["id"])])
    return out


def words(pack):
    """How many notes the package holds."""
    return sum(len(d[1]) for _, _, d in _vocab_nodes(pack, []))


def write(pack, out_dir):
    """Write out_dir/<id>.apkg, replacing an earlier export. Returns its path,
    or None when the language has no vocabulary."""
    name = pack["meta"].get("name", pack["id"])
    sets = _vocab_nodes(pack, [name])
    dest = out_dir / f"{pack['id']}.apkg"
    if not sets:
        if dest.exists():
            dest.unlink()
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    mid = _id("model", pack["id"])
    root_name = f"SquirrelGo::{name}"
    desc = (f"{name} vocabulary from squirrel-lang-data, commit {html.escape(pack['commit'])}. "
            f"Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). "
            f"Credits: {REPO}/blob/main/SOURCES.md")
    decks = {"1": _deck(1, "Default")}
    for n in ("SquirrelGo", root_name):
        did = _id("deck", n)
        decks[str(did)] = _deck(did, n, desc if n == root_name else "")
    notes, cards = [], []
    nid = 1_000_000_000_000
    for path, lang, (header, entries) in sets:
        prefix = "::".join(["SquirrelGo"] + path)
        if prefix != root_name:
            did = _id("deck", prefix)
            decks[str(did)] = _deck(did, prefix)
        for n, d in enumerate(header.get("decks", []), start=1):
            full = f"{prefix}::{n:02d} {d.get('title', d['id'])}"
            did = _id("deck", full)
            decks[str(did)] = _deck(did, full)
            for w in entries:
                if w.get("deck") != d["id"]:
                    continue
                nid += 1
                levels = " ".join(f"{k.upper()} {v}" for k, v in sorted((w.get("level") or {}).items()))
                flds = [html.escape(x) for x in (w["word"], w.get("reading", ""), w["meaning"], w.get("note", ""),
                                                  levels, w.get("freq", ""))]
                tags = [_tag(f"{lang}::{d['id']}")] + [_tag(f"{k}::{v}") for k, v in sorted((w.get("level") or {}).items())]
                if w.get("freq"):
                    tags.append(_tag(f"freq::{w['freq']}"))
                notes.append((nid, _guid(pack["id"], lang, w["id"]), mid, STAMP, -1, " " + " ".join(tags) + " ",
                              "\x1f".join(flds), flds[0], 0, 0, ""))
                for ord_ in (0, 1):
                    cards.append((nid * 10 + ord_, nid, did, ord_, STAMP, -1, 0, 0, nid - 1_000_000_000_000,
                                  0, 0, 0, 0, 0, 0, 0, 0, ""))
    conf = dict(CONF, curModel=str(mid))
    fd, tmpdb = tempfile.mkstemp(suffix=".anki2")
    os.close(fd)
    os.unlink(tmpdb)
    try:
        db = sqlite3.connect(tmpdb)
        db.executescript(SCHEMA)
        db.execute("INSERT INTO col VALUES (1,?,?,?,11,0,0,0,?,?,?,?,?)",
                   (STAMP, STAMP * 1000, STAMP * 1000, json.dumps(conf),
                    json.dumps({str(mid): _model(mid, f"SquirrelGo vocabulary ({name})", _id("deck", root_name))}),
                    json.dumps(decks, ensure_ascii=False), json.dumps(DCONF), "{}"))
        db.executemany("INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)", notes)
        db.executemany("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", cards)
        db.commit()
        db.close()
        tmp = dest.with_name(dest.name + ".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for arc, data in (("collection.anki2", open(tmpdb, "rb").read()), ("media", b"{}")):
                info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmpdb):
            os.unlink(tmpdb)
    return dest


def check(pack, dest, root):
    """Problems with a written package: it opens, holds one note per word with
    two cards each, and every card is in a deck the collection lists."""
    problems = []
    want = words(pack)
    if dest is None:
        return [f"no package written for {want} words"] if want else []
    with zipfile.ZipFile(dest) as z:
        names = sorted(z.namelist())
        if names != ["collection.anki2", "media"]:
            return [f"package holds {names}, not collection.anki2 and media"]
        data = z.read("collection.anki2")
    fd, tmpdb = tempfile.mkstemp(suffix=".anki2")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    try:
        db = sqlite3.connect(tmpdb)
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            problems.append("collection.anki2 fails SQLite's integrity check")
        models, decks = (json.loads(x) for x in db.execute("SELECT models, decks FROM col").fetchone())
        nfields = {int(k): len(m["flds"]) for k, m in models.items()}
        notes = db.execute("SELECT id, mid, flds FROM notes").fetchall()
        if len(notes) != want:
            problems.append(f"{len(notes)} notes for {want} words")
        for nid, mid, flds in notes:
            if len(flds.split("\x1f")) != nfields.get(mid):
                problems.append(f"note {nid} doesn't match its note type's fields")
        if db.execute("SELECT count(*) FROM cards").fetchone()[0] != 2 * len(notes):
            problems.append("every note should have two cards")
        missing = {d for (d,) in db.execute("SELECT DISTINCT did FROM cards")} - {int(k) for k in decks}
        if missing:
            problems.append(f"cards in decks the collection doesn't list: {sorted(missing)}")
        if len({g for (g,) in db.execute("SELECT guid FROM notes")}) != len(notes):
            problems.append("two notes share a GUID")
        db.close()
    finally:
        os.unlink(tmpdb)
    return problems
