#!/usr/bin/env python3
"""Checks on reference cards that a schema can't express.

    python3 tools/check_reference.py

- The file's language is the folder's id, and card ids are unique.
- Every table row has as many cells as the table's head.
- A card's sources are listed in SOURCES.md.

It also reports how many cards have no level yet (information only).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def listed_sources(root):
    """Source names from the first column of SOURCES.md's table."""
    p = root / "SOURCES.md"
    if not p.is_file():
        return set()
    names = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1) not in ("Source", "---"):
            names.add(m.group(1))
    return names


def check(root=lib.ROOT):
    problems, unlevelled = [], {}
    sources = listed_sources(root)
    for p in sorted((root / "languages").glob("*/reference.json")):
        rel = p.relative_to(root)
        lang = p.parent.name
        try:
            ref = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        if ref.get("language") != lang:
            problems.append(f"{rel}: language {ref.get('language')!r} should be {lang!r}")
        seen = set()
        for e in ref.get("entries", []):
            where = f"{rel}: {e.get('id')}"
            if e.get("id") in seen:
                problems.append(where + ": id is used twice")
            seen.add(e.get("id"))
            if "level" not in e:
                unlevelled[lang] = unlevelled.get(lang, 0) + 1
            table = e.get("table") or {}
            for row in table.get("rows", []):
                if len(row) != len(table.get("head", [])):
                    problems.append(where + f": table row {row[:1]} has {len(row)} cells, the head has {len(table.get('head', []))}")
            for s in e.get("sources", []):
                if s not in sources:
                    problems.append(where + f": source {s!r} isn't listed in SOURCES.md")
    return problems, unlevelled


def main():
    problems, unlevelled = check()
    print("\n".join(problems) or "reference: OK")
    if unlevelled:
        print(f"reference: {sum(unlevelled.values())} cards in {len(unlevelled)} languages have no level yet")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
