#!/usr/bin/env python3
"""Exports every language in every format into a temporary folder and checks
the packs. Nothing is kept or uploaded.

    python3 tools/check_export.py

- Every format writes a pack for every language without an error.
- Every content file in a language folder (and its varieties) is in the pack,
  byte for byte, so no content type is dropped.
- Each format's own check passes (for the folder format: every file the
  manifest lists exists, nothing else does, and the split files add up to the
  words and lessons in the source).
- Exporting twice gives identical packs.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export  # noqa: E402
import lib  # noqa: E402
import packs  # noqa: E402


def _tree(path):
    if path.is_file():
        return {"": path.read_bytes()}
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def check(root=lib.ROOT):
    problems = []
    langs = packs.languages(root)
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        for lang in langs:
            try:
                pack = packs.load(lang, root)
            except Exception as e:  # report every language, not just the first
                problems.append(f"{lang}: can't be read ({e})")
                continue
            for name, fmt in sorted(packs.FORMATS.items()):
                try:
                    first = fmt.write(pack, Path(a))
                    second = fmt.write(pack, Path(b))
                except Exception as e:
                    problems.append(f"{lang}: {name} export failed ({type(e).__name__}: {e})")
                    continue
                problems += [f"{lang}: {name}: {p}" for p in fmt.check(pack, first, root)]
                if first is None or second is None:
                    if first != second:
                        problems.append(f"{lang}: {name}: two exports of the same commit differ")
                elif _tree(first) != _tree(second):
                    problems.append(f"{lang}: {name}: two exports of the same commit differ")
    return problems, len(langs)


if __name__ == "__main__":
    problems, n = check()
    print("\n".join(problems) or f"export OK ({n} languages, formats: {', '.join(sorted(packs.FORMATS))})")
    sys.exit(1 if problems else 0)
