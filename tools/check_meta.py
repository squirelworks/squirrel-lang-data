#!/usr/bin/env python3
"""Checks on languages and varieties that a schema can't express.

    python3 tools/check_meta.py

- Every folder in languages/ has a meta.json (meta@1), and every folder in
  languages/<id>/varieties/ has one (variety@1).
- Each id matches its folder, and no id is used twice.
- A variety's parent is its language or another variety of that language, and
  following parents always ends at the language.
- A language with varieties lists them all, alphabetically, under "varieties",
  and lists nothing that isn't there.
- Every marker named under "markers" (besides "default") is a grammar meaning
  in meaning/meanings.jsonl.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def load(path, problems, root):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        problems.append(f"{path.relative_to(root)}: {e}")
        return None


def grammar_meanings(root):
    """Ids of the grammar meanings (kind "grammar") in meaning/meanings.jsonl."""
    path = root / "meaning" / "meanings.jsonl"
    if not path.is_file():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return {m["id"] for m in map(json.loads, filter(None, lines)) if m.get("kind") == "grammar"}


def check(root=lib.ROOT):
    problems = []
    langs = root / "languages"
    if not langs.is_dir():
        return problems
    seen = {}
    grammar = grammar_meanings(root)

    def claim(id_, rel):
        if id_ in seen:
            problems.append(f"{rel}: id {id_!r} is already used by {seen[id_]}")
        else:
            seen[id_] = rel

    for folder in sorted(p for p in langs.iterdir() if p.is_dir()):
        meta_path = folder / "meta.json"
        rel = meta_path.relative_to(root)
        if not meta_path.is_file():
            problems.append(f"{folder.relative_to(root)}/: no meta.json")
            continue
        meta = load(meta_path, problems, root)
        if not isinstance(meta, dict):
            continue
        if meta.get("schema") != "meta@1":
            problems.append(f"{rel}: should name schema meta@1")
        if meta.get("id") != folder.name:
            problems.append(f"{rel}: id {meta.get('id')!r} should be {folder.name!r}, its folder's name")
        claim(meta.get("id"), str(rel))
        for marker in sorted(set(meta.get("markers") or {}) - {"default"}):
            if marker not in grammar:
                problems.append(f"{rel}: markers names {marker!r}, which isn't a grammar meaning in meaning/meanings.jsonl")

        vdir = folder / "varieties"
        found = sorted(p.name for p in vdir.iterdir() if p.is_dir()) if vdir.is_dir() else []
        listed = meta.get("varieties", [])
        if listed != sorted(listed):
            problems.append(f"{rel}: varieties should be alphabetical")
        for v in sorted(set(found) - set(listed)):
            problems.append(f"{rel}: varieties/{v}/ is not listed under varieties")
        for v in sorted(set(listed) - set(found)):
            problems.append(f"{rel}: lists variety {v!r} but varieties/{v}/ doesn't exist")

        parents = {}
        for v in found:
            vpath = vdir / v / "meta.json"
            vrel = vpath.relative_to(root)
            if not vpath.is_file():
                problems.append(f"{vdir.relative_to(root)}/{v}/: no meta.json")
                continue
            var = load(vpath, problems, root)
            if not isinstance(var, dict):
                continue
            if var.get("schema") != "variety@1":
                problems.append(f"{vrel}: should name schema variety@1")
            if var.get("id") != v:
                problems.append(f"{vrel}: id {var.get('id')!r} should be {v!r}, its folder's name")
            claim(var.get("id"), str(vrel))
            parents[v] = (var.get("parent"), vrel)

        for v, (parent, vrel) in parents.items():
            if parent != folder.name and parent not in parents:
                problems.append(f"{vrel}: parent {parent!r} should be {folder.name!r} or another of its varieties")
                continue
            chain, cur = [v], parent
            while cur != folder.name and cur in parents:
                if cur in chain:
                    problems.append(f"{vrel}: parents loop ({' -> '.join(chain + [cur])})")
                    break
                chain.append(cur)
                cur = parents[cur][0]
    return problems


def main():
    problems = check()
    print("\n".join(problems) or "meta: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
