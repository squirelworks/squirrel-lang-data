#!/usr/bin/env python3
"""Import the hanzi and hanja readings, and the shared CJK table's radicals and
stroke counts, from the Unihan database and the HSK 3.0 word lists.

    python3 tools/importers/cjk_unihan.py --unihan DIR --hsk complete.json

    languages/chinese/characters/hanzi.jsonl  <- every character of HSK 3.0
                                                 levels 1-6, with Unihan pinyin,
                                                 meaning and traditional form
    languages/hangul/characters/hanja.jsonl   <- the 1,800 basic hanja for
                                                 education (Unihan kHangul
                                                 readings flagged E), with
                                                 Unihan hangul and meaning
    cjk/characters.jsonl                      <- a row for every new character,
                                                 with Unihan radical and stroke
                                                 count

Sources (see SOURCES.md), downloaded by hand:
  * the Unihan database (Unicode license), Unihan.zip from
    https://www.unicode.org/Public/UCD/latest/ucd/: Unihan_Readings.txt
    (kMandarin, kDefinition, kHangul), Unihan_IRGSources.txt (kRSUnicode,
    kTotalStrokes) and Unihan_Variants.txt (kTraditionalVariant)
  * complete-hsk-vocabulary (MIT), complete.json from
    https://github.com/drkameleon/complete-hsk-vocabulary, for which words
    belong to which HSK 3.0 level

Rows already in the shared table keep their radical and stroke count (kanji
keep LanguageStudentDesk's Jōyō values), and rows no tradition reads any more
are dropped. Ported from LanguageStudentDesk's languages/cjk/build_cjk.py.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fmt  # noqa: E402
import lib  # noqa: E402

HSK_LEVELS = 6
# Education hanja that Unihan gives no kDefinition, and the character whose
# meaning they share. 𮕩 is the Korean education-list form of 衰.
MEANING_FROM = {"𮕩": "衰"}


def read_unihan(folder):
    data = {}
    for name in ("Unihan_Readings.txt", "Unihan_IRGSources.txt", "Unihan_Variants.txt"):
        for line in (Path(folder) / name).read_text(encoding="utf-8").splitlines():
            if not line.startswith("U+"):
                continue
            cp, field, value = line.split("\t", 2)
            data.setdefault(chr(int(cp[2:], 16)), {})[field] = value
    return data


def radical(rs):
    """kRSUnicode '72.0' or "120'.3" -> the Kangxi radical as an ideograph."""
    num = int(re.match(r"\d+", rs).group())
    return unicodedata.normalize("NFKC", chr(0x2F00 + num - 1))


def meaning(definition):
    """The first few senses of a kDefinition, short enough for a card."""
    parts = [p.strip() for p in definition.split(";") if p.strip()]
    out = ""
    for p in parts:
        if out and len(out) + len(p) > 40:
            break
        out = out + "; " + p if out else p
    return out


def variant(value):
    """'U+66F8' or 'U+66F8 U+...' -> the characters, joined."""
    return "".join(chr(int(v[2:].split("<")[0], 16)) for v in value.split())


def hsk_chars(words):
    """Each HSK 3.0 character of levels 1-6, by the lowest level a word with it
    appears at, in the order the list first uses it."""
    level_of = {}
    for lvl in range(1, HSK_LEVELS + 1):
        tag = f"new-{lvl}"
        for w in sorted((w for w in words if tag in w.get("level", [])), key=lambda w: w.get("frequency", 10**9)):
            for ch in w["simplified"]:
                if unicodedata.category(ch) == "Lo" and ch not in level_of:
                    level_of[ch] = lvl
    return level_of


def hanzi_entries(unihan, level_of):
    out = []
    for ch, lvl in level_of.items():
        u = unihan.get(ch, {})
        if not u.get("kMandarin") or not u.get("kDefinition"):
            continue
        e = {"char": ch, "roman": u["kMandarin"].split()[0], "info": meaning(u["kDefinition"]),
             "pinyin": u["kMandarin"], "hsk": lvl}
        trad = variant(u["kTraditionalVariant"]) if u.get("kTraditionalVariant") else ""
        if trad and trad != ch:
            e["traditional"] = trad
        out.append(e)
    return out


def hanja_entries(unihan):
    rows = []
    for ch, u in unihan.items():
        readings = [r.split(":") for r in u.get("kHangul", "").split()]
        edu = [h for h, src in readings if "E" in src]
        definition = u.get("kDefinition") or unihan.get(MEANING_FROM.get(ch, ""), {}).get("kDefinition")
        if edu and definition:
            rows.append((edu[0], ch, edu, definition))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [{"char": ch, "roman": " / ".join(edu), "info": meaning(definition), "hangul": " / ".join(edu)}
            for _, ch, edu, definition in rows]


def table_rows(rows, read, unihan):
    """The shared table: existing rows that some tradition still reads, then a
    row for each new character, in the order the traditions list them."""
    out = [r for r in rows if r["char"] in read]
    have = {r["char"] for r in out}
    for ch in read:
        if ch in have:
            continue
        u = unihan.get(ch, {})
        if not u.get("kRSUnicode") or not u.get("kTotalStrokes"):
            sys.exit(f"{ch}: Unihan has no radical or stroke count")
        out.append({"char": ch, "radical": radical(u["kRSUnicode"].split()[0]),
                    "strokes": int(u["kTotalStrokes"].split()[0])})
        have.add(ch)
    return out


def write(path, header, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [header, *rows]), encoding="utf-8")
    path.write_text(fmt.format_file(path), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--unihan", required=True, help="folder with the Unihan_*.txt files")
    ap.add_argument("--hsk", required=True, help="complete-hsk-vocabulary complete.json")
    a = ap.parse_args(argv)
    unihan = read_unihan(a.unihan)
    hanzi = hanzi_entries(unihan, hsk_chars(json.loads(Path(a.hsk).read_text(encoding="utf-8"))))
    hanja = hanja_entries(unihan)
    paths = {t: lib.ROOT / "languages" / lang / "characters" / f"{t}.jsonl"
             for t, lang in (("kanji", "japanese"), ("hanzi", "chinese"), ("hanja", "hangul"))}
    kanji = lib.read(paths["kanji"])[1]
    read = dict.fromkeys(e["char"] for e in [*kanji, *hanzi, *hanja])
    table_path = lib.ROOT / "cjk" / "characters.jsonl"
    header, rows = lib.read(table_path)
    table = table_rows(rows, read, unihan)
    write(table_path, header, table)
    write(paths["hanzi"], lib.read(paths["hanzi"])[0], hanzi)
    write(paths["hanja"], lib.read(paths["hanja"])[0], hanja)
    print(f"hanzi {len(hanzi)}, hanja {len(hanja)}, table {len(table)}")


if __name__ == "__main__":
    main()
