"""Kana to Hepburn romaji, in the style the Japanese vocabulary uses: long
vowels with macrons (ō, ū, ā), ei and ii written out, n' before a vowel or y,
and a doubled consonant for small tsu.

    >>> romaji("がっこう")
    'gakkō'

Standard library only. Pass verb=True for a word whose final う is a verb
ending (思う is omou, not omō).
"""

_BASE = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o", "ん": "n",
    "ゔ": "vu",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa",
}

# Two-kana sounds: a kana ending in i plus a small ya/yu/yo, and the
# katakana-only combinations for loanwords (written here in hiragana).
_PAIRS = {}
for k, r in {"き": "k", "ぎ": "g", "に": "n", "ひ": "h", "び": "b", "ぴ": "p",
             "み": "m", "り": "r"}.items():
    _PAIRS.update({k + "ゃ": r + "ya", k + "ゅ": r + "yu", k + "ょ": r + "yo"})
for k, r in {"し": "sh", "じ": "j", "ち": "ch", "ぢ": "j"}.items():
    _PAIRS.update({k + "ゃ": r + "a", k + "ゅ": r + "u", k + "ょ": r + "o", k + "ぇ": r + "e"})
_PAIRS.update({
    "てぃ": "ti", "でぃ": "di", "とぅ": "tu", "どぅ": "du", "てゅ": "tyu", "でゅ": "dyu",
    "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo", "ふゅ": "fyu",
    "うぃ": "wi", "うぇ": "we", "うぉ": "wo",
    "ゔぁ": "va", "ゔぃ": "vi", "ゔぇ": "ve", "ゔぉ": "vo",
    "つぁ": "tsa", "つぃ": "tsi", "つぇ": "tse", "つぉ": "tso",
    "いぇ": "ye", "くぁ": "kwa", "ぐぁ": "gwa",
})

_MACRON = {"a": "ā", "i": "ī", "u": "ū", "e": "ē", "o": "ō"}


def _hiragana(text):
    """Katakana to hiragana; the long-vowel mark ー and anything else stay."""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" and c not in "ヵヶ" else c for c in text)


def romaji(kana, verb=False):
    """Hepburn romaji for a word written in hiragana or katakana."""
    h = _hiragana(kana)
    loan = h != kana  # katakana words keep ou and ei as written (no macron)
    tokens = []  # (romaji, kana it came from)
    i = 0
    while i < len(h):
        pair = h[i:i + 2]
        if pair in _PAIRS:
            tokens.append((_PAIRS[pair], pair))
            i += 2
        elif h[i] in _BASE:
            tokens.append((_BASE[h[i]], h[i]))
            i += 1
        else:
            tokens.append((h[i], h[i]))  # ー, っ and anything unknown
            i += 1

    out = []
    for n, (r, k) in enumerate(tokens):
        nxt = tokens[n + 1][0] if n + 1 < len(tokens) else ""
        prev = out[-1] if out else ""
        last = n == len(tokens) - 1
        if k == "っ":
            out.append("t" if nxt.startswith("ch") else (nxt[:1] if nxt[:1].isalpha() and nxt[:1] not in "aeiou" else ""))
        elif k == "ー":
            if prev and prev[-1] in _MACRON:
                out[-1] = prev[:-1] + _MACRON[prev[-1]]
        elif k == "ん":
            out.append("n'" if nxt[:1] in ("a", "i", "u", "e", "o", "y") and nxt else "n")
        elif not loan and prev and k in ("う", "お") and prev[-1] in "ou" and not (verb and last and k == "う"):
            # おう, おお, うう: a long vowel. (A word-final verb う stays u.)
            if (prev[-1] == "o") or (prev[-1] == "u" and k == "う"):
                out[-1] = prev[:-1] + _MACRON[prev[-1]]
            else:
                out.append(r)
        elif not loan and prev and k == "あ" and prev[-1] == "a" and tokens[n - 1][1] != "ゃ":
            out[-1] = prev[:-1] + "ā"
        else:
            out.append(r)
    return "".join(out)
