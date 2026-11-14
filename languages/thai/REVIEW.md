# Thai review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 6af9c22 | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 139 words (no TODO/??/stray separators; every word has a reading); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/thai/characters/` pack (alphabet chart + strokes/thai.jsonl 68 entries instead; stroke order not visually checked); meaning column on main (55 renderings). Matrix-column fills in parallel branches may still be unreviewed. | All 139 vocab words still lack `level`/`freq` tags. No characters@1 pack under the language folder yet (meta still lists `characterKeys: thai`). Alphabet vowel lessons use a carrier consonant (expected per REVIEWING.md); obsolete ฃ/ฅ examples use the paired modern letter. Vocab-links info: numbers one/three/ten. Meanings, RTGS readings/tones, grammar pedagogy, and stroke order still need a human Thai speaker. | — |
