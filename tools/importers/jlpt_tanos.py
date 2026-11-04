#!/usr/bin/env python3
"""Import the JLPT vocabulary lists (N5 to N1) into languages/japanese/vocab.jsonl.

    pip install "wordfreq[mecab]"        # only this importer needs it
    python3 tools/importers/jlpt_tanos.py

The lists are Jonathan Waller's (tanos.co.uk, CC BY), as cleaned up in
stephenmk/yomitan-jlpt-vocab (CC BY-SA 4.0), which swaps rare spellings for
the common ones in JMdict. The CSVs are fetched at a pinned commit into
cache/ and never committed.

What it does, so a rerun gives the same file:
- Keeps the decks written for this project and drops any earlier jlpt-* decks.
- A JLPT word that is already in a written deck is tagged with its level there
  instead of being added again. A word on two lists keeps the easier level.
  A list row in kana also tags a written entry spelled with kanji (おいしい
  tags 美味しい), and written entries are tagged again on every run.
- A few set greetings (N5_EXPRESSIONS) are placed at N5 when spelled in kana,
  and the greetings that end in the particle は are read with "wa".
- Every other word goes into the deck for its level (jlpt-n5 ... jlpt-n1), with
  Hepburn romaji as its reading and its kana in the note when it has kanji.
- Words with no English definition in the source are left out.
- Every word without a frequency tag gets one from wordfreq's Zipf frequency:
  core at 4.5 and above, common from 3.5, rare below.
"""
import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fmt  # noqa: E402
import lib  # noqa: E402
from freq import zipf_tagger  # noqa: E402
from kana import romaji  # noqa: E402

COMMIT = "b062d4e38c4bdd0950ae1d4ec55f04b176182e03"
URL = f"https://raw.githubusercontent.com/stephenmk/yomitan-jlpt-vocab/{COMMIT}/original_data/n{{n}}.csv"
LEVELS = [5, 4, 3, 2, 1]
SOURCE = "JLPT lists by Jonathan Waller (tanos.co.uk), via yomitan-jlpt-vocab"
LICENSE = "CC BY (Waller's lists); CC BY-SA 4.0 (yomitan-jlpt-vocab)"
NOTES = [
    "The decks JLPT N5 to JLPT N1 are imported by tools/importers/jlpt_tanos.py from "
    "Jonathan Waller's JLPT lists (tanos.co.uk, CC BY), as cleaned up in yomitan-jlpt-vocab "
    "(CC BY-SA 4.0). There is no official JLPT word list, so the levels are a well-known estimate.",
    "Frequency tags come from wordfreq (CC BY-SA 4.0).",
]
# Set greetings that Waller's lists place at N3 to N1, though every course
# teaches them first. The JLPT describes N5 as "the ability to understand some
# basic Japanese", reading "typical expressions and sentences written in
# hiragana, katakana, and basic kanji" (jlpt.jp), so they probably fall under N5.
N5_EXPRESSIONS = {"こんにちは", "こんばんは", "さようなら", "ありがとう", "おはよう",
                  "すみません", "ごめんなさい", "はじめまして", "いただきます"}
# Greetings that end in the particle は, which is read "wa" (今日は is konnichiwa).
READINGS = {"こんにちは": "konnichiwa", "こんばんは": "konbanwa"}
# Waller's list has an editor's placeholder for いえ instead of a definition.
MEANINGS = {"いえ": "no (a lighter いいえ)"}
KANA = re.compile(r"^[぀-ヿー]+$")


def fetch(n, cache):
    path = cache / f"n{n}.csv"
    if not path.is_file():
        cache.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL.format(n=n)) as r:
            path.write_bytes(r.read())
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def meaning(definition):
    """Waller separates alternatives with a comma, mostly a bare one; the data
    uses '; '. A definition with bare commas keeps its ', ' (as in "Sorry, but");
    one without uses ', ' as the separator. Digit groups (10,000) stay. A stray
    separator at either end is dropped first."""
    d = definition.strip().strip(",;").strip()
    bare = r",(?!\s)(?!(?<=\d,)\d)"
    d = re.sub(bare, "; ", d) if re.search(bare, d) else re.sub(r",\s+", "; ", d)
    return re.sub(r"\s+", " ", d)


