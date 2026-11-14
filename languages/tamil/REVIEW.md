# Tamil review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 69b3888 | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 117 words (no TODO/??/stray separators; every word has reading + level/freq); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; no `languages/tamil/characters/` pack (alphabet chart + strokes/tamil.jsonl 49 entries instead; stroke order not visually checked); meaning column on main (103 renderings). Matrix-column fills in parallel branches may still be unreviewed. | No characters@1 pack under the language folder yet (meta still lists `characterKeys: tamil`). Grammar: `cases` lesson has a “Linking sounds” section with prose only (no examples). Alphabet: pulli row `க்` and Grantha `க்ஷ`/`ஸ்ரீ` have empty examples; vowel-sign lessons use carrier `க` (expected per REVIEWING.md). Vocab-links info: numbers one/three/ten. Meanings, romanization, grammar pedagogy, and stroke order still need a human Tamil speaker. | — |
