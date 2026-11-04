#!/usr/bin/env python3
"""Checks on the meaning matrix that a schema can't express.

    python3 tools/check_meaning.py

- meaning/meanings.jsonl: ids are unique.
- meaning/sentences.jsonl: ids are unique, every pack is listed in the header
  and used, and every meaning a sentence lists is a content meaning.
- meaning/phrasings.jsonl: m and with are content meanings, and m isn't in with.
- meaning/columns/<language>.jsonl: the header's language is the file's name
  and a folder in languages/; every line renders a sentence that exists, once;
  every token is exactly [text, reading, meanings] with known meanings; and the
  rendering carries exactly the sentence's content meanings, counting implied
  ones, no more and no fewer.

It also reports content meanings no sentence uses and sentences no column
renders yet. That is information only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def load(path, rel, problems):
    try:
        return lib.read(path)
    except ValueError as e:
        problems.append(f"{rel}: does not parse ({e})")
        return {}, []


def check(root=lib.ROOT):
    problems, info = [], []
    base = root / "meaning"
    if not (base / "meanings.jsonl").is_file():
        return problems, info
    _, meanings = load(base / "meanings.jsonl", "meaning/meanings.jsonl", problems)
    kinds = {}
    for n, e in enumerate(meanings, start=2):
        if e.get("id") in kinds:
            problems.append(f"meaning/meanings.jsonl:{n}: id {e.get('id')!r} is used twice")
        kinds[e.get("id")] = e.get("kind")
    content = {k for k, v in kinds.items() if v == "content"}

    rows = {}
    used = set()
    if (base / "sentences.jsonl").is_file():
        header, sentences = load(base / "sentences.jsonl", "meaning/sentences.jsonl", problems)
        packs = [p.get("id") for p in header.get("packs", [])]
        seen_packs = set()
        for n, s in enumerate(sentences, start=2):
            where = f"meaning/sentences.jsonl:{n}"
            if s.get("id") in rows:
                problems.append(f"{where}: id {s.get('id')!r} is used twice")
            rows[s.get("id")] = s
            if s.get("pack") not in packs:
                problems.append(f"{where}: pack {s.get('pack')!r} is not listed in the header")
            seen_packs.add(s.get("pack"))
            for m in s.get("m", []):
                if m not in content:
                    problems.append(f"{where}: {m!r} is not a content meaning in meanings.jsonl")
                used.add(m)
        for p in packs:
            if p not in seen_packs:
                problems.append(f"meaning/sentences.jsonl:1: pack {p!r} has no sentences")

    if (base / "phrasings.jsonl").is_file():
        _, phrasings = load(base / "phrasings.jsonl", "meaning/phrasings.jsonl", problems)
        for n, p in enumerate(phrasings, start=2):
            where = f"meaning/phrasings.jsonl:{n}"
            for m in [p.get("m")] + p.get("with", []):
                if m not in content:
                    problems.append(f"{where}: {m!r} is not a content meaning in meanings.jsonl")
            if p.get("m") in p.get("with", []):
                problems.append(f"{where}: {p.get('m')!r} can't be in its own with list")

    rendered = set()
    for path in sorted((base / "columns").glob("*.jsonl")):
        rel = path.relative_to(root)
        header, lines = load(path, rel, problems)
        lang = path.stem
        if header.get("language") != lang:
            problems.append(f"{rel}:1: language {header.get('language')!r} should be {lang!r}")
        if not (root / "languages" / lang).is_dir():
            problems.append(f"{rel}:1: there is no languages/{lang}/")
        seen = set()
        for n, r in enumerate(lines, start=2):
            where = f"{rel}:{n}"
            sid = r.get("sentence")
            if sid in seen:
                problems.append(f"{where}: sentence {sid!r} is rendered twice")
            seen.add(sid)
            row = rows.get(sid)
            if row is None:
                problems.append(f"{where}: sentence {sid!r} is not in sentences.jsonl")
                continue
            rendered.add(sid)
            carried = []
            for t in r.get("t", []):
                if len(t) != 3:
                    problems.append(f"{where}: token {t!r} should be [text, reading, meanings]")
                    continue
                for m in t[2].split("+"):
                    if m not in kinds:
                        problems.append(f"{where}: token {t[0]!r} has unknown meaning {m!r}")
                    elif kinds[m] == "content":
                        carried.append(m)
            for m in r.get("implied", []):
                if m not in content:
                    problems.append(f"{where}: implied {m!r} is not a content meaning")
                carried.append(m)
            missing = [m for m in row.get("m", []) if m not in carried]
            extra = [m for m in carried if m not in row.get("m", [])]
            if missing:
                problems.append(f"{where}: {sid} drops {', '.join(missing)}")
            if extra:
                problems.append(f"{where}: {sid} adds {', '.join(extra)}")

    unused = sorted(content - used)
    if unused:
        info.append(f"meaning: {len(unused)} content meanings no sentence uses yet")
    unrendered = sorted(set(rows) - rendered)
    if unrendered:
        info.append(f"meaning: sentences no column renders yet: {', '.join(unrendered)}")
    return problems, info


def main():
    problems, info = check()
    print("\n".join(problems) or "meaning: OK")
    for line in info:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
