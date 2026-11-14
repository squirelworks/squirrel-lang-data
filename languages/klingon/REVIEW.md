# Klingon review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 69b3888 | Composer (mechanical) | Mechanical only (not a fluent speaker): `tools/check_*.py` pass for this tree; vocab lint over all 251 words (no TODO/??/stray separators; words are Latin transcription — no separate `reading` field); grammar structure on all 24 lessons (drills with answer∈options and `why`); random sample of 6 drills + 30 vocab rows for shape; `characters/klingon.jsonl` (26) present — examples are Latin romanization, not pIqaD PUA glyphs, so glyph-in-example containment does not apply; strokes/klingon.jsonl 36 entries (stroke order not visually checked); meaning column on main (103 renderings). Matrix-column fills in parallel branches may still be unreviewed. | All 251 vocab words still lack `level`/`freq` tags. Grammar: three sections are prose-only with no examples (`shape` “Verbs that describe”; `with-object` “Patterns that help”; `empty` they→him/her note). Alphabet chart is codepoint/roman based (no `char` glyph field on rows). Vocab-links info: many column words not linked to that meaning (numbers, questions, qualities, verbs, etc.). Meanings, Okrand romanization fidelity, grammar pedagogy, and stroke order still need a human Klingon-competent reviewer. | — |
