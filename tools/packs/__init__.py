"""Language packs: each language's content, exported in formats other
programs can open directly.

A pack is built from one language folder (languages/<id>/) and its varieties.
`load()` reads the folder into a plain dict, and each format in FORMATS writes
that dict out. Formats never read the repo themselves, so every format sees
the same content.

Content types the export doesn't know yet are still carried: each format
copies them as they are, so a new content type is never silently dropped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib  # noqa: E402

PACK_FORMAT = "squirrel-pack@1"


def languages(root=lib.ROOT):
    """Ids of every language, alphabetical."""
    return sorted(p.parent.name for p in (root / "languages").glob("*/meta.json"))


def _kind(data):
    head = data[0] if isinstance(data, tuple) else data
    return head.get("schema", "").partition("@")[0] if isinstance(head, dict) else ""


def _load_dir(folder, root):
    """One language or variety folder:

        {meta, metaText, content: [...], other: [...], varieties: [...]}

    content holds every JSON or JSONL file except meta.json, in path order,
    each as {kind, rel, path, schema, data, text}. rel is the path inside the
    folder. other holds any other file, as {rel, path, bytes}. Varieties are
    loaded the same way.
    """
    out = {"meta": lib.read(folder / "meta.json"),
           "metaText": (folder / "meta.json").read_text(encoding="utf-8"),
           "content": [], "other": [], "varieties": []}
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if not p.is_file() or rel.parts[0] == "varieties" or rel.as_posix() == "meta.json":
            continue
        entry = {"rel": rel.as_posix(), "path": p.relative_to(root).as_posix()}
        if p.suffix in (".json", ".jsonl"):
            data = lib.read(p)
            head = data[0] if isinstance(data, tuple) else data
            entry.update(kind=_kind(data) or p.stem, data=data, text=p.read_text(encoding="utf-8"),
                         schema=head.get("schema") if isinstance(head, dict) else None)
            out["content"].append(entry)
        else:
            entry["bytes"] = p.read_bytes()
            out["other"].append(entry)
    vdir = folder / "varieties"
    if vdir.is_dir():
        for v in sorted(d for d in vdir.iterdir() if (d / "meta.json").is_file()):
            out["varieties"].append(_load_dir(v, root))
    return out


def load(lang, root=lib.ROOT):
    """Everything a format needs to write one language's pack."""
    pack = _load_dir(root / "languages" / lang, root)
    pack["id"] = lang
    pack["commit"] = lib.data_commit(root)
    pack["license"] = (root / "LICENSE").read_text(encoding="utf-8") if (root / "LICENSE").is_file() else ""
    pack["sources"] = (root / "SOURCES.md").read_text(encoding="utf-8") if (root / "SOURCES.md").is_file() else ""
    return pack


def count(kind, data):
    """How many items a content file holds: words, lessons, cards and so on."""
    if isinstance(data, tuple):
        return len(data[1])
    for key in ("lessons", "entries", "cards", "items"):
        if isinstance(data.get(key), list):
            return len(data[key])
    return None


def variety_ids(pack):
    """Every variety under a pack, depth first."""
    out = []
    for v in pack["varieties"]:
        out.append(v["meta"]["id"])
        out += variety_ids(v)
    return out


from . import folder, sqlite  # noqa: E402

FORMATS = {
    "folder": folder,
    "sqlite": sqlite,
}
