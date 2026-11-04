#!/usr/bin/env python3
"""Convert LanguageStudentDesk's languages/<id>/meta.json files to meta@1.

    python3 tools/migrate/lsd_meta.py <LanguageStudentDesk checkout>

Writes languages/<id>/meta.json here. The conversion keeps every field except
`data` (generators find a language's content from the files in its folder),
renames `writingSystems` to `scripts`, and adds the language's ISO 639-3
`code`. Run tools/fmt.py afterwards.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ISO 639-3 code for each LanguageStudentDesk language id. Macrolanguage codes
# are used where the content is the language's standard form.
CODES = {
    "amharic": "amh", "arabic": "ara", "armenian": "hye", "bengali": "ben",
    "burmese": "mya", "cherokee": "chr", "chinese": "zho", "cyrillic": "rus",
    "english": "eng", "french": "fra", "georgian": "kat", "german": "deu",
    "greek": "ell", "gujarati": "guj", "hangul": "kor", "hebrew": "heb",
    "hindi": "hin", "inuktitut": "iku", "italian": "ita", "japanese": "jpn",
    "kannada": "kan", "khmer": "khm", "klingon": "tlh", "lao": "lao",
    "latin": "lat", "malayalam": "mal", "manipuri": "mni", "mongolian": "mon",
    "odia": "ory", "punjabi": "pan", "sinhala": "sin", "taiwanese": "cmn",
    "tamazight": "zgh", "tamil": "tam", "telugu": "tel", "thai": "tha",
    "tibetan": "bod",
}


def convert(meta):
    out = {"schema": "meta@1"}
    for key, value in meta.items():
        if key == "data":
            continue
        out["scripts" if key == "writingSystems" else key] = value
    out["code"] = CODES[meta["id"]]
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]) / "languages"
    metas = sorted(src.glob("*/meta.json"))
    missing = [p.parent.name for p in metas if p.parent.name not in CODES]
    if missing:
        sys.exit(f"no ISO 639-3 code for: {', '.join(missing)}")
    for p in metas:
        out = ROOT / "languages" / p.parent.name / "meta.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(convert(json.loads(p.read_text(encoding="utf-8"))), ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(metas)} languages")


if __name__ == "__main__":
    main()
