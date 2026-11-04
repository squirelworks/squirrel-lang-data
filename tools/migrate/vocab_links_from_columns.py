#!/usr/bin/env python3
"""Seed meaning/vocab-links/<language>.jsonl from the meaning columns.

    python3 tools/migrate/vocab_links_from_columns.py [language ...]

Run once per language, then review the result by hand; the links are
content from then on, and tools/check_vocab_links.py reports column words that
aren't linked yet. A vocabulary word is linked to a token's content meanings
when the token's text is exactly the word and the word's English shares a word
with the meanings' English ("going" counts as "go", "toilets" as "toilet").
That second test keeps homographs out: Korean 가요 the song isn't linked to
go. Existing links are kept; new ones are merged in. Run tools/fmt.py
afterwards.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import lib  # noqa: E402

NOTE = ("Seeded by tools/migrate/vocab_links_from_columns.py from the words the "
        "meaning columns use, then reviewed by hand.")


def stems(text):
    out = set()
    for w in re.findall(r"[a-z']+", text.lower()):
        out.add(w)
        if w.endswith("ing") and len(w) > 4:
            out.add(w[:-3])
        if w.endswith("s") and len(w) > 3:
            out.add(w[:-1])
    return out


def seed(root, lang):
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
    order = {v["id"]: i for i, v in enumerate(vocab)}
    rows = [header] + sorted(links.values(), key=lambda e: order.get(e["vocab"], len(order)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {path.relative_to(root)}: {len(rows) - 1} words")


def main(argv):
    langs = argv or sorted(p.stem for p in (ROOT / "meaning" / "columns").glob("*.jsonl"))
    for lang in langs:
        seed(ROOT, lang)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
