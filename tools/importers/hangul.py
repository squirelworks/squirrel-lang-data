"""Hangul to Revised Romanization, in the style the Korean vocabulary uses:
lowercase, no hyphens, with the sound changes the system writes (liaison,
nasalization, ㄹ assimilation, palatalization, and ㅎ before ㄱ ㄷ ㅈ). It
leaves tensification unwritten and keeps the h of ㄱ ㄷ ㅂ + ㅎ, as in
sijakhada.

    >>> romanize("한국어")
    'hangugeo'

Standard library only.
"""

INITIAL = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
VOWEL = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi",
         "yu", "eu", "ui", "i"]
# Final consonants as jamo names, index 0 = none.
FINAL = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ",
         "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
INIT_JAMO = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
ROMAN_INIT = dict(zip(INIT_JAMO, INITIAL))

# A final before a pause: its representative sound.
CODA = {"": "", "ㄱ": "k", "ㄲ": "k", "ㄳ": "k", "ㄴ": "n", "ㄵ": "n", "ㄶ": "n", "ㄷ": "t", "ㄹ": "l", "ㄺ": "k",
        "ㄻ": "m", "ㄼ": "l", "ㄽ": "l", "ㄾ": "l", "ㄿ": "p", "ㅀ": "l", "ㅁ": "m", "ㅂ": "p", "ㅄ": "p", "ㅅ": "t",
        "ㅆ": "t", "ㅇ": "ng", "ㅈ": "t", "ㅊ": "t", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p", "ㅎ": "t"}
# A final before a vowel (ㅇ initial): (what stays, what moves to the next syllable).
LIAISON = {"ㄱ": ("", "ㄱ"), "ㄲ": ("", "ㄲ"), "ㄳ": ("ㄱ", "ㅅ"), "ㄴ": ("", "ㄴ"), "ㄵ": ("ㄴ", "ㅈ"),
           "ㄶ": ("", "ㄴ"), "ㄷ": ("", "ㄷ"), "ㄹ": ("", "ㄹ"), "ㄺ": ("ㄹ", "ㄱ"), "ㄻ": ("ㄹ", "ㅁ"),
           "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅅ"), "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"), "ㅀ": ("", "ㄹ"),
           "ㅁ": ("", "ㅁ"), "ㅂ": ("", "ㅂ"), "ㅄ": ("ㅂ", "ㅅ"), "ㅅ": ("", "ㅅ"), "ㅆ": ("", "ㅆ"),
           "ㅇ": ("ㅇ", "ㅇ"), "ㅈ": ("", "ㅈ"), "ㅊ": ("", "ㅊ"), "ㅋ": ("", "ㅋ"), "ㅌ": ("", "ㅌ"),
           "ㅍ": ("", "ㅍ"), "ㅎ": ("", "ㅇ")}
NASAL = {"k": "ng", "t": "n", "p": "m"}
ASPIRATE = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}


def _split(ch):
    n = ord(ch) - 0xAC00
    if not 0 <= n < 11172:
        return None
    return INIT_JAMO[n // 588], VOWEL[(n % 588) // 28], FINAL[n % 28]


def romanize(text):
    """Revised Romanization of a word or phrase written in Hangul."""
    out = []
    for word in text.split(" "):
        syl = [list(_split(c)) if _split(c) else c for c in word]
        parts, lateral = [], set()  # syllables whose ㄹ is said l (after an l)
        for i, s in enumerate(syl):
            if isinstance(s, str):
                parts.append(s)
                continue
            init, vowel, final = s
            nxt = syl[i + 1] if i + 1 < len(syl) and not isinstance(syl[i + 1], str) else None
            coda = CODA[final]
            if nxt:
                ni = nxt[0]
                if ni == "ㅇ" and nxt[1] == "i" and final in ("ㄷ", "ㅌ", "ㄾ"):
                    # Palatalization: 같이 is gachi, 굳이 guji.
                    coda = "l" if final == "ㄾ" else ""
                    nxt[0] = "ㅈ" if final == "ㄷ" else "ㅊ"
                elif ni == "ㅇ" and final:
                    stay, move = LIAISON[final]
                    coda = CODA[stay] if stay != "ㅇ" else "ng"
                    if move != "ㅇ":
                        nxt[0] = move
                elif final in ("ㅎ", "ㄶ", "ㅀ") and ni in ASPIRATE:
                    nxt[0] = ASPIRATE[ni]
                    coda = CODA[{"ㅎ": "", "ㄶ": "ㄴ", "ㅀ": "ㄹ"}[final]]
                elif final == "ㅎ" and ni == "ㄴ":
                    coda = "n"
                elif ni in ("ㄴ", "ㅁ") and coda in NASAL:
                    coda = NASAL[coda]
                elif ni == "ㄹ" and coda == "n":
                    coda, nxt[0] = "l", "ㄹ"
                    lateral.add(i + 1)
                elif ni == "ㄹ" and coda in ("k", "p", "m", "ng"):
                    coda, nxt[0] = NASAL.get(coda, coda), "ㄴ"
                elif ni == "ㄴ" and coda == "l":
                    nxt[0] = "ㄹ"
                    lateral.add(i + 1)
            r_init = ROMAN_INIT[init]
            if init == "ㄹ" and (i in lateral or (parts and parts[-1].endswith("l"))):
                r_init = "l"
            elif init == "ㄹ" and i == 0:
                r_init = "r"
            parts.append(r_init + vowel + coda)
        out.append("".join(parts))
    return " ".join(out)
