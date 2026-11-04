"""The yomitan format: a language's vocabulary as a Yomitan dictionary.

    <out>/<id>-yomitan.zip

Import it in Yomitan (Settings > Dictionaries > Import), the browser
pop-up dictionary, to look words up by hovering over them on any web page.
The zip holds index.json, term_bank_N.json (up to 10,000 words each) and
tag_bank_1.json, in Yomitan's dictionary format 3.

Each word is one term:

- reading: the word's reading. Japanese readings here are romaji, which
  Yomitan can't match, so for Japanese the reading is the word itself when
  it's written in kana, or the kana in its note when the note is only kana
  (as the JLPT imports give it), and the romaji goes in the definition.
- definitions: the meaning split at semicolons, then the note.
- tags: the deck, each level (jlpt-N5, hsk-1), the frequency, and the
  variety for a variety's words. Frequency also sets the score, so core
  words come first.

There are no inflection rules yet, so Yomitan finds dictionary forms only.
A language with no vocabulary gets no dictionary. The revision is the data
commit, and nothing depends on the clock, so the same commit gives the same
bytes.
"""
import json
import os
import zipfile

from .anki import REPO, _vocab_nodes

BANK_SIZE = 10000
SCORE = {"core": 2, "common": 1, "rare": -1}
KANA = set(range(0x3040, 0x3100)) | {0x3005}  # hiragana, katakana, ー and 々


def _kana(text):
    return bool(text) and all(ord(c) in KANA for c in text)


def _code(meta):
    """ISO 639-1 where the speech tag gives it, ISO 639-3 otherwise."""
    tag = meta.get("speech", "").split("-")[0].lower()
    return tag if 2 <= len(tag) <= 3 and tag.isalpha() else meta.get("code", "")


def _tag(text):
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in text)


def terms(pack):
    """(terms, tags) for the dictionary: every word in teaching order."""
    rows, tags = [], {}
    japanese = pack["id"] == "japanese"
    seq = 0
    for path, lang, (header, entries) in _vocab_nodes(pack, []):
        titles = {d["id"]: d.get("title", d["id"]) for d in header.get("decks", [])}
        for w in entries:
            seq += 1
            reading = w.get("reading", "")
            glossary = [m.strip() for m in w["meaning"].split(";") if m.strip()]
            note = w.get("note", "")
            if japanese:
                if reading:
                    glossary.append(f"romaji: {reading}")
                reading = w["word"] if _kana(w["word"]) else note if _kana(note) else ""
                if note and note == reading:
                    note = ""
            if reading == w["word"]:
                reading = ""
            if note:
                glossary.append(note)
            term_tags = []
            deck = _tag(w["deck"])
            tags[deck] = [deck, "", 0, titles.get(w["deck"], w["deck"]), 0]
            for system, level in sorted((w.get("level") or {}).items()):
                t = _tag(f"{system}-{level}")
                tags[t] = [t, "frequent", 1, f"{system.upper()} {level}", 0]
                term_tags.append(t)
            if w.get("freq"):
                tags[w["freq"]] = [w["freq"], "frequent" if w["freq"] != "rare" else "", 2,
                                   f"{w['freq'].capitalize()} word", 0]
                term_tags.append(w["freq"])
            if path:
                v = _tag(lang)
                tags[v] = [v, "dictionary", 3, " / ".join(path), 0]
                term_tags.append(v)
            rows.append([w["word"], reading, deck, "", SCORE.get(w.get("freq"), 0), glossary or [w["meaning"]],
                         seq, " ".join(term_tags)])
    return rows, [tags[k] for k in sorted(tags)]


def write(pack, out_dir):
    """Write out_dir/<id>-yomitan.zip, replacing an earlier export. Returns its
    path, or None when the language has no vocabulary."""
    dest = out_dir / f"{pack['id']}-yomitan.zip"
    rows, tags = terms(pack)
    if not rows:
        if dest.exists():
            dest.unlink()
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = pack["meta"]
    name = meta.get("name", pack["id"])
    index = {
        "title": f"SquirrelGo {name}",
        "revision": pack["commit"],
        "format": 3,
        "sequenced": False,
        "author": "squirrel-lang-data contributors",
        "url": REPO,
        "description": f"{name} vocabulary from squirrel-lang-data, commit {pack['commit']}, "
                       "in teaching order with level and frequency tags.",
        "attribution": f"CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). "
                       f"Sources and credits: {REPO}/blob/main/SOURCES.md",
        "targetLanguage": "en",
    }
    if _code(meta):
        index["sourceLanguage"] = _code(meta)
    files = {"index.json": index, "tag_bank_1.json": tags}
    for n in range(0, len(rows), BANK_SIZE):
        files[f"term_bank_{n // BANK_SIZE + 1}.json"] = rows[n:n + BANK_SIZE]
    tmp = dest.with_name(dest.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for arc in sorted(files):
            info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, json.dumps(files[arc], ensure_ascii=False))
    os.replace(tmp, dest)
    return dest


def check(pack, dest, root):
    """Problems with a written dictionary: one well-formed term per word, and
    every tag a term uses is in the tag bank."""
    rows, _ = terms(pack)
    if dest is None:
        return [f"no dictionary written for {len(rows)} words"] if rows else []
    problems = []
    with zipfile.ZipFile(dest) as z:
        index = json.loads(z.read("index.json"))
        tags = {t[0] for t in json.loads(z.read("tag_bank_1.json"))}
        banks = sorted((n for n in z.namelist() if n.startswith("term_bank_")),
                       key=lambda n: int(n[len("term_bank_"):-len(".json")]))
        terms_ = [t for b in banks for t in json.loads(z.read(b))]
    if index.get("format") != 3 or not index.get("title") or not index.get("revision"):
        problems.append("index.json needs format 3, a title and a revision")
    if len(terms_) != len(rows):
        problems.append(f"{len(terms_)} terms for {len(rows)} words")
    for t in terms_:
        if len(t) != 8 or not t[0] or not isinstance(t[5], list) or not t[5]:
            problems.append(f"malformed term {t[:2]}")
            break
        unknown = {x for x in (t[2] + " " + t[7]).split() if x not in tags}
        if unknown:
            problems.append(f"term {t[0]} uses tags missing from the tag bank: {sorted(unknown)}")
            break
    return problems
