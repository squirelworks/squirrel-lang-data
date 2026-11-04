#!/usr/bin/env python3
"""Every content file names a schema in schemas/ and follows it.

    python3 tools/check_schema.py

A JSON file is checked as a whole. A JSONL file's header line is checked
against the schema's "header" property and every later line against its
"entry" property.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402
import schema as js  # noqa: E402


def check_file(path, root=lib.ROOT):
    rel = path.relative_to(root)
    try:
        data = lib.read(path)
    except ValueError as e:
        return [f"{rel}: does not parse ({e})"]
    head = data[0] if path.suffix == ".jsonl" else data
    if not isinstance(head, dict) or not head.get("schema"):
        return [f"{rel}: no \"schema\" field"]
    name = lib.schema_name(head)
    try:
        schema = lib.load_schema(name, root)
    except OSError:
        return [f"{rel}: schema {head['schema']} has no schemas/{name}"]
    if path.suffix == ".jsonl":
        props = schema.get("properties", {})
        if "header" not in props or "entry" not in props:
            return [f"{rel}: schemas/{name} is not a JSONL schema (needs header and entry)"]
        problems = [f"{rel}:1: {e}" for e in js.errors(head, props["header"], schema)]
        for n, entry in enumerate(data[1], start=2):
            problems += [f"{rel}:{n}: {e}" for e in js.errors(entry, props["entry"], schema)]
        return problems
    return [f"{rel}: {e}" for e in js.errors(data, schema)]


def check_schemas(root=lib.ROOT):
    """Each schema file is named <type>.v<N>.json and only uses supported keywords."""
    import json
    import re
    problems = []
    for p in sorted((root / "schemas").glob("*")):
        if p.name.startswith("."):
            continue
        if not re.fullmatch(r"[a-z][a-z0-9-]*\.v[0-9]+\.json", p.name):
            problems.append(f"schemas/{p.name}: name should be <type>.v<N>.json")
            continue
        try:
            unknown = js.unknown_keywords(json.loads(p.read_text(encoding="utf-8")))
        except ValueError as e:
            problems.append(f"schemas/{p.name}: does not parse ({e})")
            continue
        if unknown:
            problems.append(f"schemas/{p.name}: keywords tools/schema.py doesn't support: {', '.join(unknown)}")
    return problems


def main():
    problems = check_schemas()
    files = list(lib.content_files())
    for p in files:
        problems += check_file(p)
    print("\n".join(problems) or f"schema: {len(files)} files OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
