#!/usr/bin/env python3
"""Check electronics/ catalog and courses hang together.

    python3 tools/check_electronics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELECTRONICS = ROOT / "electronics"


def main() -> int:
    if not ELECTRONICS.is_dir():
        print("electronics/: missing")
        return 1
    catalog_path = ELECTRONICS / "catalog.json"
    if not catalog_path.is_file():
        print("electronics/catalog.json: missing")
        return 1
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema") != "electronics-catalog@1":
        print("electronics/catalog.json: schema must be electronics-catalog@1")
        return 1
    courses = catalog.get("courses") or []
    ids = [c["id"] for c in courses]
    problems: list[str] = []
    if len(ids) != len(set(ids)):
        problems.append("electronics/catalog.json: duplicate course ids")
    folders = {
        p.name
        for p in ELECTRONICS.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }
    lessons = 0
    for folder in sorted(folders):
        course_path = ELECTRONICS / folder / "course.json"
        if not course_path.is_file():
            problems.append(f"electronics/{folder}/: missing course.json")
            continue
        course = json.loads(course_path.read_text(encoding="utf-8"))
        if course.get("schema") != "electronics-course@1":
            problems.append(f"electronics/{folder}/course.json: schema must be electronics-course@1")
        if course.get("id") != folder:
            problems.append(
                f"electronics/{folder}/course.json: id {course.get('id')!r} "
                f"must match the folder name"
            )
        if folder not in ids:
            problems.append(f"electronics/{folder}/: not listed in catalog.json")
        for L in course.get("lessons") or []:
            lessons += 1
            for q in L.get("practice") or []:
                if q.get("answer") not in (q.get("options") or []):
                    problems.append(
                        f"electronics/{folder}/{L.get('id')}: answer not in options"
                    )
    for cid in ids:
        if cid not in folders:
            problems.append(f"electronics/catalog.json: {cid} has no electronics/{cid}/ folder")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"electronics: catalog {len(ids)} courses, {len(folders)} folders, {lessons} lessons OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
