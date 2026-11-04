#!/usr/bin/env python3
"""Checks on stroke files that a schema can't express.

    python3 tools/check_strokes.py

- The header's set is the file name, and no character is listed twice.
- Every stroke is SVG path data a browser draws to the end: it starts with M,
  uses only M L H V C S Q T Z, and gives each command a whole number of
  arguments. (An earlier kanji file lost minus signs that doubled as
  separators, and browsers silently stopped drawing there.)
- Every point stays inside the box, give or take a tenth of it.
- KanjiVG sets give one stroke-number label per stroke.
- Characters in the shared CJK table (cjk/characters.jsonl) have the number of
  strokes it gives, except the differences listed in KNOWN_COUNTS.

The rendered check, that the finished strokes cover the character as a font
draws it, needs fonts and numpy; LanguageStudentDesk runs it on the generated
files (SquirrelGo-Apps/tools/strokecheck).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "Z": 0}
TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[\s,]+|.")
# Stroke counts that differ from the shared table on purpose or pending review:
# {set: {char: why}}.
KNOWN_COUNTS = {}


def path_problem(d, box):
    """Why the path won't draw to the end or leaves the box, or None."""
    toks = [t for t in TOKEN.findall(d) if not re.fullmatch(r"[\s,]+", t)]
    if not toks or toks[0] not in "Mm":
        return "doesn't start with M"
    x = y = sx = sy = 0.0
    pts, i, cmd = [], 0, None
    while i < len(toks):
        t = toks[i]
        if re.fullmatch(r"[A-Za-z]", t):
            if t.upper() not in ARGS:
                return f"unsupported command {t}"
            cmd, i = t, i + 1
            if cmd in "Zz":
                x, y = sx, sy
                continue
        elif cmd is None or not re.fullmatch(r"[-+0-9.eE]+", t):
            return f"unexpected {t!r}"
        n = ARGS[cmd.upper()]
        nums = toks[i:i + n]
        if len(nums) < n or not all(re.fullmatch(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", v) for v in nums):
            return f"{cmd} needs {n} numbers"
        v = [float(a) for a in nums]
        i += n
        rel, c = cmd.islower(), cmd.upper()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if c == "H":
            x = ox + v[0]
        elif c == "V":
            y = (y if rel else 0.0) + v[0]
        else:
            for k in range(0, n, 2):
                pts.append((ox + v[k], oy + v[k + 1]))
            x, y = pts[-1]
        pts.append((x, y))
        if c == "M":
            sx, sy = x, y
            cmd = "l" if rel else "L"
    margin = box / 10
    if any(not (-margin <= px <= box + margin and -margin <= py <= box + margin) for px, py in pts):
        return f"leaves the {box} x {box} box"
    return None


def check(root=lib.ROOT):
    problems = []
    counts = {}
    table = root / "cjk" / "characters.jsonl"
    if table.is_file():
        counts = {e["char"]: e.get("strokes") for e in lib.read(table)[1]}
    for p in sorted((root / "strokes").glob("*.jsonl")):
        rel = p.relative_to(root)
        try:
            header, entries = lib.read(p)
        except ValueError as e:
            problems.append(f"{rel}: does not parse ({e})")
            continue
        name = header.get("set")
        if name != p.stem:
            problems.append(f"{rel}:1: set {name!r} should be {p.stem!r}, the file name")
        box = header.get("box", 100)
        known = KNOWN_COUNTS.get(p.stem, {})
        seen = set()
        for n, e in enumerate(entries, start=2):
            ch, strokes = e.get("char"), e.get("strokes", [])
            if ch in seen:
                problems.append(f"{rel}:{n}: {ch} is listed twice")
            seen.add(ch)
            for k, d in enumerate(strokes, start=1):
                why = path_problem(d, box) if isinstance(d, str) else "not a string"
                if why:
                    problems.append(f"{rel}:{n}: {ch} stroke {k} {why}")
            if box == 109 and len(e.get("labels", [])) != len(strokes):
                problems.append(f"{rel}:{n}: {ch} has {len(strokes)} strokes but {len(e.get('labels', []))} labels")
            want = counts.get(ch)
            if want and want != len(strokes) and ch not in known:
                problems.append(f"{rel}:{n}: {ch} has {len(strokes)} strokes; cjk/characters.jsonl says {want}")
        have = {e.get("char"): len(e.get("strokes", [])) for e in entries}
        for ch in known:
            if ch in have and counts.get(ch) == have[ch]:
                problems.append(f"{rel}: KNOWN_COUNTS lists {ch}, which no longer differs; take it out")
    return problems


def main():
    problems = check()
    print("\n".join(problems) or "strokes: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
