#!/usr/bin/env python3
"""Export each language's content as a pack other programs can open.

    python3 tools/export.py                        # every language, every format
    python3 tools/export.py japanese latin         # just these languages
    python3 tools/export.py --format folder        # just this format
    python3 tools/export.py --out ~/packs          # somewhere else (default build/packs/)
    python3 tools/export.py --list                 # languages and formats

Each format writes one pack per language into the output folder. Re-running
replaces the packs it writes. The output is build output: it's ignored by git
and never committed. See tools/packs/ for the formats.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402
import packs  # noqa: E402

DEFAULT_OUT = lib.ROOT / "build" / "packs"


def export(langs, formats, out_dir, root=lib.ROOT, quiet=False):
    """Write every pack; returns the paths written."""
    written = []
    for lang in langs:
        pack = packs.load(lang, root)
        for name in formats:
            path = packs.FORMATS[name].write(pack, out_dir)
            written.append(path)
            if not quiet:
                print(f"{name}: {path}")
    return written


def main(argv):
    ap = argparse.ArgumentParser(description="Export language packs.")
    ap.add_argument("languages", nargs="*", help="language ids (default: every language)")
    ap.add_argument("--format", action="append", choices=sorted(packs.FORMATS),
                    help="a format to write; repeat for several (default: every format)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default: build/packs/)")
    ap.add_argument("--list", action="store_true", help="list languages and formats, then stop")
    args = ap.parse_args(argv)
    known = packs.languages()
    if args.list:
        print("formats:", ", ".join(sorted(packs.FORMATS)))
        print("languages:", ", ".join(known))
        return 0
    unknown = [l for l in args.languages if l not in known]
    if unknown:
        print("unknown language:", ", ".join(unknown), "(see --list)")
        return 2
    export(args.languages or known, args.format or sorted(packs.FORMATS), args.out.expanduser())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
