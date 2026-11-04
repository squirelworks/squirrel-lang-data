#!/usr/bin/env python3
"""Checks on character tables that a schema can't express.

    python3 tools/check_characters.py

Script tables (characters@1, languages/<id>/characters/<script>.jsonl):
- The header's language is the folder's id and its script is the file name.
- No script key is used twice in the repo, since apps file tables under it.
- No character is listed twice in a table, and each group's characters sit
  together.

The shared CJK table (cjk@1, cjk/characters.jsonl) and the readings
(cjk-readings@1, languages/<id>/characters/<tradition>.jsonl):
- Each tradition's readings sit with its language (kanji with japanese, hanzi
  with chinese, hanja with hangul), in a file named after the tradition.
- No character is listed twice in a file.
- Every character a tradition reads is in the shared table, and every
  character in the table is read by at least one tradition.
- Stroke counts are at least 1.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

TRADITIONS = {"kanji": "japanese", "hanzi": "chinese", "hanja": "hangul"}
TABLE = Path("cjk") / "characters.jsonl"


def check(root=lib.ROOT):
    problems, scripts, read = [], {}, {}
    for p in sorted((root / "languages").glob("*/characters/*.jsonl")):
        rel = p.relative_to(root)
        lang = p.parent.parent.name
        try:
            header, entries = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        if header.get("language") != lang:
            problems.append(f"{rel}:1: language {header.get('language')!r} should be {lang!r}")
        kind = header.get("schema")
        if kind == "characters@1":
            key = header.get("script")
            if key != p.stem:
                problems.append(f"{rel}:1: script {key!r} should be {p.stem!r}, the file name")
            if key in scripts:
                problems.append(f"{rel}:1: script {key!r} is also {scripts[key]}")
            scripts.setdefault(key, rel)
        elif kind == "cjk-readings@1":
            tradition = header.get("tradition")
            if tradition != p.stem:
                problems.append(f"{rel}:1: tradition {tradition!r} should be {p.stem!r}, the file name")
            elif TRADITIONS.get(tradition) != lang:
                problems.append(f"{rel}:1: {tradition} readings belong in languages/{TRADITIONS[tradition]}/characters/")
            elif tradition in read:
                problems.append(f"{rel}:1: {tradition} readings are listed twice")
            else:
                read[tradition] = (rel, [e.get("char") for e in entries])
        else:
            problems.append(f"{rel}:1: schema {kind!r} isn't a character table (characters@1 or cjk-readings@1)")
            continue
        seen, groups, last = set(), set(), None
        for n, e in enumerate(entries, start=2):
            ch = e.get("char")
            if ch in seen:
                problems.append(f"{rel}:{n}: {ch} is listed twice")
            seen.add(ch)
            g = e.get("group")
            if g != last and g in groups:
                problems.append(f"{rel}:{n}: group {g!r} is split; keep its characters together")
            groups.add(g)
            last = g

    table = {}
    if (root / TABLE).is_file():
        try:
            header, entries = lib.read(root / TABLE)
        except ValueError as e:
            return problems + [f"{TABLE}: does not parse ({e})"]
        for n, e in enumerate(entries, start=2):
            ch = e.get("char")
            if ch in table:
                problems.append(f"{TABLE}:{n}: {ch} is listed twice")
            table[ch] = n
            if isinstance(e.get("strokes"), int) and e["strokes"] < 1:
                problems.append(f"{TABLE}:{n}: {ch} has {e['strokes']} strokes")
    elif read:
        problems.append(f"{TABLE} is missing, but {', '.join(sorted(read))} readings need it")
    used = set()
    for tradition, (rel, chars) in sorted(read.items()):
        for n, ch in enumerate(chars, start=2):
            used.add(ch)
            if table and ch not in table:
                problems.append(f"{rel}:{n}: {ch} is not in {TABLE}")
    for ch, n in table.items():
        if ch not in used:
            problems.append(f"{TABLE}:{n}: {ch} has no readings in any tradition")
    return problems


def main():
    problems = check()
    print("\n".join(problems) or "characters: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
