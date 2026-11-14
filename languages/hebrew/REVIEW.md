# Hebrew review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 6af9c22 | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 146 words (no TODO/??/stray separators; every word has reading + level/freq); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/hebrew/characters/` pack (alphabet chart + strokes/hebrew.jsonl 41 entries instead; stroke order not visually checked); meaning column on main (55 renderings). Matrix-column fills in parallel branches may still be unreviewed. | No characters@1 pack under the language folder yet (meta still lists `characterKeys: hebrew`). Alphabet chart has a few dagesh/shin-dot rows whose marked letter form does not literally match the pointed example (Unicode mark composition). Vocab-links info: numbers one/three/ten. Meanings, transliteration, grammar pedagogy, and stroke order still need a human Hebrew speaker. | — |
