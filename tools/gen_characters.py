#!/usr/bin/env python3
"""Generate the character tables apps load, from languages/*/characters/ and
cjk/characters.jsonl.

    python3 data/tools/gen_characters.py --out languages            # write
    python3 data/tools/gen_characters.py --out languages --check    # exit 1 if stale
    python3 data/tools/gen_characters.py --kanji-app FILE [--check] # SquirrelGo Kanji's table

Into LanguageStudentDesk's languages/ folder (--out) it writes:

    <id>/characters.js    window.SCRIPTS[<script>] = {name, chars} for each
                          characters@1 file of the language
    cjk/characters.js     window.LSD_CJK: {char: {uses, radical, strokes}},
                          uses being the traditions that read the character
    japanese/kanji.js     window.LSD_CJK_READINGS.<tradition> = {name, chars},
    chinese/hanzi.js      chars keyed by character; kanji also get their
    hangul/hanja.js       on'yomi groups

--kanji-app writes SquirrelGo Kanji's www/data/kanji.js: SCRIPTS.kanji with the
kanji readings, radical and stroke count in one list, and the on'yomi groups.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

TRADITIONS = {"hanzi": "chinese", "kanji": "japanese", "hanja": "hangul"}  # also the order of uses
APP_KEYS = ["char", "roman", "info", "level", "on", "kun", "radical", "strokes", "grade", "frequency"]
GROUP_MIN = 3


def js(value):
    """Compact JSON for a script, with private-use characters (pIqaD) escaped so
    the file reads the same in any editor."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return re.sub("[-]", lambda m: f"\\u{ord(m.group()):04X}", text)


def comments(notes):
    return [f"// {l}" for n in notes for l in textwrap.wrap(n, 77)]


def prop(key):
    return f".{key}" if re.fullmatch(r"[A-Za-z_$][\w$]*", key) else f"[{json.dumps(key)}]"


def on_groups(chars):
    """Kanji that share an on'yomi, GROUP_MIN or more, biggest group first and
    otherwise in the order the readings first appear."""
    by = {}
    for ch, e in chars.items():
        if e.get("roman"):
            by.setdefault(e["roman"], []).append(ch)
    big = sorted((r for r, cs in by.items() if len(cs) >= GROUP_MIN), key=lambda r: -len(by[r]))
    return [{"reading": f"{r} ({r})", "note": f"{len(by[r])} total",
             "chars": [{"char": c, "roman": r} for c in by[r]]} for r in big]


def load(data):
    """(scripts by language, readings by tradition, shared table), each in file order."""
    scripts, readings = {}, {}
    for p in sorted((data / "languages").glob("*/characters/*.jsonl")):
        header, entries = lib.read(p)
        if header["schema"] == "cjk-readings@1":
            readings[header["tradition"]] = (header, {e["char"]: {k: v for k, v in e.items() if k != "char"} for e in entries})
        else:
            scripts.setdefault(p.parent.parent.name, []).append((header, entries))
    table = {}
    if (data / "cjk" / "characters.jsonl").is_file():
        header, entries = lib.read(data / "cjk" / "characters.jsonl")
        table = (header, {e["char"]: e for e in entries})
    return scripts, readings, table


def script_file(lang, tables, commit, command):
    lines = [f"// Generated from squirrel-lang-data {commit} languages/{lang}/characters/ by: {command}",
             "window.SCRIPTS = window.SCRIPTS || {};"]
    for header, entries in tables:
        rows, last = [], None
        for e in entries:
            if e.get("group") and e["group"] != last:
                rows.append(f"    // {e['group']}")
            last = e.get("group")
            rows.append("    " + js({k: v for k, v in e.items() if k != "group"}) + ",")
        if rows and not rows[-1].lstrip().startswith("//"):
            rows[-1] = rows[-1][:-1]
        lines += [""] + comments(header.get("notes", []))
        lines += [f"window.SCRIPTS{prop(header['script'])} = {{",
                  f"  \"name\": {js(header['name'])},", "  \"chars\": ["] + rows + ["  ]", "};"]
    return "\n".join(lines) + "\n"


