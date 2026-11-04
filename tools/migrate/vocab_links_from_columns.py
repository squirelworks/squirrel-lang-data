#!/usr/bin/env python3
"""Seed meaning/vocab-links/<language>.jsonl from the meaning columns.

    python3 tools/migrate/vocab_links_from_columns.py [--glosses] [language ...]

Run once per language, then review the result by hand; the links are
content from then on, and tools/check_vocab_links.py reports column words that
aren't linked yet. A vocabulary word is linked to a token's content meanings
when the token's text is exactly the word and the word's English shares a word
with the meanings' English ("going" counts as "go", "toilets" as "toilet").
That second test keeps homographs out: Korean 가요 the song isn't linked to
go. Existing links are kept; new ones are merged in. Run tools/fmt.py
afterwards.

With --glosses it also links cards in the Desk's own starter decks (not the
imported JLPT, NIKL or frequency decks) whose first English sense, without
"to" or an article, is exactly a meaning's main English: "to eat" is eat,
"house; home" is house. A card in GLOSS_SKIP is left alone because its English
names another sense (Korean 감기 is a cold you catch, not cold weather).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import lib  # noqa: E402

IMPORTED = re.compile(r"^(jlpt-|nikl-|freq-|hsk)")
GLOSS_SKIP = {"hangul": {"body/감기"}, "hindi": {"time2/सर्दी"}, "klingon": {"family/tuq"}}

NOTE = ("Seeded by tools/migrate/vocab_links_from_columns.py --glosses from the "
        "words the meaning columns use and from starter-deck cards whose English is "
        "a meaning's main English, then reviewed by hand.")


def stems(text):
    out = set()
    for w in re.findall(r"[a-z']+", text.lower()):
        out.add(w)
        if w.endswith("ing") and len(w) > 4:
            out.add(w[:-3])
        if w.endswith("s") and len(w) > 3:
            out.add(w[:-1])
    return out


def first_sense(english):
    first = re.sub(r"\([^)]*\)", "", re.split(r"[;,]", english)[0]).strip().lower()
    return re.sub(r"^(to|a|an|the) ", "", first)


def seed(root, lang, glosses=False):
    _, meanings = lib.read(root / "meaning" / "meanings.jsonl")
    en = {m["id"]: stems(" ".join(m["en"])) for m in meanings if m["kind"] == "content"}
    _, vocab = lib.read(root / "languages" / lang / "vocab.jsonl")
    words = {}
    for v in vocab:
        words.setdefault(v["word"], []).append(v)
    path = root / "meaning" / "vocab-links" / f"{lang}.jsonl"
    header, old = lib.read(path) if path.is_file() else ({"schema": "vocab-links@1", "language": lang, "notes": [NOTE]}, [])
    links = {e["vocab"]: dict(e) for e in old}
    for r in lib.read(root / "meaning" / "columns" / f"{lang}.jsonl")[1]:
        for text, _, ms in r["t"]:
            ids = [m for m in ms.split("+") if m in en]
            if not ids:
                continue
            for v in words.get(text, []):
                if stems(v["meaning"]) & set().union(*(en[m] for m in ids)):
                    e = links.setdefault(v["id"], {"vocab": v["id"], "meanings": []})
                    e["meanings"] += [m for m in ids if m not in e["meanings"]]
    if glosses:
        main = {}
        for m in meanings:
            if m["kind"] == "content":
                main.setdefault(m["en"][0].lower(), []).append(m["id"])
        for v in vocab:
            if v["id"] in links or IMPORTED.match(v["deck"]) or v["id"] in GLOSS_SKIP.get(lang, set()):
                continue
            ids = main.get(first_sense(v["meaning"]), [])
            if len(ids) == 1:
                links[v["id"]] = {"vocab": v["id"], "meanings": ids}
    order = {v["id"]: i for i, v in enumerate(vocab)}
    rows = [header] + sorted(links.values(), key=lambda e: order.get(e["vocab"], len(order)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {path.relative_to(root)}: {len(rows) - 1} words")


def main(argv):
    glosses = "--glosses" in argv
    argv = [a for a in argv if a != "--glosses"]
    langs = argv or sorted(p.stem for p in (ROOT / "meaning" / "columns").glob("*.jsonl"))
    for lang in langs:
        seed(ROOT, lang, glosses)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
