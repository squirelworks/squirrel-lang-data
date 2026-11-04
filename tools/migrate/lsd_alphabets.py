#!/usr/bin/env python3
"""Convert the SquirrelGo character apps' script courses to alphabet@1.

    python3 tools/migrate/lsd_alphabets.py <LanguageStudentDesk checkout>

Needs node, since the courses are JavaScript. Reads every
SquirrelGo-Apps/squirrelgo-characters/squirrelgo-alphabets/www/data/<id>.js
(except app.js), plus squirrelgo-kana/www/data/kana.js (hiragana, katakana)
and squirrelgo-bopomofo/www/data/bopomofo.js (zhuyin), and writes
alphabets/<id>.json. SquirrelGo Klingon's www/data/klingon.js becomes
alphabets/klingon.json (klingon@1), each letter [romanization, code point, how
to say it, sounds like, example, meaning] an object with KLINGON fields. Each character array becomes
an object with named fields (FIELDS below, in array order); the comment at the
top of the file becomes the notes. Run tools/fmt.py afterwards.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KLINGON = ["roman", "codepoint", "say", "soundsLike", "example", "meaning"]
FIELDS = ["char", "roman", "hint", "example", "exampleRoman", "meaning", "speak", "ipa", "exampleLang", "exampleIpa"]
ORDER = ["id", "title", "native", "lang", "langName", "dir", "font", "nonJoining", "chartFlow", "blurb", "writeTip",
         "audio", "voice", "bareVowel", "vertical", "lessons", "builder", "articles"]

DUMP = r"""
const fs = require("fs");
global.window = global;
window.SG_SCRIPTS = [];
eval(fs.readFileSync(process.argv[1], "utf8").replace(/\bconst (\w+)\s*=/g, "var $1 ="));
process.stdout.write(JSON.stringify(process.argv[2] ? window.SG_KLINGON : window.SG_SCRIPTS));
"""


def notes(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[2:].strip())
    # The array layout is the app file's business; gen_alphabets.py writes its own.
    text = re.sub(r"\s*Each (character|symbol) is \[[^\]]*\]\.", "", " ".join(lines)).strip()
    text = text.replace("  ", " ")
    return [text] if text else []


def convert(s, file_notes):
    out = {"schema": "alphabet@1"}
    for k in ORDER:
        if k not in s:
            continue
        if k == "articles":
            # Bopomofo gave some bodies as a list of paragraphs, which the app
            # printed joined by commas; every other body is HTML.
            out[k] = [dict(a, body="\n".join(f"<p>{x}</p>" for x in a["body"])) if isinstance(a["body"], list) else a
                      for a in s[k]]
        elif k == "lessons":
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
    apps = Path(sys.argv[1]) / "SquirrelGo-Apps/squirrelgo-characters"
    data = apps / "squirrelgo-alphabets/www/data"
    (ROOT / "alphabets").mkdir(exist_ok=True)
    n = 0
    files = [p for p in sorted(data.glob("*.js")) if p.name != "app.js"]
    files += [apps / "squirrelgo-kana/www/data/kana.js", apps / "squirrelgo-bopomofo/www/data/bopomofo.js"]
    for p in files:
        scripts = json.loads(subprocess.run(["node", "-e", DUMP, str(p)], capture_output=True, text=True, check=True).stdout)
        for s in scripts:
            (ROOT / "alphabets" / f"{s['id']}.json").write_text(
                json.dumps(convert(s, notes(p.read_text(encoding="utf-8"))), ensure_ascii=False), encoding="utf-8")
            n += 1
    p = apps / "squirrelgo-klingon/www/data/klingon.js"
    k = json.loads(subprocess.run(["node", "-e", DUMP, str(p), "klingon"], capture_output=True, text=True, check=True).stdout)
    if set(k) != {"ipa", "lessons", "words", "articles"}:
        sys.exit(f"klingon.js: fields this tool doesn't know: {sorted(k)}")
    out = {"schema": "klingon@1", "notes": notes(p.read_text(encoding="utf-8")), "ipa": k["ipa"],
           "lessons": [dict(l, chars=[dict(zip(KLINGON, c, strict=True)) for c in l["chars"]]) for l in k["lessons"]],
           "words": k["words"], "articles": k["articles"]}
    (ROOT / "alphabets" / "klingon.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {n} alphabets and the Klingon course")


if __name__ == "__main__":
    main()
