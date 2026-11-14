# Arabic review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 6af9c22 | Composer (mechanical) | Mechanical only (not a native speaker): `tools/check_*.py` pass for this tree; vocab lint over all 300 words (no TODO/??/stray separators; every word has reading + level/freq); grammar structure on all 72 lessons (sections with examples+romanization, drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; `characters/arabic.jsonl` (28) example containment; strokes file present (38) but not visually ordered; meaning column on main (34 renderings). Matrix-column fills in parallel branches may still be unreviewed. | `ا` example is `أحمد` (hamza-alif أ, not bare ا). Vocab-links info: a few column words not linked to that meaning (e.g. numbers one/ten). Meanings, readings, grammar pedagogy, and stroke order still need a human Arabic speaker. | — |
