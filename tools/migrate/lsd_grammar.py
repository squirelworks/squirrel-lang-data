#!/usr/bin/env python3
"""Convert LanguageStudentDesk's languages/<id>/grammar.js courses to grammar@1.

    python3 tools/migrate/lsd_grammar.py <LanguageStudentDesk checkout>

Needs node, since the courses are JavaScript literals. Writes
languages/<id>/grammar.json here. The comment at the top of each file becomes
`notes`, line by line. Klingon's verb prefix grid (window.KLINGON_GRID)
becomes its `drillData`. Run tools/fmt.py afterwards.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DUMP = r"""
const fs = require("fs"), path = require("path");
global.window = global;
const file = process.argv[1];
eval(fs.readFileSync(file, "utf8"));
const id = path.basename(path.dirname(file));
process.stdout.write(JSON.stringify({ course: window.GRAMMAR[id], grid: window.KLINGON_GRID || null }));
"""


def comment_lines(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[3:] if line.startswith("// ") else line[2:])
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def convert(lang, course, grid, notes):
    out = {"schema": "grammar@1", "language": lang}
    if notes:
        out["notes"] = notes
    out.update(course)
    if grid:
        out["drillData"] = grid
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "languages"
    lessons = 0
    for p in sorted(src.glob("*/grammar.js")):
        lang = p.parent.name
        dumped = json.loads(subprocess.run(["node", "-e", DUMP, str(p)], capture_output=True, text=True, check=True).stdout)
        out = convert(lang, dumped["course"], dumped["grid"], comment_lines(p.read_text(encoding="utf-8")))
        (ROOT / "languages" / lang / "grammar.json").write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8")
        lessons += len(out["lessons"])
    print(f"wrote {lessons} lessons")


if __name__ == "__main__":
    main()
