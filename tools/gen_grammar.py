#!/usr/bin/env python3
"""Generate LanguageStudentDesk's grammar.js courses from languages/*/grammar.json.

    python3 data/tools/gen_grammar.py --out languages            # write
    python3 data/tools/gen_grammar.py --out languages --check    # exit 1 if stale

Writes --out/<id>/grammar.js for each language with a course: a classic script
that sets window.GRAMMAR[<id>] to { title, intro, lessons, plan }. A course's
drillData is published under the global its app already reads (Klingon's
window.KLINGON_GRID).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

# The global each language's drillData is published as.
DRILL_GLOBALS = {"klingon": "KLINGON_GRID"}
COURSE = ("title", "intro", "lessons", "plan")


def script(lang, course, commit, command):
    lines = [f"// Generated from squirrel-lang-data {commit} languages/{lang}/grammar.json by: {command}"]
    lines += [("// " + l).rstrip() for l in course.get("notes", [])]
    lines.append("window.GRAMMAR = window.GRAMMAR || {};")
    if "drillData" in course:
        name = DRILL_GLOBALS.get(lang, "GRAMMAR_DRILL_DATA_" + re.sub(r"\W", "_", lang).upper())
        lines.append(f"window.{name} = {json.dumps(course['drillData'], ensure_ascii=False, indent=2)};")
    prop = f".{lang}" if re.fullmatch(r"[A-Za-z_$][\w$]*", lang) else f"[{json.dumps(lang)}]"
    body = {k: course[k] for k in COURSE if k in course}
    lines.append(f"window.GRAMMAR{prop} = {json.dumps(body, ensure_ascii=False, indent=2)};")
    return "\n".join(lines) + "\n"


def build(data, command):
    commit = lib.data_commit(data)
    return {f"{p.parent.name}/grammar.js": script(p.parent.name, lib.read(p), commit, command)
            for p in sorted((data / "languages").glob("*/grammar.json"))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the consumer's languages/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_grammar.py --out {args.out.name}"
    return lib.write_outputs(build(args.data, command), args.out, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
