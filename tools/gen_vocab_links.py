#!/usr/bin/env python3
"""Generate LanguageStudentDesk's links between vocabulary and meaning units
from meaning/vocab-links/.

    python3 data/tools/gen_vocab_links.py --out translation-learner/data            # write
    python3 data/tools/gen_vocab_links.py --out translation-learner/data --check    # exit 1 if stale

Writes --out/vocab-links.js, a classic script setting
window.TL_VOCAB_LINKS = {language: {"<deck>/<word>": [meaning ids]}}, with
languages and words in file order. The Translation Learner, the Vocabulary
Learner and the meaning network can all read it, so they share one set of
meaning units.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def js(value):
    return json.dumps(value, ensure_ascii=False)


def build(data, command):
    commit = lib.data_commit(data)
    lines = [f"// Generated from squirrel-lang-data {commit} meaning/vocab-links/ by: {command}",
             "// Which meaning units (TL_MEANINGS ids) each vocabulary card carries, by",
             "// language and vocab id (\"<deck>/<word>\").",
             "window.TL_VOCAB_LINKS = {"]
    for p in sorted((data / "meaning" / "vocab-links").glob("*.jsonl")):
        header, entries = lib.read(p)
        lines.append(f"  {js(header['language'])}: {{")
        lines += [f"    {js(e['vocab'])}: {js(e['meanings'])}," for e in entries]
        lines.append("  },")
    lines.append("};")
    return {"vocab-links.js": "\n".join(lines) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the Translation Learner's data/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = "python3 data/tools/gen_vocab_links.py --out translation-learner/data"
    return lib.write_outputs(build(args.data, command), args.out, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
