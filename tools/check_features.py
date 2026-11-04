#!/usr/bin/env python3
"""Check features.json against the rules in schemas/features.v1.json.

Standard library only, so it runs anywhere CI does.
Usage: python3 tools/check_features.py [path/to/features.json]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID = re.compile(r"^[a-z][a-z0-9-]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Words that mean a string is explaining how the app is built.
IMPL = re.compile(r"\.(json|js|py|html)\b|\?lang=|features\.json|squirrel-lang-data|/", re.I)


def check(data):
    errs = []
    top = {"schema", "levels", "defaultLevel", "features", "featured", "text"}
    if data.get("schema") != "features@1":
        errs.append('"schema" must be "features@1"')
    for k in top - data.keys():
        errs.append(f'missing "{k}"')
    for k in data.keys() - top:
        errs.append(f'unknown field "{k}"')

    def strings(where, obj, keys):
        for k in keys:
            v = obj.get(k)
            if not isinstance(v, str) or not v.strip():
                errs.append(f"{where}: \"{k}\" must be a non-empty string")
            elif k in ("label", "description") or where == "text":
                if IMPL.search(v):
                    errs.append(f"{where}: \"{k}\" reads like an implementation note: {v!r}")

    levels = data.get("levels") or []
    level_ids = []
    for i, lv in enumerate(levels):
        where = f"levels[{i}]"
        if not isinstance(lv, dict):
            errs.append(f"{where}: must be an object"); continue
        if not ID.match(str(lv.get("id", ""))):
            errs.append(f"{where}: bad id {lv.get('id')!r}")
        strings(where, lv, ("label", "description"))
        if set(lv) - {"id", "label", "description"}:
            errs.append(f"{where}: unknown fields {sorted(set(lv) - {'id', 'label', 'description'})}")
        level_ids.append(lv.get("id"))
    if len(set(level_ids)) != len(level_ids):
        errs.append("level ids must be unique")
    if data.get("defaultLevel") not in level_ids:
        errs.append(f"defaultLevel {data.get('defaultLevel')!r} is not a level")

    feats = data.get("features") or []
    ids = []
    for i, f in enumerate(feats):
        where = f"features[{i}]"
        if not isinstance(f, dict):
            errs.append(f"{where}: must be an object"); continue
        fid = f.get("id")
        where = f"feature {fid!r}"
        if not ID.match(str(fid or "")):
            errs.append(f"{where}: bad id")
        strings(where, f, ("label", "description"))
        if f.get("level") not in level_ids:
            errs.append(f"{where}: level {f.get('level')!r} is not a level")
        if not DATE.match(str(f.get("added", ""))):
            errs.append(f"{where}: \"added\" must be a YYYY-MM-DD date")
        extra = set(f) - {"id", "label", "description", "level", "added"}
        if extra:
            errs.append(f"{where}: unknown fields {sorted(extra)}")
        ids.append(fid)
    if len(set(ids)) != len(ids):
        errs.append("feature ids must be unique")
    if ids != sorted(ids, key=str):
        errs.append("features must be sorted by id")

    featured = data.get("featured")
    if not isinstance(featured, list) or not all(isinstance(x, str) and ID.match(x) for x in featured):
        errs.append('"featured" must be a list of language ids')
    elif len(set(featured)) != len(featured):
        errs.append('"featured" has duplicates')

    text = data.get("text")
    if not isinstance(text, dict):
        errs.append('"text" must be an object')
    else:
        strings("text", text, sorted({"notice", "welcomeTitle", "welcomeBody", "whatsInApp",
                                      "customize", "custom"} | set(text)))
    return errs


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "features.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"{path}: {e}"); return 1
    errs = check(data)
    for e in errs:
        print(f"{path.name}: {e}")
    if not errs:
        print(f"{path.name}: OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
