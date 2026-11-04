#!/usr/bin/env python3
"""Checks on SquirrelGo Alphabets courses that a schema can't express.

    python3 tools/check_alphabets.py

- A course's id is its file name, and no character card is listed twice.
- Every character a card shows (both cases, for "Ա ա") has strokes in
  strokes/<id>.jsonl, since the app draws and checks each one.
- Joined letter forms (nonJoining) go with right-to-left scripts.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def check(root=lib.ROOT):
    problems = []
    for p in sorted((root / "alphabets").glob("*.json")):
        rel = p.relative_to(root)
        try:
            course = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
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
            missing = sorted(forms - drawn)
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
