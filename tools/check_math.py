#!/usr/bin/env python3
"""Check math/ catalog and courses hang together.

    python3 tools/check_math.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATH = ROOT / "math"


def main() -> int:
    if not MATH.is_dir():
        print("math/: missing")
        return 1
    catalog_path = MATH / "catalog.json"
    if not catalog_path.is_file():
        print("math/catalog.json: missing")
        return 1
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema") != "math-catalog@1":
        print("math/catalog.json: schema must be math-catalog@1")
        return 1
    courses = catalog.get("courses") or []
    ids = [c["id"] for c in courses]
    problems: list[str] = []
    if len(ids) != len(set(ids)):
        problems.append("math/catalog.json: duplicate course ids")
    folders = {
        p.name
        for p in MATH.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }
    lessons = 0
    for folder in sorted(folders):
        course_path = MATH / folder / "course.json"
        if not course_path.is_file():
            problems.append(f"math/{folder}/: missing course.json")
            continue
        course = json.loads(course_path.read_text(encoding="utf-8"))
        if course.get("schema") != "math-course@1":
            problems.append(f"math/{folder}/course.json: schema must be math-course@1")
        if course.get("id") != folder:
            problems.append(
                f"math/{folder}/course.json: id {course.get('id')!r} "
                f"must match the folder name"
            )
        if folder not in ids:
            problems.append(f"math/{folder}/: not listed in catalog.json")
        for L in course.get("lessons") or []:
            lessons += 1
            for q in L.get("practice") or []:
                if q.get("answer") not in (q.get("options") or []):
                    problems.append(
                        f"math/{folder}/{L.get('id')}: answer not in options"
                    )
    for cid in ids:
        if cid not in folders:
            problems.append(f"math/catalog.json: {cid} has no math/{cid}/ folder")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"math: catalog {len(ids)} courses, {len(folders)} folders, {lessons} lessons OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
