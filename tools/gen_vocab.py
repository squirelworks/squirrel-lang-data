#!/usr/bin/env python3
"""Generate LanguageStudentDesk's vocab.js decks from languages/*/vocab.jsonl.

    python3 data/tools/gen_vocab.py --out languages            # write
    python3 data/tools/gen_vocab.py --out languages --check    # exit 1 if stale

Writes --out/<id>/vocab.js for each language with vocabulary: a classic script
that sets window.LSD_DECKS[<id>] to its decks, each word as [word, reading,
English, note], or [word, English, note] when the language has no readings.
"""
import argparse
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def decks(header, entries):
    out = [{"id": d["id"], "title": d["title"], "words": []} for d in header["decks"]]
    by_id = {d["id"]: d for d in out}
    for e in entries:
        note = e.get("note", "")
        word = [e["word"], e["reading"], e["meaning"], note] if "reading" in e else [e["word"], e["meaning"], note]
        by_id[e["deck"]]["words"].append(word)
    return out


def script(lang, header, entries, commit, command):
    lines = [f"// Generated from squirrel-lang-data {commit} languages/{lang}/vocab.jsonl by: {command}"]
    for note in header.get("notes", []):
        lines += ["// " + l for l in textwrap.wrap(note, 77)]
    prop = f".{lang}" if re.fullmatch(r"[A-Za-z_$][\w$]*", lang) else f"[{json.dumps(lang)}]"
    body = []
    for d in decks(header, entries):
        words = ",\n".join("      " + json.dumps(w, ensure_ascii=False) for w in d["words"])
        body.append(f'  {{\n    "id": {json.dumps(d["id"])},\n    "title": {json.dumps(d["title"], ensure_ascii=False)},\n'
                    f'    "words": [\n{words}\n    ]\n  }}')
    return ("\n".join(lines) + "\n"
            + "window.LSD_DECKS = window.LSD_DECKS || {};\n"
            + f"window.LSD_DECKS{prop} = [\n" + ",\n".join(body) + "\n];\n")


def build(data, command):
    commit = lib.data_commit(data)
    files = {}
    for p in sorted((data / "languages").glob("*/vocab.jsonl")):
        header, entries = lib.read(p)
        files[f"{p.parent.name}/vocab.js"] = script(p.parent.name, header, entries, commit, command)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the consumer's languages/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_vocab.py --out {args.out.name}"
    return lib.write_outputs(build(args.data, command), args.out, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
