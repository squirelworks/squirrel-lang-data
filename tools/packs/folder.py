"""The folder format: a language's content as plain files, split by type.

    <out>/<id>/
      README.md            what's in the pack, and its license and credits
      pack.json            the manifest: language, data commit, every file
      LICENSE.txt          CC BY-SA 4.0
      SOURCES.md           every source and its attribution
      meta.json
      vocab/vocab.jsonl    the vocabulary exactly as in the repo
      vocab/decks/NN-<deck>.tsv     one deck per file, for spreadsheets
      grammar/grammar.json the course exactly as in the repo
      grammar/lessons/NN-<lesson>.json   one lesson per file
      <type>/<file>        any other content type, exactly as in the repo
      varieties/<id>/...   each variety, laid out the same way

Files are written in a fixed order with no timestamps, so exporting the same
commit twice gives the same bytes.
"""
import csv
import io
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lib  # noqa: E402

from . import PACK_FORMAT, count, variety_ids  # noqa: E402

TSV_COLUMNS = ["word", "reading", "meaning", "note", "level", "freq", "varieties"]


def _json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _tsv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def _slug(text):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in text)


def _vocab_views(data):
    header, words = data
    files = {}
    cols = [c for c in TSV_COLUMNS if any(c in w for w in words) or c in ("word", "meaning")]
    for n, deck in enumerate(header.get("decks", []), start=1):
        rows = [cols]
        for w in words:
            if w.get("deck") != deck["id"]:
                continue
            row = []
            for c in cols:
                v = w.get(c, "")
                if isinstance(v, dict):
                    v = ", ".join(f"{k}:{x}" for k, x in v.items())
                elif isinstance(v, list):
                    v = ", ".join(v)
                row.append(v)
            rows.append(row)
        files[f"decks/{n:02d}-{_slug(deck['id'])}.tsv"] = _tsv(rows)
    return files


def _grammar_views(data):
    return {f"lessons/{n:02d}-{_slug(l['id'])}.json": _json(l)
            for n, l in enumerate(data.get("lessons", []), start=1)}


VIEWS = {"vocab": _vocab_views, "grammar": _grammar_views}


def place(rel, kind):
    """Where a file from a language folder goes in the pack: a top-level
    content file goes in a folder named after its type; anything in a
    subfolder keeps its path."""
    return f"{kind}/{rel}" if kind and "/" not in rel else rel


def _files(node, prefix=""):
    """{relative path: text or bytes} for one language or variety, its
    contents list and its varieties."""
    files = {f"{prefix}meta.json": node["metaText"]}
    contents = []
    for c in node["content"]:
        at = prefix + place(c["rel"], c["kind"])
        files[at] = c["text"]
        views = {f"{at.rsplit('/', 1)[0]}/{rel}": text
                 for rel, text in VIEWS.get(c["kind"], lambda d: {})(c["data"]).items()}
        files.update(views)
        contents.append({"kind": c["kind"], "schema": c["schema"], "source": c["path"],
                         "count": count(c["kind"], c["data"]), "files": [at] + sorted(views)})
    for o in node["other"]:
        files[prefix + o["rel"]] = o["bytes"]
        contents.append({"kind": None, "schema": None, "source": o["path"], "count": None,
                         "files": [prefix + o["rel"]]})
    varieties = {}
    for v in node["varieties"]:
        vid = v["meta"]["id"]
        vfiles, vcontents, vvars = _files(v, f"{prefix}varieties/{vid}/")
        files.update(vfiles)
        varieties[vid] = {"name": v["meta"].get("name"), "kind": v["meta"].get("kind"),
                          "parent": v["meta"].get("parent"), "contents": vcontents}
        varieties.update(vvars)
    return files, contents, varieties


