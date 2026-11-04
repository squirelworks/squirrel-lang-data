#!/usr/bin/env python3
"""Convert LanguageStudentDesk's languages/<id>/vocab.js decks to vocab@1.

    python3 tools/migrate/lsd_vocab.py <LanguageStudentDesk checkout>

Needs node, since the decks are JavaScript literals. Writes
languages/<id>/vocab.jsonl here. A word [word, reading, English, note] keeps
its reading; [word, English, note] (languages without a separate reading) has
none. Empty notes are left out. The comment lines at the top of each file
become the header's notes. Run tools/fmt.py afterwards.
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
process.stdout.write(JSON.stringify(window.LSD_DECKS[id]));
"""


def comment_notes(text):
    """The leading // comment, minus its first line (which names the file), as sentences."""
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[2:].strip())
    body = " ".join(lines[1:]).strip()
    return [body] if body else []


def convert(lang, decks, notes):
    header = {"schema": "vocab@1", "language": lang}
    if notes:
        header["notes"] = notes
    header["decks"] = [{"id": d["id"], "title": d["title"]} for d in decks]
    rows = [header]
    for d in decks:
        for w in d["words"]:
            if len(w) >= 4:
                word, reading, meaning, note = w[0], w[1], w[2], w[3]
            else:
                word, reading, meaning, note = w[0], None, w[1], (w[2] if len(w) > 2 else "")
            e = {"id": f"{d['id']}/{word}", "deck": d["id"], "word": word}
            if reading is not None:
                e["reading"] = reading
            e["meaning"] = meaning
            if note:
                e["note"] = note
            rows.append(e)
    return rows


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "languages"
    count = 0
    for p in sorted(src.glob("*/vocab.js")):
        lang = p.parent.name
        decks = json.loads(subprocess.run(["node", "-e", DUMP, str(p)], capture_output=True, text=True, check=True).stdout)
        rows = convert(lang, decks, comment_notes(p.read_text(encoding="utf-8")))
        out = ROOT / "languages" / lang / "vocab.jsonl"
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        count += len(rows) - 1
    print(f"wrote {count} words")


if __name__ == "__main__":
    main()
