# Kannada review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | c3f78fb | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 115 words (no TODO/??/stray separators; every word has a reading); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/kannada/characters/` pack (alphabet chart + strokes/kannada.jsonl 63 entries instead; stroke order not visually checked); meaning column on main (103 renderings). No `meaning/vocab-links/kannada.jsonl` yet. | All 115 vocab words still lack `level`/`freq` tags. No characters@1 pack under the language folder yet (meta still lists `characterKeys: kannada`). Alphabet: halant `ಕ್`, letters `ಙ`/`ಞ`/`ಢ`/`ಷ` have empty examples; vowel-sign lessons use carrier `ಕ` (expected per REVIEWING.md). Meanings, simplified romanization, grammar pedagogy, matrix renderings, and stroke order still need a human Kannada speaker. | — |