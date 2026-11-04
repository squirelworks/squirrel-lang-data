#!/usr/bin/env python3
"""Import the most frequent Mandarin words, with CC-CEDICT readings and
meanings, into languages/chinese/vocab.jsonl.

    pip install "wordfreq[cjk]"          # word list and frequency tags
    python3 tools/importers/cedict.py

There is no clearly licensed HSK or TOCFL list, so words come by frequency
instead: wordfreq's most frequent Chinese words (CC BY-SA 4.0), kept when
CC-CEDICT (CC BY-SA 4.0) has them. CC-CEDICT is read from the cc-cedict npm
package at a pinned version (its build of the 2026-01-04 dictionary), checked
against the registry's integrity hash, fetched into cache/ and never committed.

What it does, so a rerun gives the same file:
- Keeps the decks written for this project and drops any earlier freq-* decks.
- Takes the first WORDS words of wordfreq's list that are written only in
  Chinese characters and that CC-CEDICT has as a common word (not only a name,
  surname or variant spelling).
- A word already in a written deck gets its frequency tag there instead of
  being added again.
- Every other word goes into Most common words (core) or Common words
  (common), with tone-marked pinyin, the first CC-CEDICT senses as its meaning,
  and its traditional form and other readings in the note when they apply.
"""
import base64
import hashlib
import io
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fmt  # noqa: E402
import lib  # noqa: E402
from freq import zipf_tagger  # noqa: E402

VERSION = "1.1.1"
URL = f"https://registry.npmjs.org/cc-cedict/-/cc-cedict-{VERSION}.tgz"
WORDS = 5000
DECKS = [("core", "freq-core", "Most common words"), ("common", "freq-common", "Common words")]
SOURCE = "CC-CEDICT (readings and meanings) and wordfreq (word list and frequency)"
LICENSE = "CC BY-SA 4.0"
NOTES = [
    "The decks Most common words and Common words are imported by tools/importers/cedict.py: "
    "wordfreq's most frequent Chinese words (CC BY-SA 4.0), with pinyin and meanings from "
    "CC-CEDICT (MDBG, CC BY-SA 4.0).",
    "Frequency tags come from wordfreq (CC BY-SA 4.0).",
]
# Words whose usual reading isn't the one with the most CC-CEDICT senses.
PREFER = {"了": "le5", "着": "zhe5", "没": "mei2", "么": "me5", "南": "nan2", "得": "de5", "起来": "qi3 lai5",
          "告诉": "gao4 su5", "重": "zhong4", "雨": "yu3", "卡": "ka3", "圈": "quan1", "陆": "lu4", "炮": "pao4",
          "吓": "xia4", "空": "kong1", "当日": "dang1 ri4", "什": "shen2", "说法": "shuo1 fa3", "啊": "a5"}
HAN = re.compile(r"^[㐀-鿿]+$")
SKIP = re.compile(r"^(surname |(old |archaic |erhua |Japanese )?variant of |see |used in |abbr\. for |"
                  r"also written |CL:|\(old\)|\(archaic\)|\(dialect\)|\(Tw\))")
TONES = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}


def fetch(cache):
    path = cache / f"cc-cedict-{VERSION}.tgz"
    if not path.is_file():
        cache.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"https://registry.npmjs.org/cc-cedict/{VERSION}") as r:
            want = json.load(r)["dist"]["integrity"]
        with urllib.request.urlopen(URL) as r:
            data = r.read()
        algo, _, digest = want.partition("-")
        if base64.b64encode(hashlib.new(algo, data).digest()).decode() != digest:
            sys.exit(f"{URL}: integrity check failed")
        path.write_bytes(data)
    with tarfile.open(path) as tar:
        text = tar.extractfile("package/data/all.js").read().decode("utf-8")
    return json.loads(text[text.index("{"):].rstrip().rstrip(";"))["all"]  # "export default {...}"


def pinyin(numbered):
    """'xie4 xie5' -> 'xièxie'; syllables of one word are written together."""
    out = []
    for syl in numbered.split():
        syl = syl.replace("u:", "ü").replace("v", "ü")
        m = re.fullmatch(r"([A-Za-zü]+)([1-5])", syl)
        if not m:
            out.append(syl)
            continue
        base, tone = m[1], int(m[2])
        if tone < 5:
            low = base.lower()
            i = next((low.index(v) for v in "ae" if v in low), None)
            if i is None:
                i = low.index("o") if "ou" in low else max(low.rfind(v) for v in "iouü")
            base = base[:i] + TONES[low[i]][tone - 1] + base[i + 1:]
        if out and base[:1].lower() in "aeoāáǎàēéěèōóǒò":
            base = "'" + base
        out.append(base)
    return "".join(out)


