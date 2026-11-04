#!/usr/bin/env python3
"""Generate the SquirrelGo character apps' script courses from alphabets/*.json.

    python3 data/tools/gen_alphabets.py --apps SquirrelGo-Apps            # write
    python3 data/tools/gen_alphabets.py --apps SquirrelGo-Apps --check    # exit 1 if stale

Writes a classic script that pushes each course onto window.SG_SCRIPTS:
squirrelgo-characters/squirrelgo-alphabets/www/data/<id>.js under --apps, or
the file TARGETS names (Kana's two scripts share kana.js; Bopomofo also commits
an Android copy). alphabets/klingon.json (klingon@1) becomes SquirrelGo
Klingon's www/data/klingon.js, which sets window.SG_KLINGON. Each character card becomes the array the app reads,
[char, roman, hint, example, exampleRoman, meaning, speak, ipa, exampleLang,
exampleIpa], cut after the last field the card gives. The app's index.html
decides which scripts load and in what order.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

C = Path("squirrelgo-characters")
OUT = C / "squirrelgo-alphabets" / "www" / "data"
TARGETS = {
    "hiragana": [C / "squirrelgo-kana/www/data/kana.js"],
    "katakana": [C / "squirrelgo-kana/www/data/kana.js"],
    "zhuyin": [C / "squirrelgo-bopomofo/www/data/bopomofo.js",
               C / "squirrelgo-bopomofo/android/app/src/main/assets/www/data/bopomofo.js"],
}
FIELDS = ["char", "roman", "hint", "example", "exampleRoman", "meaning", "speak", "ipa", "exampleLang", "exampleIpa"]


def card(c):
    if c is None:
        return None
    n = max(FIELDS.index(k) for k in c) + 1
    return [c.get(k, "") for k in FIELDS[:n]]


def js(value, indent=1):
    """JSON, two-space indented, with each character card on one line."""
    pad = "  " * indent
    if isinstance(value, dict):
        items = [f"{pad}  {json.dumps(k)}: {js(v, indent + 1)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if isinstance(value, list):
        if all(v is None or isinstance(v, (str, int, float, bool)) for v in value):
            return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
        return "[\n" + ",\n".join(f"{pad}  {js(v, indent + 1)}" for v in value) + f"\n{pad}]"
    return json.dumps(value, ensure_ascii=False)


def script(courses, commit, command):
    names = " and ".join(f"alphabets/{c['id']}.json" for c in courses)
    lines = [f"// Generated from squirrel-lang-data {commit} {names} by: {command}"]
    notes = []
    for c in courses:
        notes += [n for n in c.get("notes", []) if n not in notes]
    lines += [f"// {l}" for n in notes for l in textwrap.wrap(n, 77)]
    lines.append("// Each character is [" + ", ".join(FIELDS) + "], cut after the last field it gives.")
    out = "\n".join(lines) + "\nwindow.SG_SCRIPTS = window.SG_SCRIPTS || [];\n"
    for course in courses:
        body = {k: v for k, v in course.items() if k not in ("schema", "notes")}
        body["lessons"] = [dict(l, chars=[card(c) for c in l["chars"]]) for l in course["lessons"]]
        out += f"window.SG_SCRIPTS.push({js(body, 0)});\n"
    return out


KLINGON = ["roman", "codepoint", "say", "soundsLike", "example", "meaning"]


def klingon_script(course, commit, command):
    lines = [f"// Generated from squirrel-lang-data {commit} alphabets/klingon.json by: {command}"]
    lines += [f"// {l}" for n in course.get("notes", []) for l in textwrap.wrap(n, 77)]
    lines.append("// Each character is [" + ", ".join(KLINGON) + "].")
    body = {"ipa": course["ipa"],
            "lessons": [dict(l, chars=[[c[k] for k in KLINGON] for c in l["chars"]]) for l in course["lessons"]],
            "words": course["words"], "articles": course["articles"]}
    # Code points read better in hex, as U+F8D0 is written.
    text = re.sub(r"\[(\"(?:[^\"\\]|\\.)*\"), (\d+),", lambda m: f"[{m.group(1)}, 0x{int(m.group(2)):X},", js(body, 0))
    return "\n".join(lines) + f"\nwindow.SG_KLINGON = {text};\n"


ORDER = ["hiragana", "katakana"]  # courses that share a file, in the order the app lists them


def build(data, command):
    commit = lib.data_commit(data)
    by_file = {}
    paths = sorted((data / "alphabets").glob("*.json"), key=lambda p: (ORDER.index(p.stem) if p.stem in ORDER else 0, p.stem))
    for p in paths:
        course = lib.read(p)
        if course.get("schema") == "klingon@1":
            by_file[str(C / "squirrelgo-klingon/www/data/klingon.js")] = klingon_script(course, commit, command)
            continue
        for out in TARGETS.get(p.stem, [OUT / f"{p.stem}.js"]):
            by_file.setdefault(str(out), []).append(course)
    return {f: cs if isinstance(cs, str) else script(cs, commit, command) for f, cs in by_file.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apps", required=True, type=Path, help="the consumer's SquirrelGo-Apps/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_alphabets.py --apps {args.apps.name}"
    return lib.write_outputs(build(args.data, command), args.apps, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
