#!/usr/bin/env python3
"""Checks on vocabulary that a schema can't express.

    python3 tools/check_vocab.py

- The header's language is the folder's id, and every deck it lists has words.
- Every word is in a listed deck, its id is unique, and decks come in the
  header's order, so the file reads in teaching order.
- A language gives a reading for every word or for none.
- Any variety a word names exists under the language.

It also reports how many words still have no level or frequency tag. That is
information only until the words are tagged.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def check(root=lib.ROOT):
    problems, untagged = [], {}
    for p in sorted((root / "languages").glob("*/vocab.jsonl")):
        rel = p.relative_to(root)
        lang = p.parent.name
        try:
            header, entries = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        if header.get("language") != lang:
            problems.append(f"{rel}:1: language {header.get('language')!r} should be {lang!r}")
        order = [d.get("id") for d in header.get("decks", [])]
        if len(set(order)) != len(order):
            problems.append(f"{rel}:1: a deck id is listed twice")
        varieties = {v.name for v in (p.parent / "varieties").iterdir()} if (p.parent / "varieties").is_dir() else set()
        seen, used, last = set(), set(), -1
        with_reading = 0
        for n, e in enumerate(entries, start=2):
            deck = e.get("deck")
            if deck not in order:
                problems.append(f"{rel}:{n}: deck {deck!r} is not listed in the header")
            else:
                i = order.index(deck)
                if i < last:
                    problems.append(f"{rel}:{n}: deck {deck!r} comes after a later deck; keep each deck's words together, in header order")
                last = max(last, i)
                used.add(deck)
            if e.get("id") in seen:
                problems.append(f"{rel}:{n}: id {e.get('id')!r} is used twice")
            seen.add(e.get("id"))
            with_reading += "reading" in e
            for v in e.get("varieties", []):
                if v not in varieties:
                    problems.append(f"{rel}:{n}: variety {v!r} doesn't exist under languages/{lang}/varieties/")
            if not e.get("level") and not e.get("freq"):
                untagged[lang] = untagged.get(lang, 0) + 1
        for d in order:
            if d not in used:
                problems.append(f"{rel}:1: deck {d!r} has no words")
        if 0 < with_reading < len(entries):
            problems.append(f"{rel}: {with_reading} of {len(entries)} words have a reading; give every word one, or none")
    return problems, untagged


def main():
    problems, untagged = check()
    print("\n".join(problems) or "vocab: OK")
    if untagged:
        print(f"vocab: {sum(untagged.values())} words in {len(untagged)} languages have no level or frequency tag yet")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
