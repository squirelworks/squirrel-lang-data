# Mongolian review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 361c55c | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 143 words (no TODO/??/stray separators; every word has a reading); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/mongolian/characters/` pack; alphabet chart + strokes/mongolian.jsonl 28 entries instead; stroke order not visually checked; meaning column on main (103 renderings). | All 143 vocab words still lack `level`/`freq` tags. No characters@1 pack under the language folder yet (meta still lists `characterKeys: mongolian`). Meanings, romanization, grammar pedagogy, matrix renderings, and stroke order still need a human speaker. | — |
