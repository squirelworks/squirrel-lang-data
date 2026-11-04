#!/usr/bin/env python3
"""Convert LanguageStudentDesk's character tables to characters@1, cjk@1 and
cjk-readings@1.

    python3 tools/migrate/lsd_characters.py <LanguageStudentDesk checkout>

Needs node, since the tables are JavaScript. Reads languages/*/characters.js
(window.SCRIPTS), languages/cjk/characters.js (window.LSD_CJK) and the three
reading files (window.LSD_CJK_READINGS), and writes:

    languages/<id>/characters/<script>.jsonl     one file per SCRIPTS key
    languages/<id>/characters/<tradition>.jsonl  kanji, hanzi, hanja readings
    cjk/characters.jsonl                         the shared table

A // comment line inside a chars list becomes the group of the characters
after it. The table's uses list isn't kept, because it follows from which
reading files list a character, and neither are the kanji on'yomi groups,
which follow from the readings. Run tools/fmt.py afterwards.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DUMP = r"""
const fs = require("fs");
global.window = global;
global.SCRIPTS = window.SCRIPTS = {};
for (const f of process.argv.slice(1)) eval(fs.readFileSync(f, "utf8"));
process.stdout.write(JSON.stringify({scripts: window.SCRIPTS, cjk: window.LSD_CJK, readings: window.LSD_CJK_READINGS}));
"""

TRADITIONS = {"kanji": "japanese", "hanzi": "chinese", "hanja": "hangul"}
READING_FILES = {"kanji": "japanese/kanji.js", "hanzi": "chinese/hanzi.js", "hanja": "hangul/hanja.js"}
READING_KEYS = ["roman", "info", "level", "on", "kun", "grade", "frequency", "pinyin", "hsk", "traditional", "hangul"]

# What the reading files' header comments say, as notes, with the sources
# spelled out (they were in languages/README.md).
READING_NOTES = {
    "kanji": ["The full Jōyō set, in frequency order, with on'yomi, kun'yomi, meaning (info), JLPT level, "
              "school grade and frequency rank.",
              "Moved from LanguageStudentDesk's Jōyō table, which SquirrelGo Kanji shares; that table doesn't record "
              "where its readings first came from."],
    "hanzi": ["Every character of HSK 3.0 levels 1 to 6, by level: hsk is the lowest level a word with the character "
              "appears at, from the word lists in complete-hsk-vocabulary.",
              "Pinyin (kMandarin), meaning (kDefinition) and traditional form (kTraditionalVariant) come from the "
              "Unihan database. Made by tools/importers/cjk_unihan.py."],
    "hanja": ["The 1,800 basic hanja for education, in hangul order: the kHangul readings the Unihan database marks E, "
              "with Unihan meanings. Made by tools/importers/cjk_unihan.py."],
}
TABLE_NOTES = ["Kanji keep the radicals and stroke counts of LanguageStudentDesk's Jōyō table. Characters that are "
               "not kanji take theirs from the Unihan database (kRSUnicode, kTotalStrokes), through "
               "tools/importers/cjk_unihan.py."]


def groups(text):
    """{script key: [group of each character, or None]}, from the // comments
    inside each SCRIPTS.<key> chars list."""
    out, key, group = {}, None, None
    for line in text.splitlines():
        m = re.match(r"\s*(?:window\.)?SCRIPTS\.(\w+)\s*=", line)
        if m:
            key, group = m.group(1), None
            out[key] = []
            continue
        s = line.strip()
        if key and s.startswith("//"):
            group = s[2:].strip()
        elif key and s.startswith("{ char"):
            out[key].append(group)
    return out


def script_notes(text):
    """{script key: [note]} from a '// <key> data — <note>' line."""
    return {m.group(1): [m.group(2)[0].upper() + m.group(2)[1:] + "."]
            for m in re.finditer(r"^// (\w+) data — (.+)$", text, re.M)}


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "languages"
    char_files = sorted(p for p in src.glob("*/characters.js") if p.parent.name != "cjk")
    files = char_files + [src / "cjk" / "characters.js"] + [src / f for f in READING_FILES.values()]
    data = json.loads(subprocess.run(["node", "-e", DUMP, *map(str, files)],
                                     capture_output=True, text=True, check=True).stdout)
    count = 0
    for p in char_files:
        lang, text = p.parent.name, p.read_text(encoding="utf-8")
        notes, grp = script_notes(text), groups(text)
        for key in grp:
            s = data["scripts"][key]
            header = {"schema": "characters@1", "language": lang, "script": key, "name": s["name"]}
            if notes.get(key):
                header["notes"] = notes[key]
            rows = [header]
            for c, g in zip(s["chars"], grp[key], strict=True):
                rows.append(dict(c, group=g) if g else c)
            write(ROOT / "languages" / lang / "characters" / f"{key}.jsonl", rows)
            count += len(rows) - 1
    for tradition, lang in TRADITIONS.items():
        r = data["readings"][tradition]
        rows = [{"schema": "cjk-readings@1", "language": lang, "tradition": tradition, "name": r["name"],
                 "notes": READING_NOTES[tradition]}]
        for ch, e in r["chars"].items():
            rows.append({"char": ch, **{k: e[k] for k in READING_KEYS if k in e}})
            unknown = set(e) - set(READING_KEYS)
            if unknown:
                sys.exit(f"{tradition} {ch}: fields this tool doesn't know: {sorted(unknown)}")
        write(ROOT / "languages" / lang / "characters" / f"{tradition}.jsonl", rows)
        count += len(rows) - 1
    rows = [{"schema": "cjk@1", "notes": TABLE_NOTES}]
    rows += [{"char": ch, "radical": e["radical"], "strokes": e["strokes"]} for ch, e in data["cjk"].items()]
    write(ROOT / "cjk" / "characters.jsonl", rows)
    print(f"wrote {count} characters and readings, and {len(rows) - 1} shared CJK characters")


if __name__ == "__main__":
    main()
