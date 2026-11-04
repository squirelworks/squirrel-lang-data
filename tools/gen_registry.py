#!/usr/bin/env python3
"""Generate LanguageStudentDesk's language registry from languages/*/meta.json.

    python3 data/tools/gen_registry.py --out languages            # write
    python3 data/tools/gen_registry.py --out languages --check    # exit 1 if stale

Run from the consumer's root with this repo checked out at data/ (or pass
--data). Writes, inside --out:

    registry.js       window.LSD_LANGUAGE_REGISTRY = {id: meta, ...}
    <id>/meta.json    each language's meta, in the shape the Desk reads today

The Desk shape renames `scripts` back to `writingSystems` and adds `data`, the
content files the consumer's language folder holds (kinds: characters,
grammar, vocab, reference). Languages whose characterKeys include a CJK
tradition (hanzi, kanji, hanja) also list the shared CJK table and that
tradition's readings file.

Varieties are left out unless --varieties is given, so they don't reach a
picker before the switches for them exist. With it, each variety is written
with everything it inherits from its parent filled in, plus `parent`, `kind`
and `period`.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

DATA = lib.ROOT

# The Desk's data kinds and the file each lives in, in its language folder.
KINDS = {"characters": "characters.js", "grammar": "grammar.js", "vocab": "vocab.js", "reference": "reference.json"}
# The shared CJK table and each tradition's readings file, relative to --out.
CJK_TABLE = "cjk/characters.js"
CJK_READINGS = {"hanzi": "chinese/hanzi.js", "kanji": "japanese/kanji.js", "hanja": "hangul/hanja.js"}
# Fields a variety inherits from its parent when it doesn't give its own.
INHERITED = ["nativeName", "scripts", "characterKeys", "romanization", "notes", "speech", "font", "direction"]
# Desk field order.
ORDER = ["id", "name", "nativeName", "writingSystems", "characterKeys", "romanization", "notes", "speech",
         "font", "direction", "code", "parent", "kind", "period", "reconstructed", "data"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def languages(data):
    """[(meta, [variety, ...])] for every language, by id."""
    out = []
    for p in sorted((data / "languages").glob("*/meta.json")):
        meta = read(p)
        vs = [read(v) for v in sorted((p.parent / "varieties").glob("*/meta.json"))]
        out.append((meta, vs))
    return out


def resolve(variety, by_id):
    """A variety with its inherited fields filled in from its parent chain."""
    chain, cur = [], variety
    while cur is not None:
        chain.append(cur)
        cur = by_id.get(cur.get("parent"))
    out = {}
    for node in reversed(chain):  # language first, the variety itself last
        for k in INHERITED:
            if k in node:
                out[k] = node[k]
    for k in ("id", "name", "code", "parent", "kind", "period", "reconstructed"):
        if k in variety:
            out[k] = variety[k]
    return out


def data_files(lang_id, meta, out_dir):
    """The Desk's "data" map: the content files out_dir/<id>/ holds."""
    folder = out_dir / lang_id
    data = {}
    for kind, name in KINDS.items():
        files = [name] if (folder / name).is_file() else []
        if kind == "characters":
            for t in meta.get("characterKeys", []):
                if t in CJK_READINGS and (out_dir / CJK_READINGS[t]).is_file():
                    if "../" + CJK_TABLE not in files:
                        files.append("../" + CJK_TABLE)
                    rel = CJK_READINGS[t]
                    files.append(rel.split("/", 1)[1] if rel.startswith(lang_id + "/") else "../" + rel)
        if files:
            data[kind] = files[0] if len(files) == 1 else files
    return data


def desk_shape(meta, out_dir):
    m = {k: v for k, v in meta.items() if k not in ("schema", "varieties")}
    if "scripts" in m:
        m["writingSystems"] = m.pop("scripts")
    data = data_files(meta["id"], meta, out_dir)
    if data:
        m["data"] = data
    return {k: m[k] for k in ORDER if k in m} | {k: v for k, v in m.items() if k not in ORDER}


def build(data, out_dir, with_varieties=False):
    """{relative path: text} for every file this generator owns in out_dir."""
    entries = {}
    for meta, vs in languages(data):
        entries[meta["id"]] = desk_shape(meta, out_dir)
        if with_varieties:
            by_id = {meta["id"]: meta} | {v["id"]: v for v in vs}
            for v in vs:
                entries[v["id"]] = desk_shape(resolve(v, by_id), out_dir)
    command = "python3 data/tools/gen_registry.py --out " + out_dir.name + (" --varieties" if with_varieties else "")
    header = f"// Generated from squirrel-lang-data {lib.data_commit(data)} languages/*/meta.json by: {command}\n// Do not edit; change the data repo and run it again.\n"
    files = {"registry.js": header + "window.LSD_LANGUAGE_REGISTRY = " + json.dumps(entries, ensure_ascii=False, indent=2) + ";\n"}
    for id_, m in entries.items():
        files[f"{id_}/meta.json"] = json.dumps(m, ensure_ascii=False, indent=2) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path, help="the consumer's languages/ folder")
    ap.add_argument("--data", type=Path, default=DATA, help="this repo's checkout (default: the one this tool is in)")
    ap.add_argument("--varieties", action="store_true", help="also write regional varieties and historical stages")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file differs")
    args = ap.parse_args(argv)
    command = f"python3 data/tools/gen_registry.py --out {args.out.name}" + (" --varieties" if args.varieties else "")
    return lib.write_outputs(build(args.data, args.out, args.varieties), args.out, args.check, command)

if __name__ == "__main__":
    sys.exit(main())
