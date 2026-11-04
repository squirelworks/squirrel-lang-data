#!/usr/bin/env python3
"""Import the graded words of the NIKL Basic Korean Dictionary into
languages/hangul/vocab.jsonl.

    pip install "wordfreq[mecab]"        # only for the frequency tags
    python3 tools/importers/krdict.py

The Basic Korean Dictionary (한국어기초사전, krdict.korean.go.kr) is the
National Institute of Korean Language's learner's dictionary, under CC BY-SA
2.0 KR, which allows sharing adaptations under CC BY-SA 4.0. It grades about
6,800 words beginner (초급), intermediate (중급) or advanced (고급); those are the
words imported. The XML export is read from the spellcheck-ko mirror at a
pinned commit (August 2019), fetched into cache/ and never committed.

What it does, so a rerun gives the same file:
- Keeps the decks written for this project and drops any earlier nikl-* decks.
- A graded word already in a written deck gets its level there instead of
  being added again (the easiest level when homographs differ).
- Every other graded word goes into the deck for its level, with Revised
  Romanization as its reading, the dictionary's English equivalents of its
  first senses as its meaning, and its hanja in the note when it has them.
- Affixes, endings and multiword entries are left out, as are words with no
  English equivalent.
- Every word without a frequency tag gets one from wordfreq's Zipf frequency:
  core at 4.5 and above, common from 3.5, rare below.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fmt  # noqa: E402
import lib  # noqa: E402
from freq import zipf_tagger  # noqa: E402
from hangul import romanize  # noqa: E402

COMMIT = "e7249562dca526461a347eb2cc5a2e67a17c4488"
URL = f"https://raw.githubusercontent.com/spellcheck-ko/korean-dict-nikl-krdict/{COMMIT}/{{name}}"
FILES = [f"{n}.xml" for n in range(5000, 55000, 5000)] + ["51947.xml"]
LEVELS = [("초급", "beginner", "Beginner words"), ("중급", "intermediate", "Intermediate words"),
          ("고급", "advanced", "Advanced words")]
SKIP_POS = {"접사", "어미"}
SOURCE = "NIKL Basic Korean Dictionary (한국어기초사전)"
LICENSE = "CC BY-SA 2.0 KR"
NOTES = [
    "The decks Beginner, Intermediate and Advanced words are imported by tools/importers/krdict.py "
    "from the National Institute of Korean Language's Basic Korean Dictionary (CC BY-SA 2.0 KR), "
    "which grades each word beginner, intermediate or advanced; the level is kept as nikl.",
    "Frequency tags come from wordfreq (CC BY-SA 4.0).",
]
HANJA = re.compile(r"^[㐀-鿿豈-﫿]+$")
VAL = re.compile(r'(val=")([^"]*)(")')


def fetch(name, cache):
    path = cache / name
    if not path.is_file():
        cache.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL.format(name=name)) as r:
            path.write_bytes(r.read())
    return path


def entries_in(path):
    """The dictionary's entries as dicts. The export has a few raw '<' inside
    attribute values, so those are escaped before parsing."""
    text = path.read_text(encoding="utf-8")
    text = VAL.sub(lambda m: m[1] + m[2].replace("<", "&lt;").replace(">", "&gt;") + m[3], text)
    root = ET.fromstring(text.encode("utf-8"))
    for el in root.iter("LexicalEntry"):
        feats = {f.get("att"): f.get("val") for f in el.findall("feat")}
        senses = []
        for s in el.findall("Sense"):
            for eq in s.findall("Equivalent"):
                f = {x.get("att"): x.get("val") for x in eq.findall("feat")}
                if f.get("language") == "영어" and f.get("lemma"):
                    senses.append(f["lemma"])
        yield {"word": el.find("Lemma/feat[@att='writtenForm']").get("val").strip(),
               "unit": feats.get("lexicalUnit"), "pos": feats.get("partOfSpeech"),
               "level": feats.get("vocabularyLevel"), "origin": feats.get("origin", ""),
               "homonym": feats.get("homonym_number", "0"), "english": senses}


def meaning(senses, most=4):
    """The English equivalents of the first senses, without repeats, as 'a; b'."""
    out = []
    for s in senses:
        for alt in re.split(r"\s*;\s*", s.strip()):
            alt = re.sub(r"\s+", " ", alt).strip()
            if alt and alt.lower() not in (o.lower() for o in out):
                out.append(alt)
    return "; ".join(out[:most])


def build(header, entries, words, freq):
    own = [e for e in entries if not e["deck"].startswith("nikl-")]
    decks = [d for d in header["decks"] if not d["id"].startswith("nikl-")]
    grade = {k: (i, slug) for i, (k, slug, _) in enumerate(LEVELS)}
    graded = [w for w in words if w["level"] in grade and w["unit"] == "단어" and w["pos"] not in SKIP_POS
              and not w["word"].startswith("-") and not w["word"].endswith("-")]
    graded.sort(key=lambda w: (grade[w["level"]][0], w["word"], int(w["homonym"] or 0)))
    by_word = {}
    for e in own:
        by_word.setdefault(e["word"], []).append(e)
    added, skipped, ids = {slug: [] for _, slug, _ in LEVELS}, 0, set()
    for w in graded:
        slug = grade[w["level"]][1]
        if w["word"] in by_word:
            for e in by_word[w["word"]]:
                e.setdefault("level", {}).setdefault("nikl", slug)
            continue
        m = meaning(w["english"])
        if not m:
            skipped += 1
            continue
        deck = f"nikl-{slug}"
        id_ = f"{deck}/{w['word']}"
        if id_ in ids:
            id_ = f"{id_}/{w['homonym']}"
        ids.add(id_)
        e = {"id": id_, "deck": deck, "word": w["word"], "reading": romanize(w["word"]), "meaning": m,
             "level": {"nikl": slug}}
        if HANJA.match(w["origin"]):
            e["note"] = f"Hanja: {w['origin']}"
        added[slug].append(e)
    out = own + [e for _, slug, _ in LEVELS for e in added[slug]]
    for e in out:
        if "freq" not in e:
            e["freq"] = freq(e["word"])
    head = dict(header)
    head["notes"] = [x for x in header.get("notes", []) if x not in NOTES and "krdict.py" not in x] + NOTES
    head["source"], head["license"] = SOURCE, LICENSE
    head["decks"] = decks + [{"id": f"nikl-{slug}", "title": title} for _, slug, title in LEVELS if added[slug]]
    return head, out, skipped


def main():
    path = lib.ROOT / "languages" / "hangul" / "vocab.jsonl"
    header, entries = lib.read(path)
    cache = lib.ROOT / "cache" / "krdict" / COMMIT[:12]
    words = [w for name in FILES for w in entries_in(fetch(name, cache))]
    head, out, skipped = build(header, entries, words, zipf_tagger("ko"))
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in [head, *out]), encoding="utf-8")
    path.write_text(fmt.format_file(path), encoding="utf-8")
    new = sum(e["deck"].startswith("nikl-") for e in out)
    tagged = sum(not e["deck"].startswith("nikl-") and "nikl" in e.get("level", {}) for e in out)
    print(f"{path.relative_to(lib.ROOT)}: {new} graded words added, {tagged} written words tagged, "
          f"{skipped} left out with no English")


if __name__ == "__main__":
    main()
