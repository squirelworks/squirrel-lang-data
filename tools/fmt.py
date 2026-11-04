#!/usr/bin/env python3
"""Format every content file the same way, so diffs only show real changes.

    python3 tools/fmt.py           # rewrite files in place
    python3 tools/fmt.py --check   # list unformatted files, exit 1 if any

JSON: two-space indent, keys in the order the schema lists them (unknown keys
after, in their own order), UTF-8 without escapes, one trailing newline. A
list of plain values (strings, numbers) that fits in 80 columns stays on one
line.
JSONL: one compact object per line, header first, keys ordered the same way
(by the header's schema for every line, using the schema's `entry` properties
when it has them).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def ordered(obj, props):
    """obj with its keys in schema order, recursing into known sub-schemas."""
    if not isinstance(obj, dict):
        return obj
    names = list(props or {})
    keys = [k for k in names if k in obj] + [k for k in obj if k not in names]
    out = {}
    for k in keys:
        sub = (props or {}).get(k, {})
        v = obj[k]
        if isinstance(v, dict):
            v = ordered(v, sub.get("properties"))
        elif isinstance(v, list) and isinstance(sub.get("items"), dict):
            v = [ordered(i, sub["items"].get("properties")) for i in v]
        out[k] = v
    return out


WIDTH = 80


def dumps(value, indent=0):
    """json.dumps(indent=2), except short lists of plain values stay on one line."""
    pad = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = [f"{pad}{json.dumps(k, ensure_ascii=False)}: {dumps(v, indent + 1)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + "  " * indent + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if not any(isinstance(v, (dict, list)) for v in value):
            flat = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
            if len(pad) + len(flat) <= WIDTH:
                return flat
        return "[\n" + ",\n".join(pad + dumps(v, indent + 1) for v in value) + "\n" + "  " * indent + "]"
    return json.dumps(value, ensure_ascii=False)


def format_file(path, root=lib.ROOT):
    data = lib.read(path)
    head = data[0] if path.suffix == ".jsonl" else data
    try:
        schema = lib.load_schema(lib.schema_name(head), root)
    except (OSError, ValueError):
        schema = {}
    if path.suffix == ".jsonl":
        header, entries = data
        hprops = schema.get("properties", {}).get("header", {}).get("properties", schema.get("properties"))
        eprops = schema.get("properties", {}).get("entry", {}).get("properties")
        lines = [ordered(header, hprops)] + [ordered(e, eprops) for e in entries]
        return "".join(json.dumps(l, ensure_ascii=False, separators=(", ", ": ")) + "\n" for l in lines)
    return dumps(ordered(data, schema.get("properties"))) + "\n"


def main(argv):
    check = "--check" in argv
    bad = []
    for p in lib.content_files():
        try:
            text = format_file(p)
        except ValueError as e:
            print(f"{p.relative_to(lib.ROOT)}: does not parse ({e})")
            bad.append(p)
            continue
        if p.read_text(encoding="utf-8") != text:
            bad.append(p)
            if not check:
                p.write_text(text, encoding="utf-8")
    for p in bad:
        print(("unformatted: " if check else "formatted: ") + str(p.relative_to(lib.ROOT)))
    if check and bad:
        print("run python3 tools/fmt.py")
    return 1 if check and bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
