"""Shared helpers for the tools: finding content files, reading them, and the
schemas they name."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".github", "schemas", "tools", "cache"}


def content_files(root=ROOT):
    """Every .json and .jsonl content file under root, in a stable order."""
    for p in sorted([*root.rglob("*.json"), *root.rglob("*.jsonl")]):
        if not SKIP & set(p.relative_to(root).parts):
            yield p


def read(path):
    """A JSON file's object, or a JSONL file's (header, entries)."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        return (rows[0] if rows else {}), rows[1:]
    return json.loads(text)


def schema_name(data):
    """'meta@1' -> 'meta.v1.json'."""
    kind, _, ver = data.get("schema", "").partition("@")
    return f"{kind}.v{ver}.json"


def load_schema(name, root=ROOT):
    return json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
