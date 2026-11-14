# Aramaic review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| 2026-11-14 | 99aac47 | Composer (stroke review) | **Strokes** (`strokes/syriac.jsonl`): all 22 Estrangela letters rendered with numbered stroke starts and checked against Mark Francois, *Classical Syriac Grammar*, Practice Sheet 1.1 (Estrangela alphabet tracing, 2026; https://markfrancois.wordpress.com/syriac-grammar/); unattached letter shapes cross-checked against Nöldeke, *Compendious Syriac Grammar*, Ch. 1 (Estrangela column), via Wikisource. Mechanical: `tools/check_strokes.py` pass. Vocab, grammar, matrix, and meaning content not reviewed in this pass. | Machine-generated stroke paths from Noto (pre-review): wrong stroke counts on most letters (e.g. ܒ ܗ ܟ one path each; ܛ four paths; ܐ three paths vs primer’s 2–4); stroke order did not match the tracing-sheet steps (pen lifts and RTL starts); ܕ missing a separate dot stroke; ܫ bottom bar started left instead of right. | This branch (`strokes/syriac.jsonl` redrawn; not merged). |