def _readme(pack, contents):
    meta = pack["meta"]
    lines = [f"# {meta.get('name', pack['id'])} ({meta.get('nativeName', '')})", "",
             f"A language pack from squirrel-lang-data, commit `{pack['commit']}`.", "",
             "| Content | Items | Files |", "|---|---|---|"]
    for c in contents:
        n = c["count"] if c["count"] is not None else ""
        top = c["files"][0].split("/")[0]
        lines.append(f"| {c['kind'] or 'file'} | {n} | `{top}/` |" if "/" in c["files"][0] else f"| {c['kind'] or 'file'} | {n} | `{top}` |")
    if not contents:
        lines.append("| (none yet) | | |")
    vids = variety_ids(pack)
    if vids:
        lines += ["", "Varieties: " + ", ".join(vids) + " (in `varieties/`)."]
    lines += ["", "## License", "",
              "The content is licensed under CC BY-SA 4.0 (`LICENSE.txt`). You may share and adapt it,",
              "including commercially, if you credit the sources listed in `SOURCES.md` and share",
              "adaptations under the same license.", ""]
    return "\n".join(lines)


def write(pack, out_dir):
    """Write the pack to out_dir/<id>/, replacing an earlier export there.
    Returns the pack's path."""
    dest = out_dir / pack["id"]
    if dest.exists():
        if not (dest / "pack.json").is_file():
            raise FileExistsError(f"{dest} exists and isn't a pack; not replacing it")
        shutil.rmtree(dest)
    files, contents, varieties = _files(pack)
    files["LICENSE.txt"] = pack["license"]
    files["SOURCES.md"] = pack["sources"]
    files["README.md"] = _readme(pack, contents)
    manifest = {
        "format": PACK_FORMAT,
        "language": pack["id"],
        "name": pack["meta"].get("name"),
        "nativeName": pack["meta"].get("nativeName"),
        "code": pack["meta"].get("code"),
        "dataCommit": pack["commit"],
        "license": "CC-BY-SA-4.0",
        "contents": contents,
        "varieties": varieties,
    }
    manifest["files"] = sorted([*files, "pack.json"])
    files["pack.json"] = _json(manifest)
    for rel in sorted(files):
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(files[rel], bytes):
            p.write_bytes(files[rel])
        else:
            p.write_text(files[rel], encoding="utf-8")
    return dest


def check(pack, dest, root):
    """Problems with a written pack, found by reading the repo again rather
    than trusting what load() saw."""
    problems = []
    manifest = json.loads((dest / "pack.json").read_text(encoding="utf-8"))
    actual = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
    if actual != manifest["files"]:
        extra = sorted(set(actual) - set(manifest["files"]))
        missing = sorted(set(manifest["files"]) - set(actual))
        problems.append(f"pack.json files don't match the folder (missing {missing}, unlisted {extra})")
    src = root / "languages" / pack["id"]
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src).as_posix()
        prefix = ""
        if rel.startswith("varieties/"):
            _, vid, rel = rel.split("/", 2)
            prefix = f"varieties/{vid}/"
        kind = ""
        if p.suffix in (".json", ".jsonl") and rel != "meta.json":
            data = lib.read(p)
            head = data[0] if isinstance(data, tuple) else data
            kind = (head.get("schema", "").partition("@")[0] if isinstance(head, dict) else "") or p.stem
        at = dest / (prefix + place(rel, kind))
        if not at.is_file():
            problems.append(f"{p.relative_to(root)} is missing from the pack")
        elif at.read_bytes() != p.read_bytes():
            problems.append(f"{p.relative_to(root)} differs in the pack ({at.relative_to(dest)})")
    for c in manifest["contents"] + [c for v in manifest["varieties"].values() for c in v["contents"]]:
        if c["kind"] == "vocab":
            decks = [f for f in c["files"] if f.endswith(".tsv")]
            rows = sum(len(list(csv.reader(io.StringIO((dest / f).read_text(encoding="utf-8")), delimiter="\t"))) - 1
                       for f in decks)
            if rows != c["count"]:
                problems.append(f"{c['source']}: deck files hold {rows} words, the source {c['count']}")
        if c["kind"] == "grammar":
            lessons = [f for f in c["files"] if "/lessons/" in f]
            if len(lessons) != c["count"]:
                problems.append(f"{c['source']}: {len(lessons)} lesson files for {c['count']} lessons")
    return problems
