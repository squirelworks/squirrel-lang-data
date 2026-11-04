#!/usr/bin/env python3
"""Generate LanguageStudentDesk's Translation Learner matrix and columns from
meaning/.

    python3 data/tools/gen_meaning.py --out translation-learner/data            # write
    python3 data/tools/gen_meaning.py --out translation-learner/data --check    # exit 1 if stale

Writes --out/matrix.js (window.TL_MEANINGS, TL_PACK_TITLES, TL_SENTENCES and
TL_PHRASINGS) and --out/<language>.js for each column (window.TL_LANGS.<id>),
as classic scripts. A meaning's English is joined with "|", and a grammar
meaning is written "(label)English", the form the Translation Learner reads.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def js(value):
    return json.dumps(value, ensure_ascii=False)


def comment(notes):
    out = []
    for note in notes:
        out += ["// " + l for l in textwrap.wrap(note, 77)]
    return out


def meaning_value(e):
    alts = "|".join(e.get("en", []))
    return f"({e['label']}){alts}" if e["kind"] == "grammar" else alts


def matrix(data, commit, command):
    _, meanings = lib.read(data / "meaning" / "meanings.jsonl")
    sheader, sentences = lib.read(data / "meaning" / "sentences.jsonl")
    pfile = data / "meaning" / "phrasings.jsonl"
    phrasings = lib.read(pfile)[1] if pfile.is_file() else []
    lines = [f"// Generated from squirrel-lang-data {commit} meaning/ by: {command}",
             "// The meaning matrix: TL_MEANINGS (id -> English that may carry it, \"|\"",
             "// between alternatives; \"(label)\" first for grammar), TL_PACK_TITLES,",
             "// TL_SENTENCES (the rows) and TL_PHRASINGS.",
             "window.TL_MEANINGS = {"]
    group = None
    for e in meanings:
        if e.get("group") and e["group"] != group:
            group = e["group"]
            lines.append(f"  // {group}")
        lines.append(f"  {js(e['id'])}: {js(meaning_value(e))},")
    lines += ["};", "", "window.TL_PACK_TITLES = {"]
    lines += [f"  {js(p['id'])}: {js(p['title'])}," for p in sheader["packs"]]
    lines += ["};", "", "window.TL_SENTENCES = ["]
    for s in sentences:
        row = {"id": s["id"], "pack": s["pack"], "en": s["en"], "m": s["m"]}
        if s.get("also"):
            row["also"] = s["also"]
        lines.append(f"  {js(row)},")
    lines += ["];", "", "window.TL_PHRASINGS = ["]
    for p in phrasings:
        if p.get("note"):
            lines.append(f"  // {p['note']}")
        row = {"m": p["m"], "with": p["with"]}
        if p.get("optional"):
            row["optional"] = True
        else:
            row["en"] = "|".join(p["en"])
        lines.append(f"  {js(row)},")
    lines.append("];")
    return "\n".join(lines) + "\n"


def column(path, commit, command):
    header, rows = lib.read(path)
    lang = header["language"]
    prop = f".{lang}" if re.fullmatch(r"[A-Za-z_$][\w$]*", lang) else f"[{js(lang)}]"
    lines = [f"// Generated from squirrel-lang-data {commit} meaning/columns/{lang}.jsonl by: {command}"]
    lines += comment(header.get("notes", []))
    lines += ["window.TL_LANGS = window.TL_LANGS || {};", f"window.TL_LANGS{prop} = {{", f"  sep: {js(header['sep'])},"]
    if header.get("caseSensitive"):
        lines.append("  caseSensitive: true,")
    lines.append("  r: {")
    for r in rows:
        body = {}
        if "end" in r:
            body["end"] = r["end"]
        if r.get("implied"):
            body["implied"] = r["implied"]
        body["t"] = r["t"]
        lines.append(f"    {js(r['sentence'])}: {js(body)},")
    lines += ["  },", "};"]
    return "\n".join(lines) + "\n"


def build(data, command):
    commit = lib.data_commit(data)
    files = {"matrix.js": matrix(data, commit, command)}
    for p in sorted((data / "meaning" / "columns").glob("*.jsonl")):
        files[f"{p.stem}.js"] = column(p, commit, command)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the Translation Learner's data/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = "python3 data/tools/gen_meaning.py --out translation-learner/data"
    return lib.write_outputs(build(args.data, command), args.out, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
