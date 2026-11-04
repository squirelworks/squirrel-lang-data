#!/usr/bin/env python3
"""Checks on the links between vocabulary and meaning units that a schema
can't express.

    python3 tools/check_vocab_links.py

- meaning/vocab-links/<language>.jsonl: the header's language is the file's
  name and has a languages/<language>/vocab.jsonl; every vocab id is a vocab@1
  id in that file, exactly, listed once and in the vocab file's order; and
  every meaning is a content meaning in meaning/meanings.jsonl.

It also reports, per language, vocabulary words that a token in
meaning/columns/<language>.jsonl spells exactly but that aren't linked to the
token's meanings. That is information only: a column may use a word in a sense
its deck card doesn't teach (Korean 가요 is a song in its deck, a form of go in
a column).
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


def content_meanings(root, problems):
    path = root / "meaning" / "meanings.jsonl"
    if not path.is_file():
        return set()
    _, meanings = load(path, "meaning/meanings.jsonl", problems)
    return {m.get("id") for m in meanings if m.get("kind") == "content"}


def unlinked_tokens(root, lang, words, links, content):
    """Column tokens whose text is a vocab word not linked to their meanings."""
    path = root / "meaning" / "columns" / f"{lang}.jsonl"
    if not path.is_file():
        return set()
    out = set()
    for r in lib.read(path)[1]:
        for t in r.get("t", []):
            if len(t) != 3:
                continue
            ms = [m for m in t[2].split("+") if m in content]
            for vid in words.get(t[0], []):
                if ms and not set(ms) <= links.get(vid, set()):
                    out.add(f"{vid} ({'+'.join(ms)})")
    return out


def check(root=lib.ROOT):
    problems, info = [], []
    base = root / "meaning" / "vocab-links"
    if not base.is_dir():
        return problems, info
    content = content_meanings(root, problems)
    for p in sorted(base.glob("*.jsonl")):
        rel = p.relative_to(root)
        header, entries = load(p, rel, problems)
        lang = p.stem
        if header.get("language") != lang:
            problems.append(f"{rel}:1: language {header.get('language')!r} should be {lang!r}")
        vfile = root / "languages" / lang / "vocab.jsonl"
        if not vfile.is_file():
            problems.append(f"{rel}:1: there is no languages/{lang}/vocab.jsonl to link")
            continue
        _, vocab = load(vfile, vfile.relative_to(root), problems)
        order = {v.get("id"): i for i, v in enumerate(vocab)}
        words = {}
        for v in vocab:
            words.setdefault(v.get("word"), []).append(v.get("id"))
        seen, last, links = set(), -1, {}
        for n, e in enumerate(entries, start=2):
            vid = e.get("vocab")
            if vid not in order:
                problems.append(f"{rel}:{n}: vocab id {vid!r} is not in languages/{lang}/vocab.jsonl")
            else:
                if vid in seen:
                    problems.append(f"{rel}:{n}: vocab id {vid!r} is linked twice; list all its meanings on one line")
                elif order[vid] < last:
                    problems.append(f"{rel}:{n}: vocab id {vid!r} is out of order; keep the vocab file's order")
                last = max(last, order[vid])
                seen.add(vid)
            for m in e.get("meanings", []):
                if m not in content:
                    problems.append(f"{rel}:{n}: {m!r} is not a content meaning in meaning/meanings.jsonl")
            links[vid] = links.get(vid, set()) | set(e.get("meanings", []))
        loose = unlinked_tokens(root, lang, words, links, content)
        if loose:
            info.append(f"vocab-links: {lang}: column words whose card is not linked to that meaning: {', '.join(sorted(loose))}")
    return problems, info


def main():
    problems, info = check()
    print("\n".join(problems) or "vocab-links: OK")
    for line in info:
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
