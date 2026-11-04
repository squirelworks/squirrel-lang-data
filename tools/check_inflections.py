#!/usr/bin/env python3
"""Checks on inflection tables that a schema can't express.

    python3 tools/check_inflections.py

For every languages/<id>/inflections.jsonl (inflections@1):
- The header's language matches the folder.
- Each word's m is a content meaning in meaning/meanings.jsonl, and each
  feature of each form is a meaning there (grammar or content).
- No lemma is listed twice with the same m, and no word names two forms alike.
- Each word has a form named dictionary, and its text is the lemma.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def meanings(root):
    """{id: kind} for every meaning in meaning/meanings.jsonl."""
    path = root / "meaning" / "meanings.jsonl"
    if not path.is_file():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return {m["id"]: m.get("kind", "") for m in map(json.loads, filter(None, lines))}


def check_file(path, known, root=lib.ROOT):
    rel = path.relative_to(root)
    try:
        header, words = lib.read(path)
    except ValueError as e:
        return [f"{rel}: does not parse ({e})"]
    problems = []
    if header.get("language") != path.parent.name:
        problems.append(f"{rel}:1: language {header.get('language')!r} is not the folder {path.parent.name!r}")
    seen = set()
    for n, word in enumerate(words, start=2):
        lemma, m = word.get("lemma"), word.get("m")
        if (lemma, m) in seen:
            problems.append(f"{rel}:{n}: {lemma} ({m}) is listed twice")
        seen.add((lemma, m))
        if m not in known:
            problems.append(f"{rel}:{n}: m {m!r} is not a meaning in meaning/meanings.jsonl")
        elif known[m] == "grammar":
            problems.append(f"{rel}:{n}: m {m!r} is a grammar meaning; a word carries a content meaning")
        names = [f.get("name") for f in word.get("forms", [])]
        for name in sorted({x for x in names if names.count(x) > 1}):
            problems.append(f"{rel}:{n}: {lemma} names two forms {name!r}")
        dictionary = [f for f in word.get("forms", []) if f.get("name") == "dictionary"]
        if not dictionary:
            problems.append(f"{rel}:{n}: {lemma} has no form named dictionary")
        elif dictionary[0].get("text") != lemma:
            problems.append(f"{rel}:{n}: {lemma}'s dictionary form is {dictionary[0].get('text')!r}, not the lemma")
        for form in word.get("forms", []):
            for feature in form.get("features", []):
                if feature not in known:
                    problems.append(f"{rel}:{n}: {lemma} {form.get('name')}: feature {feature!r} is not a meaning")
    return problems


def check(root=lib.ROOT):
    known = meanings(root)
    problems = []
    for path in sorted((root / "languages").glob("*/inflections.jsonl")):
        problems += check_file(path, known, root)
    return problems


def main():
    problems = check()
    print("\n".join(problems) or "inflections: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