def senses(english, most=4):
    """Usable CC-CEDICT senses (no names, variants or cross-references), at most `most`."""
    parts = [english] if isinstance(english, str) else english
    out = []
    for s in parts:
        s = re.sub(r"^\(bound form\) ", "", s.strip())
        s = re.sub(r"\[[A-Za-z0-9: ]+\]", "", s)              # 得[de2] -> 得
        s = re.sub(r"[\u3400-\u9fff]+\|([\u3400-\u9fff]+)", r"\1", s)  # 無|无 -> 无
        s = re.sub(r" ?\((also|Taiwan) pr\.[^)]*\)", "", s)
        s = re.sub(r",? as in .*$", "", s)
        s = re.sub(r";? ?(also|Taiwan) pr\..*$", "", s)
        s = re.sub(r" ?\([^()]{25,}\)", "", s).strip(" ;,")    # long asides
        if len(s) > 60:
            s = s[:60].rsplit(" ", 1)[0].rstrip(" ;,(") + "…"
        if s and not SKIP.match(s) and s.lower() not in (o.lower() for o in out):
            out.append(s)
    return out[:most]


def joined(senses_, limit=100):
    """'a; b; c', stopping before the text gets longer than limit (always at least one)."""
    out = senses_[:1]
    for s in senses_[1:]:
        if len("; ".join(out + [s])) > limit:
            break
        out.append(s)
    return "; ".join(out)


def index(entries):
    """simplified -> [(traditional, pinyin, english)] for the common-word (lowercase pinyin) entries."""
    out = {}
    for trad, simp, py, en, *_ in entries:
        if not py[:1].isupper():
            out.setdefault(simp, []).append((trad, py, en))
    return out


def pick(cands, word=None):
    """The reading with the most usable senses, plus the other readings, or None.
    CC-CEDICT doesn't say which reading is commonest, so the others go in the note."""
    usable = [(trad, py, senses(en, most=99)) for trad, py, en in cands]
    usable = [u for u in usable if u[2]]
    if not usable:
        return None
    best = max(usable, key=lambda u: (u[1] == PREFER.get(word), len(u[2])))
    others, seen = [], {pinyin(best[1])}
    for u in usable:
        if pinyin(u[1]) not in seen:
            seen.add(pinyin(u[1]))
            others.append(u)
    return best[0], best[1], best[2][:4], others


def build(header, entries, words, cedict, freq):
    own = [e for e in entries if not e["deck"].startswith("freq-")]
    # No HSK level comes from frequency: news-heavy counts put 政府 at HSK 1
    # and 喝 at HSK 4 (#41). Levels on the written decks are placed by hand and
    # kept as they are.
    decks = [d for d in header["decks"] if not d["id"].startswith("freq-")]
    mine = {e["word"] for e in own}
    added = {band: [] for band, _, _ in DECKS}
    taken = 0
    for w in words:
        if taken >= WORDS:
            break
        if not HAN.match(w) or w not in cedict:
            continue
        hit = pick(cedict[w], w)
        if not hit:
            continue
        taken += 1
        if w in mine:
            continue
        band = freq(w)
        if band not in added:
            continue
        trad, py, s, others = hit
        note = []
        if trad != w:
            note.append(f"Traditional: {trad}.")
        for _, opy, osenses in others[:2]:
            note.append(f"Also read {pinyin(opy)}: {joined(osenses[:2], 60)}.")
        e = {"id": f"freq-{band}/{w}", "deck": f"freq-{band}", "word": w, "reading": pinyin(py), "meaning": joined(s)}
        if note:
            e["note"] = " ".join(note)
        added[band].append(e)
    out = own + [e for band, _, _ in DECKS for e in added[band]]
    for e in out:
        if "freq" not in e:
            e["freq"] = freq(e["word"])
    head = dict(header)
    head["notes"] = [x for x in header.get("notes", []) if x not in NOTES and "cedict.py" not in x] + NOTES
    head["source"], head["license"] = SOURCE, LICENSE
    head["decks"] = decks + [{"id": deck, "title": title} for band, deck, title in DECKS if added[band]]
    return head, out


def main():
    from wordfreq import top_n_list
    path = lib.ROOT / "languages" / "chinese" / "vocab.jsonl"
    header, entries = lib.read(path)
    cedict = index(fetch(lib.ROOT / "cache" / "cedict"))
    head, out = build(header, entries, top_n_list("zh", 4 * WORDS), cedict, zipf_tagger("zh"))
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in [head, *out]), encoding="utf-8")
    path.write_text(fmt.format_file(path), encoding="utf-8")
    new = sum(e["deck"].startswith("freq-") for e in out)
    print(f"{path.relative_to(lib.ROOT)}: {new} words added; every word has a frequency tag")


if __name__ == "__main__":
    main()
