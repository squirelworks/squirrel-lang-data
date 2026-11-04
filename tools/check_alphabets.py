#!/usr/bin/env python3
"""Checks on the SquirrelGo character apps' courses that a schema can't express.

    python3 tools/check_alphabets.py

- A course's id is its file name, and no character card is listed twice.
- Every character a card shows (both cases, for "Ա ա") has strokes in
  strokes/<id>.jsonl, since the app draws and checks each one; NO_STROKES
  lists the cards that aren't single characters to write.
- Joined letter forms (nonJoining) go with right-to-left scripts.

The Klingon course (klingon@1): each letter and digit is taught once, has
strokes in strokes/klingon.jsonl and a pIqaD code point (U+F8D0 to U+F8FF)
no other uses, and every letter has its IPA.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


# Cards that are read, not written, so they have no strokes: {course: {card: why}}.
NO_STROKES = {
    "zhuyin": {"你好": "a word in the Everyday syllables lesson", "台灣": "a word in the Everyday syllables lesson",
               "注音": "a word in the Everyday syllables lesson", "謝謝": "a word in the Everyday syllables lesson",
               "（平）": "the first tone, which has no mark"},
}


def check_klingon(rel, course, root):
    problems = []
    cards = [(l, c) for l in course.get("lessons", []) for c in l.get("chars", [])]
    strokes = root / "strokes" / "klingon.jsonl"
    drawn = {e.get("char") for e in lib.read(strokes)[1]} if strokes.is_file() else set()
    romans, points = set(), set()
    for lesson, c in cards:
        r, cp = c.get("roman"), c.get("codepoint")
        if r in romans:
            problems.append(f"{rel}: {r} is taught twice")
        if cp in points:
            problems.append(f"{rel}: {r}: code point {cp:#x} is used twice")
        romans.add(r)
        points.add(cp)
        if not isinstance(cp, int) or not 0xF8D0 <= cp <= 0xF8FF:
            problems.append(f"{rel}: {r}: code point {cp!r} is outside U+F8D0 to U+F8FF")
        if r not in drawn:
            problems.append(f"{rel}: {r} has no strokes in strokes/klingon.jsonl")
        if not lesson.get("numerals") and r not in course.get("ipa", {}):
            problems.append(f"{rel}: {r} has no IPA")
    return problems


def check(root=lib.ROOT):
    problems = []
    for p in sorted((root / "alphabets").glob("*.json")):
        rel = p.relative_to(root)
        try:
            course = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        if course.get("schema") == "klingon@1":
            problems += check_klingon(rel, course, root)
            continue
        cid = course.get("id")
        if cid != p.stem:
            problems.append(f"{rel}: id {cid!r} should be {p.stem!r}, the file name")
        cards = [c for l in course.get("lessons", []) for c in l.get("chars", []) if isinstance(c, dict)]
        seen = set()
        for c in cards:
            if c.get("char") in seen:
                problems.append(f"{rel}: {c.get('char')} is taught twice")
            seen.add(c.get("char"))
        forms = {f for c in cards for f in str(c.get("char", "")).split(" ") if f}
        strokes = root / "strokes" / f"{p.stem}.jsonl"
        if not strokes.is_file():
            problems.append(f"{rel}: strokes/{p.stem}.jsonl is missing")
        else:
            drawn = {e.get("char") for e in lib.read(strokes)[1]}
            missing = sorted(forms - drawn - set(NO_STROKES.get(p.stem, {})))
            if missing:
                problems.append(f"{rel}: no strokes in strokes/{p.stem}.jsonl for {' '.join(missing)}")
        if "nonJoining" in course:
            if course.get("dir") != "rtl":
                problems.append(f"{rel}: nonJoining is set but the script isn't right to left")
    return problems


def main():
    problems = check()
    print("\n".join(problems) or "alphabets: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
