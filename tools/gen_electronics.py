#!/usr/bin/env python3
"""Generate Electronics Learner JS packs from electronics/.

    python3 data/tools/gen_electronics.py --out electronics-learner/data            # write
    python3 data/tools/gen_electronics.py --out electronics-learner/data --check    # exit 1 if stale

Writes catalog.js (window.ELECTRONICS_CATALOG) and <id>.js (window.ELECTRONICS[<id>]) for
each course under electronics/<id>/course.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

COURSE_KEYS = ("id", "name", "title", "intro", "lessons")


def _dump(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def catalog_script(catalog: dict, commit: str, command: str) -> str:
    courses = catalog.get("courses") or []
    lines = [
        f"// Generated from squirrel-lang-data {commit} electronics/catalog.json by: {command}",
        "// Courses in the Electronics Learner. Order here doesn't matter: the page may sort",
        "// by group. Each id has a course in data/<id>.js.",
        f"window.ELECTRONICS_CATALOG = {_dump(courses)};",
        "",
    ]
    return "\n".join(lines)


def course_script(course: dict, commit: str, command: str) -> str:
    cid = course["id"]
    body = {k: course[k] for k in COURSE_KEYS if k in course}
    prop = f".{cid}" if re.fullmatch(r"[A-Za-z_$][\w$]*", cid) else f"[{json.dumps(cid)}]"
    lines = [
        f"// Generated from squirrel-lang-data {commit} electronics/{cid}/course.json by: {command}",
        "window.ELECTRONICS = window.ELECTRONICS || {};",
        f"window.ELECTRONICS{prop} = {_dump(body)};",
        "",
    ]
    return "\n".join(lines)


def build(data: Path, command: str) -> dict[str, str]:
    commit = lib.data_commit(data)
    math = data / "math"
    catalog = lib.read(math / "catalog.json")
    out: dict[str, str] = {"catalog.js": catalog_script(catalog, commit, command)}
    for course_path in sorted(math.glob("*/course.json")):
        course = lib.read(course_path)
        cid = course["id"]
        out[f"{cid}.js"] = course_script(course, commit, command)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the consumer's electronics-learner/data folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    if not (args.data / "math" / "catalog.json").is_file():
        print(f"{args.data / 'math' / 'catalog.json'}: missing")
        return 1
    command = "python3 data/tools/gen_electronics.py --out electronics-learner/data"
    return lib.write_outputs(build(args.data, command), args.out, args.check, command)


if __name__ == "__main__":
    raise SystemExit(main())
