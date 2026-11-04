#!/usr/bin/env python3
"""Tag every vocabulary word that has no frequency tag yet, for each language
wordfreq covers.

    pip install "wordfreq[cjk,mecab]"
    python3 tools/importers/freq_tags.py              # every covered language
    python3 tools/importers/freq_tags.py greek hindi  # just these

The tag comes from wordfreq's Zipf frequency (see freq.py): core at 4.5 and
above, common from 3.5, rare below, taking the most frequent spelling (Russian
ё or е, Hindi with or without the nukta,
ँ or ं). Dictionary forms such as infinitives
are rarer as written forms than the words they stand for, so a few common verbs
land in rare. A word that already has a tag keeps it, so
a rerun changes nothing. Languages wordfreq doesn't cover are left alone.
wordfreq's data is CC BY-SA 4.0.
"""
import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fmt  # noqa: E402
import freq  # noqa: E402
import lib  # noqa: E402

# Language folder -> wordfreq code, for the folders wordfreq covers.
WORDFREQ = {
    "arabic": "ar", "bengali": "bn", "chinese": "zh", "cyrillic": "ru", "english": "en",
    "french": "fr", "german": "de", "greek": "el", "hangul": "ko", "hebrew": "he",
    "hindi": "hi", "italian": "it", "japanese": "ja", "taiwanese": "zh", "tamil": "ta",
}
NOTE = "Frequency tags come from wordfreq (CC BY-SA 4.0)."


def variants(word, code):
    """Spellings to look up besides the word itself: the corpora behind
    wordfreq mostly write Russian ё as е and leave out the Hindi nukta and write
    chandrabindu as anusvara."""
    out = [word]
    if code == "ru" and "ё" in word:
        out.append(word.replace("ё", "е").replace("Ё", "Е"))
    if code == "hi" and "\u093c" in unicodedata.normalize("NFD", word):
        out.append(unicodedata.normalize("NFC", unicodedata.normalize("NFD", word).replace("\u093c", "")))
    if code == "hi" and "ँ" in word:
        out += [v.replace("ँ", "ं") for v in list(out)]
    return out


def tagger(code):
    """word -> 'core' | 'common' | 'rare', from the most frequent spelling."""
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        sys.exit('needs wordfreq: pip install "wordfreq[cjk,mecab]"')
    return lambda word: freq.tag(max(zipf_frequency(v, code) for v in variants(word, code)))


def tag_entries(header, entries, tagger):
    """Adds a freq tag to entries without one; returns (header, entries, count)."""
    n = 0
    for e in entries:
        if "freq" not in e:
            e["freq"] = tagger(e["word"])
            n += 1
    head = dict(header)
    if n and not any("wordfreq" in x for x in head.get("notes", [])):
        head["notes"] = head.get("notes", []) + [NOTE]
    return head, entries, n


def main(argv):
    langs = argv or sorted(WORDFREQ)
    for lang in langs:
        if lang not in WORDFREQ:
            sys.exit(f"{lang}: wordfreq has no data for it")
        path = lib.ROOT / "languages" / lang / "vocab.jsonl"
        if not path.is_file():
            continue
        header, entries = lib.read(path)
        head, out, n = tag_entries(header, entries, tagger(WORDFREQ[lang]))
        if n:
            path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in [head, *out]), encoding="utf-8")
            path.write_text(fmt.format_file(path), encoding="utf-8")
        print(f"{path.relative_to(lib.ROOT)}: {n} words tagged")


if __name__ == "__main__":
    main(sys.argv[1:])