def words(text):
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def matches(entry, word, kana, definition=""):
    """An entry written for this project that is this JLPT word. A list row with
    no kanji also matches an entry written with kanji that has the same reading
    and shares an English word with it, so おいしい ("delicious") on the N5 list
    tags 美味しい but さん ("Mr or Mrs") does not tag 三."""
    note = entry.get("note", "")
    same_kana = entry["word"] == kana or note.startswith(kana) or entry.get("reading") == romaji(kana)
    if entry["word"] != word:
        return (word == kana and entry["word"] != kana and same_kana
                and bool(words(entry["meaning"]) & words(definition)))
    return word == kana or same_kana


def build(header, entries, lists, freq):
    own = [e for e in entries if not e["deck"].startswith("jlpt-")]
    decks = [d for d in header["decks"] if not d["id"].startswith("jlpt-")]
    for e in own:  # tag again from scratch, so a fixed rule also fixes old tags
        if "jlpt" in e.get("level", {}):
            del e["level"]["jlpt"]
            if not e["level"]:
                del e["level"]
    added, seen, ids, skipped = {n: [] for n in LEVELS}, set(), set(), 0
    for n in LEVELS:
        for row in lists[n]:
            kana, word, definition = row["kana"].strip(), (row["kanji"] or row["kana"]).strip(), row["waller_definition"]
            level = "N5" if word in N5_EXPRESSIONS else f"N{n}"
            if (word, kana) in seen:
                continue
            seen.add((word, kana))
            if not definition.strip():
                skipped += 1
                continue
            mine = [e for e in own if matches(e, word, kana, definition)]
            if mine:
                for e in mine:
                    e.setdefault("level", {}).setdefault("jlpt", level)
                continue
            deck = f"jlpt-{level.lower()}"
            id_ = f"{deck}/{word}" if f"{deck}/{word}" not in ids else f"{deck}/{word}/{kana}"
            ids.add(id_)
            verb = word != kana and word.endswith("う") and definition.startswith("to ")
            e = {"id": id_, "deck": deck, "word": word, "reading": READINGS.get(kana) or romaji(kana, verb=verb),
                 "meaning": MEANINGS.get(word) or meaning(definition), "level": {"jlpt": level}}
            if word != kana or not KANA.match(word):
                e["note"] = kana
            added[int(level[1])].append(e)
    out = own + [e for n in LEVELS for e in added[n]]
    for e in out:
        if "freq" not in e:
            e["freq"] = freq(e["word"])
    head = dict(header)
    head["notes"] = [x for x in header.get("notes", []) if x not in NOTES and "jlpt_tanos" not in x] + NOTES
    head["source"], head["license"] = SOURCE, LICENSE
    head["decks"] = decks + [{"id": f"jlpt-n{n}", "title": f"JLPT N{n}"} for n in LEVELS if added[n]]
    return head, out, skipped


def main():
    path = lib.ROOT / "languages" / "japanese" / "vocab.jsonl"
    header, entries = lib.read(path)
    cache = lib.ROOT / "cache" / "jlpt" / COMMIT[:12]
    lists = {n: fetch(n, cache) for n in LEVELS}
    head, out, skipped = build(header, entries, lists, zipf_tagger("ja"))
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in [head, *out]), encoding="utf-8")
    path.write_text(fmt.format_file(path), encoding="utf-8")
    new = sum(e["deck"].startswith("jlpt-") for e in out)
    tagged = sum(not e["deck"].startswith("jlpt-") and "jlpt" in e.get("level", {}) for e in out)
    print(f"{path.relative_to(lib.ROOT)}: {new} JLPT words added, {tagged} written words tagged, "
          f"{skipped} left out with no definition")


if __name__ == "__main__":
    main()
