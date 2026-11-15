#!/usr/bin/env python3
"""Check programming/ catalog and courses hang together.

    python3 tools/check_programming.py

Each course folder must have course.json whose id matches the folder name.
Every catalog id must have a course folder once courses start landing; until
then, catalog entries without a folder are listed as notes, not errors, so
the first schema PR can ship the catalog alone with one pilot course.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROG = ROOT / "programming"


def main() -> int:
    if not PROG.is_dir():
        print("programming/: missing")
        return 1
    catalog_path = PROG / "catalog.json"
    if not catalog_path.is_file():
        print("programming/catalog.json: missing")
        return 1
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema") != "programming-catalog@1":
        print("programming/catalog.json: schema must be programming-catalog@1")
        return 1
    courses = catalog.get("courses") or []
    ids = [c["id"] for c in courses]
    problems: list[str] = []
    if len(ids) != len(set(ids)):
        problems.append("programming/catalog.json: duplicate course ids")
    folders = {
        p.name
        for p in PROG.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }
    for folder in sorted(folders):
        course_path = PROG / folder / "course.json"
        if not course_path.is_file():
            problems.append(f"programming/{folder}/: missing course.json")
            continue
        course = json.loads(course_path.read_text(encoding="utf-8"))
        if course.get("schema") != "programming-course@1":
            problems.append(f"programming/{folder}/course.json: schema must be programming-course@1")
        if course.get("id") != folder:
            problems.append(
                f"programming/{folder}/course.json: id {course.get('id')!r} "
                f"must match the folder name"
            )
        if folder not in ids:
            problems.append(f"programming/{folder}/: not listed in catalog.json")
    for cid in ids:
        if cid in folders:
            continue
        # Allowed until the migration finishes: catalog can name courses
        # still living only in LanguageStudentDesk.
        print(f"note: catalog lists {cid} but programming/{cid}/ is not here yet")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"programming: catalog {len(ids)} courses, {len(folders)} folders OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
