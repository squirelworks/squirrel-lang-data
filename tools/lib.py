"""Shared helpers for the tools: finding content files, reading them, and the
schemas they name."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".github", "schemas", "tools", "cache", "build"}


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


def data_commit(root=ROOT):
    """This checkout's short commit, for the header of generated files."""
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_outputs(files, out_dir, check, command):
    """Write {relative path: text} under out_dir, or with check, report files
    that differ. The first line of a .js file names the data commit, which
    changes with every bump, so --check compares the rest. Returns the exit
    status."""
    stale = []
    for rel, text in files.items():
        p = out_dir / rel
        old = p.read_text(encoding="utf-8") if p.is_file() else None
        if check:
            same = old is not None and (old.split("\n", 1)[1:] == text.split("\n", 1)[1:] if rel.endswith(".js") else old == text)
            if not same:
                stale.append(rel)
        elif old != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            print("wrote", p)
    for rel in stale:
        print(f"{out_dir / rel} differs from the data; run {command}")
    return 1 if stale else 0
