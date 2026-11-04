#!/usr/bin/env python3
"""Checks on grammar courses that a schema can't express.

    python3 tools/check_grammar.py

- The course's language is the folder's id.
- Lesson ids are unique, and planned points don't reuse a lesson's id.
- Every drill's answer is one of its options.
- A planned point's "after" names a lesson or another planned point.
- A lesson that generates drills has drillData to build them from.

It also reports how many lessons have no level yet (information only).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def check(root=lib.ROOT):
    problems, unlevelled = [], {}
    for p in sorted((root / "languages").glob("*/grammar.json")):
        rel = p.relative_to(root)
        lang = p.parent.name
        try:
            course = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        if course.get("language") != lang:
            problems.append(f"{rel}: language {course.get('language')!r} should be {lang!r}")
        ids = set()
        for lesson in course.get("lessons", []):
            lid = lesson.get("id")
            if lid in ids:
                problems.append(f"{rel}: lesson id {lid!r} is used twice")
            ids.add(lid)
            if "level" not in lesson:
                unlevelled[lang] = unlevelled.get(lang, 0) + 1
            if "generate" in lesson and "drillData" not in course:
                problems.append(f"{rel}: lesson {lid!r} generates drills but the course has no drillData")
            for i, d in enumerate(lesson.get("drills", []), start=1):
                if d.get("answer") not in d.get("options", []):
                    problems.append(f"{rel}: lesson {lid!r} drill {i}: answer {d.get('answer')!r} is not one of its options")
        planned = set()
        for point in course.get("plan", []):
            pid = point.get("id")
            if pid in ids or pid in planned:
                problems.append(f"{rel}: planned point {pid!r} reuses an id")
            planned.add(pid)
        for point in course.get("plan", []):
            for a in point.get("after", []):
                if a not in ids and a not in planned:
                    problems.append(f"{rel}: planned point {point.get('id')!r} comes after {a!r}, which isn't a lesson or planned point")
    return problems, unlevelled


def main():
    problems, unlevelled = check()
    print("\n".join(problems) or "grammar: OK")
    if unlevelled:
        print(f"grammar: {sum(unlevelled.values())} lessons in {len(unlevelled)} languages have no level yet")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
