#!/usr/bin/env python3
"""Convert SquirrelGo Alphabets' script files to alphabet@1.

    python3 tools/migrate/lsd_alphabets.py <LanguageStudentDesk checkout>

Needs node, since the courses are JavaScript. Reads every
SquirrelGo-Apps/squirrelgo-characters/squirrelgo-alphabets/www/data/<id>.js
(except app.js) and writes alphabets/<id>.json. Each character array becomes
an object with named fields (FIELDS below, in array order); the comment at the
top of the file becomes the notes. Run tools/fmt.py afterwards.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ["char", "roman", "hint", "example", "exampleRoman", "meaning", "speak", "ipa", "exampleLang", "exampleIpa"]
ORDER = ["id", "title", "native", "lang", "langName", "dir", "font", "nonJoining", "chartFlow", "blurb", "writeTip",
         "audio", "voice", "bareVowel", "vertical", "lessons", "builder", "articles"]

DUMP = r"""
const fs = require("fs");
global.window = global;
window.SG_SCRIPTS = [];
eval(fs.readFileSync(process.argv[1], "utf8"));
process.stdout.write(JSON.stringify(window.SG_SCRIPTS));
"""


def notes(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[2:].strip())
    # The array layout is the app file's business; gen_alphabets.py writes its own.
    text = re.sub(r"\s*Each character is \[[^\]]*\]\.", "", " ".join(lines)).strip()
    return [text] if text else []


def convert(s, file_notes):
    out = {"schema": "alphabet@1"}
    for k in ORDER:
        if k not in s:
            continue
        if k == "lessons":
            out[k] = [dict(l, chars=[None if c is None else dict(zip(FIELDS, c, strict=False)) for c in l["chars"]])
                      for l in s[k]]
        else:
            out[k] = s[k]
    unknown = set(s) - set(ORDER)
    if unknown:
        sys.exit(f"{s['id']}: fields this tool doesn't know: {sorted(unknown)}")
    for l in s["lessons"]:
        for c in l["chars"]:
            if c is not None and len(c) > len(FIELDS):
                sys.exit(f"{s['id']}: {c[0]} has more fields than this tool knows")
    if file_notes:
        out["notes"] = file_notes
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    data = Path(sys.argv[1]) / "SquirrelGo-Apps/squirrelgo-characters/squirrelgo-alphabets/www/data"
    (ROOT / "alphabets").mkdir(exist_ok=True)
    n = 0
    for p in sorted(data.glob("*.js")):
        if p.name == "app.js":
            continue
        scripts = json.loads(subprocess.run(["node", "-e", DUMP, str(p)], capture_output=True, text=True, check=True).stdout)
        for s in scripts:
            (ROOT / "alphabets" / f"{s['id']}.json").write_text(
                json.dumps(convert(s, notes(p.read_text(encoding="utf-8"))), ensure_ascii=False), encoding="utf-8")
            n += 1
    print(f"wrote {n} alphabets")


if __name__ == "__main__":
    main()