def table_file(table, readings, commit, command):
    header, chars = table
    lines = [f"// Generated from squirrel-lang-data {commit} cjk/characters.jsonl by: {command}"]
    lines += comments(["The shared CJK table, keyed by character. uses lists every tradition the character "
                       "belongs to: hanzi (Chinese), kanji (Japanese), hanja (Korean). Readings and meanings "
                       "are in japanese/kanji.js, chinese/hanzi.js and hangul/hanja.js."] + header.get("notes", []))
    rows = []
    for ch, e in chars.items():
        uses = [t for t in TRADITIONS if ch in readings.get(t, (None, {}))[1]]
        rows.append(f"  {js(ch)}: {js({'uses': uses, 'radical': e['radical'], 'strokes': e['strokes']})}")
    return "\n".join(lines) + "\nwindow.LSD_CJK = {\n" + ",\n".join(rows) + "\n};\n"


def readings_file(tradition, header, chars, commit, command):
    lang = TRADITIONS[tradition]
    lines = [f"// Generated from squirrel-lang-data {commit} languages/{lang}/characters/{tradition}.jsonl by: {command}"]
    lines += comments(header.get("notes", []))
    body = ",\n".join(f"    {js(ch)}: {js(e)}" for ch, e in chars.items())
    out = f"{{\n  \"name\": {js(header['name'])},\n  \"chars\": {{\n{body}\n  }}"
    if tradition == "kanji":
        out += ",\n  \"groups\": [\n" + ",\n".join("    " + js(g) for g in on_groups(chars)) + "\n  ]"
    return ("\n".join(lines) + "\nwindow.LSD_CJK_READINGS = window.LSD_CJK_READINGS || {};\n"
            + f"window.LSD_CJK_READINGS.{tradition} = {out}\n}};\n")


def kanji_app_file(readings, table, commit, command):
    header, chars = readings["kanji"]
    shared = table[1]
    lines = [f"// Generated from squirrel-lang-data {commit} languages/japanese/characters/kanji.jsonl"
             f" and cjk/characters.jsonl by: {command}"]
    lines += comments(header.get("notes", []))
    rows = []
    for ch, e in chars.items():
        full = dict(e, char=ch, radical=shared[ch]["radical"], strokes=str(shared[ch]["strokes"]))
        rows.append("    " + js({k: full[k] for k in APP_KEYS if k in full}))
    groups = ",\n".join("    " + js(g) for g in on_groups(chars))
    return ("\n".join(lines) + "\nif (typeof SCRIPTS === 'undefined') SCRIPTS = {};\nSCRIPTS.kanji = {\n"
            + f"  \"name\": {js(header['name'])},\n  \"chars\": [\n" + ",\n".join(rows)
            + f"\n  ],\n  \"groups\": [\n{groups}\n  ]\n}};\n")


def build(data, command):
    commit = lib.data_commit(data)
    scripts, readings, table = load(data)
    files = {f"{lang}/characters.js": script_file(lang, tables, commit, command) for lang, tables in scripts.items()}
    if table:
        files["cjk/characters.js"] = table_file(table, readings, commit, command)
    for tradition, (header, chars) in readings.items():
        files[f"{TRADITIONS[tradition]}/{tradition}.js"] = readings_file(tradition, header, chars, commit, command)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, help="the consumer's languages/ folder")
    ap.add_argument("--kanji-app", type=Path, help="SquirrelGo Kanji's www/data/kanji.js")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    if not args.out and not args.kanji_app:
        ap.error("give --out, --kanji-app or both")
    status = 0
    if args.out:
        command = f"python3 data/tools/gen_characters.py --out {args.out.name}"
        status |= lib.write_outputs(build(args.data, command), args.out, args.check, command)
    if args.kanji_app:
        command = "python3 data/tools/gen_characters.py --kanji-app www/data/kanji.js"
        _, readings, table = load(args.data)
        text = kanji_app_file(readings, table, lib.data_commit(args.data), command)
        status |= lib.write_outputs({args.kanji_app.name: text}, args.kanji_app.parent, args.check, command)
    return status


if __name__ == "__main__":
    sys.exit(main())
