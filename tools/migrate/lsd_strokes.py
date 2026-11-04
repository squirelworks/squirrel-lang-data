#!/usr/bin/env python3
"""Convert the SquirrelGo apps' stroke files to strokes@1.

    python3 tools/migrate/lsd_strokes.py <LanguageStudentDesk checkout>

Needs node, since the stroke files are JavaScript. Reads every file
gen_strokes.py writes (its TARGETS, the first path of each set) and writes
strokes/<set>.jsonl. The comment at the top of each file becomes the header's
notes; the box, source and license come from SETS below. Run tools/fmt.py
afterwards.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gen_strokes  # noqa: E402

DUMP = r"""
const fs = require("fs");
global.window = global;
eval(fs.readFileSync(process.argv[1], "utf8"));
const v = process.argv[2] ? (window[process.argv[2]] || {})[process.argv[3]] || window[process.argv[2]] : null;
process.stdout.write(JSON.stringify(Object.entries(v)));
"""

OFL = ("Noto fonts", "SIL Open Font License 1.1")
KANJIVG = ("KanjiVG", "CC BY-SA 3.0")
SOURCES = {"kanji": KANJIVG, "kana": KANJIVG, "hiragana": KANJIVG, "katakana": KANJIVG,
           "klingon": ("Written for this project", "CC BY-SA 4.0"), "zhuyin": OFL}


def comment(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        lines.append(line[2:].strip())
    return [" ".join(lines)] if lines else []


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    apps = Path(sys.argv[1]) / "SquirrelGo-Apps"
    total = 0
    for name, (form, paths) in sorted(gen_strokes.targets(apps, gen_strokes.ALL).items()):
        src = paths[0]
        glob, key = {"keyed": ("SG_STROKES", name), "plain": ("SG_STROKES", ""), "kanji": ("KANJI_STROKES", ""),
                     "kana": ("KANA_STROKES", "")}[form]
        entries = json.loads(subprocess.run(["node", "-e", DUMP, str(src), glob, key], capture_output=True,
                                            text=True, check=True).stdout)
        # JavaScript lists keys that look like numbers (Klingon's numerals) first;
        # keep the file's own order instead.
        text = src.read_text(encoding="utf-8")
        if form in ("keyed", "plain"):
            order = [json.loads(m) for m in re.findall(r'^  ("(?:[^"\\]|\\.)*"):', text, re.M)]
            by = dict(entries)
            assert sorted(order) == sorted(by), src
            entries = [(k, by[k]) for k in order]
        source, license_ = SOURCES.get(name, OFL)
        header = {"schema": "strokes@1", "set": name, "box": 109 if form in ("kanji", "kana") else 100,
                  "notes": comment(src.read_text(encoding="utf-8")), "source": source, "license": license_}
        rows = [header]
        for ch, v in entries:
            rows.append({"char": ch, "strokes": v[0], "labels": v[1]} if form in ("kanji", "kana") else {"char": ch, "strokes": v})
        out = ROOT / "strokes" / f"{name}.jsonl"
        out.parent.mkdir(exist_ok=True)
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        total += len(rows) - 1
    print(f"wrote {total} characters' strokes")


if __name__ == "__main__":
    main()
