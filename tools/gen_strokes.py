#!/usr/bin/env python3
"""Generate the SquirrelGo apps' stroke files from strokes/*.jsonl.

    python3 data/tools/gen_strokes.py --apps SquirrelGo-Apps            # write
    python3 data/tools/gen_strokes.py --apps SquirrelGo-Apps --check    # exit 1 if stale

Each set goes to the files listed in TARGETS (relative to --apps), in the form
the app's stroke player reads:

    keyed   window.SG_STROKES["<set>"] = {char: [path, ...]}   (Alphabets, Kana, Bopomofo)
    plain   window.SG_STROKES = {letter: [path, ...]}          (Klingon)
    kanji   window.KANJI_STROKES = {char: [[path, ...], [[x, y], ...]]}
    kana    window.KANA_STROKES, the same, merged into KANJI_STROKES

A set with no TARGETS entry is a SquirrelGo Alphabets script. Where an app also
commits a copy of its www/ under android/, both are written.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

C = "squirrelgo-characters"
ANDROID = "android/app/src/main/assets/www"
TARGETS = {
    "hiragana": ("keyed", [f"{C}/squirrelgo-kana/www/data/strokes/hiragana.js"]),
    "katakana": ("keyed", [f"{C}/squirrelgo-kana/www/data/strokes/katakana.js"]),
    "kana": ("kana", [f"{C}/squirrelgo-kana/www/data/kana-strokes.js"]),
    "kanji": ("kanji", [f"{C}/squirrelgo-kanji/www/data/strokes.js", f"{C}/squirrelgo-kanji/{ANDROID}/data/strokes.js"]),
    "klingon": ("plain", [f"{C}/squirrelgo-klingon/www/data/strokes.js"]),
    "zhuyin": ("keyed", [f"{C}/squirrelgo-bopomofo/www/data/strokes/zhuyin.js",
                         f"{C}/squirrelgo-bopomofo/{ANDROID}/data/strokes/zhuyin.js"]),
}
ALL = None


def targets(apps, sets):
    """{set: (form, [absolute paths])} for the given set names, or every set
    with a file here (strokes/) or, for ALL, every file the apps have."""
    names = sets
    if names is ALL:
        alphabets = apps / C / "squirrelgo-alphabets" / "www" / "data" / "strokes"
        names = list(TARGETS) + sorted(p.stem for p in alphabets.glob("*.js"))
    out = {}
    for n in names:
        form, rels = TARGETS.get(n, ("keyed", [f"{C}/squirrelgo-alphabets/www/data/strokes/{n}.js"]))
        out[n] = (form, [apps / r for r in rels])
    return out


def script(header, entries, form, commit, command):
    lines = [f"// Generated from squirrel-lang-data {commit} strokes/{header['set']}.jsonl by: {command}"]
    lines += [f"// {l}" for n in header.get("notes", []) for l in _wrap(n)]
    lines.append(f"// Source: {header['source']} ({header['license']}).")
    if form in ("kanji", "kana"):
        body = json.dumps({e["char"]: [e["strokes"], e.get("labels", [])] for e in entries},
                          ensure_ascii=False, separators=(",", ":"))
        name = "KANJI_STROKES" if form == "kanji" else "KANA_STROKES"
        lines.append(f"window.{name} = {body};")
        if form == "kana":
            lines.append("window.KANJI_STROKES = Object.assign(window.KANJI_STROKES || {}, window.KANA_STROKES);")
        return "\n".join(lines) + "\n"
    rows = ",\n".join(f"  {json.dumps(e['char'], ensure_ascii=False)}: {json.dumps(e['strokes'])}" for e in entries)
    if form == "plain" or (form == "keyed" and header["set"] not in TARGETS):
        rows += ","  # the Alphabets and Klingon files end every entry with a comma
    if form == "plain":
        lines.append("window.SG_STROKES = {")
    else:
        lines += ["window.SG_STROKES = window.SG_STROKES || {};", f"window.SG_STROKES[{json.dumps(header['set'])}] = {{"]
    return "\n".join(lines) + "\n" + rows + "\n};\n"


def _wrap(text):
    import textwrap
    return textwrap.wrap(text, 77)


def build(data, apps, command):
    """{absolute path: text} for every set in strokes/."""
    commit = lib.data_commit(data)
    files = {}
    paths = sorted((data / "strokes").glob("*.jsonl"))
    where = targets(apps, [p.stem for p in paths])
    for p in paths:
        header, entries = lib.read(p)
        form, outs = where[p.stem]
        for out in outs:
            files[out] = script(header, entries, form, commit, command)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apps", required=True, type=Path, help="the consumer's SquirrelGo-Apps/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_strokes.py --apps {args.apps.name}"
    files = {str(p.relative_to(args.apps)): t for p, t in build(args.data, args.apps, command).items()}
    return lib.write_outputs(files, args.apps, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
