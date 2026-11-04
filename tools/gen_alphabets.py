#!/usr/bin/env python3
"""Generate SquirrelGo Alphabets' script files from alphabets/*.json.

    python3 data/tools/gen_alphabets.py --apps SquirrelGo-Apps            # write
    python3 data/tools/gen_alphabets.py --apps SquirrelGo-Apps --check    # exit 1 if stale

Writes squirrelgo-characters/squirrelgo-alphabets/www/data/<id>.js under --apps
for each course: a classic script that pushes the course onto
window.SG_SCRIPTS. Each character card becomes the array the app reads,
[char, roman, hint, example, exampleRoman, meaning, speak, ipa, exampleLang,
exampleIpa], cut after the last field the card gives. The app's index.html
decides which scripts load and in what order.
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

OUT = Path("squirrelgo-characters") / "squirrelgo-alphabets" / "www" / "data"
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


def script(course, commit, command):
    body = {k: v for k, v in course.items() if k not in ("schema", "notes")}
    body["lessons"] = [dict(l, chars=[card(c) for c in l["chars"]]) for l in course["lessons"]]
    lines = [f"// Generated from squirrel-lang-data {commit} alphabets/{course['id']}.json by: {command}"]
    lines += [f"// {l}" for n in course.get("notes", []) for l in textwrap.wrap(n, 77)]
    lines.append("// Each character is [" + ", ".join(FIELDS) + "], cut after the last field it gives.")
    return ("\n".join(lines) + "\nwindow.SG_SCRIPTS = window.SG_SCRIPTS || [];\n"
            + f"window.SG_SCRIPTS.push({js(body, 0)});\n")


def build(data, command):
    commit = lib.data_commit(data)
    return {str(OUT / f"{p.stem}.js"): script(lib.read(p), commit, command)
            for p in sorted((data / "alphabets").glob("*.json"))}


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
