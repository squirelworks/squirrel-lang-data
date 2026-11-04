#!/usr/bin/env python3
"""Convert LanguageStudentDesk's languages/<id>/reference.json cards to reference@1.

    python3 tools/migrate/lsd_reference.py <LanguageStudentDesk checkout>

Writes languages/<id>/reference.json here: the same cards, with "schema"
added and the top-level "id" renamed "language". Run tools/fmt.py afterwards.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def convert(ref):
    return {"schema": "reference@1", "language": ref["id"], "entries": ref["entries"]}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    n = 0
    for p in sorted((Path(sys.argv[1]) / "languages").glob("*/reference.json")):
        out = convert(json.loads(p.read_text(encoding="utf-8")))
        (ROOT / "languages" / p.parent.name / "reference.json").write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8")
        n += len(out["entries"])
    print(f"wrote {n} cards")


if __name__ == "__main__":
    main()
