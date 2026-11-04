#!/usr/bin/env python3
"""Convert LanguageStudentDesk's Translation Learner meaning matrix to
meaning@1, sentences@1, phrasings@1 and columns@1.

    python3 tools/migrate/lsd_meaning.py <LanguageStudentDesk checkout>

Needs node, since the matrix and columns are JavaScript literals. Reads
translation-learner/data/matrix.js and data/<language>.js and writes
meaning/meanings.jsonl, sentences.jsonl, phrasings.jsonl and
columns/<language>.jsonl here. The // group comments in TL_MEANINGS become each
meaning's group, the comment above a phrasing becomes its note, and the comment
at the top of a column file becomes the column's notes. Run tools/fmt.py
afterwards.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP = {"matrix.js", "network.js", "tested.js"}

DUMP = r"""
const fs = require("fs");
global.window = global;
for (const f of process.argv.slice(1)) eval(fs.readFileSync(f, "utf8"));
process.stdout.write(JSON.stringify({
  meanings: window.TL_MEANINGS, packs: window.TL_PACK_TITLES, sentences: window.TL_SENTENCES,
  phrasings: window.TL_PHRASINGS || [], langs: window.TL_LANGS || {},
}));
"""


def node(files):
    out = subprocess.run(["node", "-e", DUMP, *map(str, files)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def block(text, name):
    """The source lines of `window.<name> = ...;` up to its closing line."""
    start = text.index(f"window.{name} =")
    end = text.index("\n}", start) if name == "TL_MEANINGS" else text.index("\n];", start)
    return text[start:end].splitlines()


def groups(text):
    """meaning id -> the // comment it sits under in TL_MEANINGS."""
    out, current = {}, None
    for line in block(text, "TL_MEANINGS")[1:]:
        s = line.strip()
        if s.startswith("//"):
            current = s[2:].strip()
            continue
        m = re.match(r'^(?:"([^"]+)"|([A-Za-z0-9_-]+))\s*:', s)
        if m:
            key = m.group(1) or m.group(2)
            if key.startswith("@"):
                out[key] = "Grammar"
            elif current:
                out[key] = current
    return out


def phrasing_notes(text):
    """The // comment right above each phrasing line, in order."""
    notes, pending = [], None
    for line in block(text, "TL_PHRASINGS")[1:]:
        s = line.strip()
        if s.startswith("//"):
            pending = s[2:].strip()
        elif s.startswith("{"):
            notes.append(pending)
            pending = None
    return notes


def lead_comment(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[2:].strip())
    # The matrix moves with the columns, so the pointer to matrix.js goes.
    body = " ".join(lines).replace(" (matrix.js)", "").strip()
    return [body] if body else []


def meaning_entry(mid, raw, group):
    g = re.match(r"^\((.*?)\)(.*)$", raw)
    if g:
        e = {"id": mid, "kind": "grammar", "label": g.group(1), "en": [a for a in g.group(2).split("|") if a]}
    else:
        e = {"id": mid, "kind": "content", "en": [a for a in raw.split("|") if a]}
    if group:
        e["group"] = group
    return e


def convert(data, matrix_text, column_texts):
    gr = groups(matrix_text)
    meanings = [{"schema": "meaning@1", "notes": ["Written for this project."]}]
    meanings += [meaning_entry(k, v, gr.get(k)) for k, v in data["meanings"].items()]
    sentences = [{"schema": "sentences@1", "notes": ["Written for this project."],
                  "packs": [{"id": k, "title": v} for k, v in data["packs"].items()]}]
    for s in data["sentences"]:
        e = {"id": s["id"], "pack": s["pack"], "en": s["en"]}
        if s.get("also"):
            e["also"] = s["also"]
        e["m"] = s["m"]
        sentences.append(e)
    phrasings = [{"schema": "phrasings@1", "notes": ["Written for this project."]}]
    notes = phrasing_notes(matrix_text) if "TL_PHRASINGS" in matrix_text else []
    for i, p in enumerate(data["phrasings"]):
        e = {"m": p["m"], "with": p["with"]}
        if p.get("optional"):
            e["optional"] = True
        else:
            e["en"] = p["en"].split("|")
        if i < len(notes) and notes[i]:
            e["note"] = notes[i]
        phrasings.append(e)
    columns = {}
    for lang, col in data["langs"].items():
        header = {"schema": "columns@1", "language": lang}
        n = lead_comment(column_texts.get(lang, ""))
        if n:
            header["notes"] = n
        header["sep"] = col["sep"]
        if col.get("caseSensitive"):
            header["caseSensitive"] = True
        rows = [header]
        for sid, r in col["r"].items():
            e = {"sentence": sid, "t": r["t"]}
            if r.get("implied"):
                e["implied"] = r["implied"]
            if "end" in r:
                e["end"] = r["end"]
            rows.append(e)
        columns[lang] = rows
    return meanings, sentences, phrasings, columns


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "translation-learner" / "data"
    cols = sorted(p for p in src.glob("*.js") if p.name not in SKIP)
    data = node([src / "matrix.js", *cols])
    texts = {p.stem: p.read_text(encoding="utf-8") for p in cols}
    meanings, sentences, phrasings, columns = convert(data, (src / "matrix.js").read_text(encoding="utf-8"), texts)
    out = ROOT / "meaning"
    write(out / "meanings.jsonl", meanings)
    write(out / "sentences.jsonl", sentences)
    write(out / "phrasings.jsonl", phrasings)
    for lang, rows in columns.items():
        write(out / "columns" / f"{lang}.jsonl", rows)
    print(f"wrote {len(meanings) - 1} meanings, {len(sentences) - 1} sentences, {len(phrasings) - 1} phrasings, {len(columns)} columns")


if __name__ == "__main__":
    main()
