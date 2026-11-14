# Armenian review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 69b3888 | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 142 words (no TODO/??/stray separators; every word has a reading); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/armenian/characters/` pack (alphabet chart + strokes/armenian.jsonl 77 entries instead; stroke order not visually checked); meaning column on main (103 renderings). Matrix-column fills in parallel branches may still be unreviewed. | All 142 vocab words still lack `level`/`freq` tags. No characters@1 pack under the language folder yet (meta still lists `characterKeys: armenian`). Alphabet chart letter `և` uses itself as the example word. Vocab-links info: numbers one/three/ten. Meanings, Eastern Armenian romanization, grammar pedagogy, and stroke order still need a human Armenian speaker. | — |
