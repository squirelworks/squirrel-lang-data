#!/usr/bin/env python3
"""Generate LanguageStudentDesk's reference.json cards from languages/*/reference.json.

    python3 data/tools/gen_reference.py --out languages            # write
    python3 data/tools/gen_reference.py --out languages --check    # exit 1 if stale

Writes --out/<id>/reference.json for each language with cards, in the shape the
Reference Learner reads: {"id": <language>, "entries": [...]}.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def desk_shape(ref):
    return {"id": ref["language"], "entries": ref["entries"]}


def build(data):
    return {f"{p.parent.name}/reference.json": json.dumps(desk_shape(lib.read(p)), ensure_ascii=False, indent=2) + "\n"
            for p in sorted((data / "languages").glob("*/reference.json"))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the consumer's languages/ folder")
    ap.add_argument("--data", type=Path, default=lib.ROOT, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_reference.py --out {args.out.name}"
    return lib.write_outputs(build(args.data), args.out, args.check, command)


if __name__ == "__main__":
    sys.exit(main())
