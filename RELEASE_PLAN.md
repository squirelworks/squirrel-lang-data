# Release plan

This repo's releases freeze the language data at a known version, so the apps
(LanguageStudentDesk, the SquirrelGo apps and squirrelator) can be tested
against content that doesn't move under them. The platform-wide rules are in
LanguageStudentDesk's `docs/RELEASES.md`: drafts only, the owner publishes,
tags are never moved or reused, releases are never deleted.

## Versions

`vMAJOR.MINOR.PATCH` on this repo's own tags.

- **PATCH** (v0.1.1): fixes found while testing the apps: wrong meanings,
  typos, wrong levels, broken references. No new content types.
- **MINOR** (v0.2.0): new content types, new languages, or big imports.
- **MAJOR**: a schema change that apps must be updated for (a `@2` schema).

## Released

- [x] **v0.1.0** (2026-11-04): the first frozen data release. Schemas,
      validators, `features.json`, language meta and registry, Aramaic,
      vocabulary, grammar, reference cards, the meaning matrix, the character
      tables, language-pack export, and the JLPT, NIKL and Chinese frequency
      imports.
- [x] **v0.1.1** (2026-11-04): fixes from app testing.
- [x] **v0.1.2** (2026-11-04): strokes and script courses moved in, frequency
      tags for 11 more languages, the first inflection tables, Anki and
      Yomitan packs.
- [x] **v0.1.3** (2026-11-04, `b6912a0`): full Japanese, Chinese and Korean
      matrix columns, Chinese HSK levels placed by hand, Korean grammar
      rewrites, Hangul stroke fixes. LanguageStudentDesk and squirrelator
      both pin this tag.

## Next: v0.1.4

Everything merged since v0.1.3 is collected in `release-notes/v0.1.4.md`
(still marked Draft): the code pack and its Japanese, Chinese, Korean and
Latin columns, Latin and English inflection tables, meta `cases` and
`order`, the review checklist and Content error form, the historical kana
lesson, and the grammar expansion to 72 lessons per language (24 for Tibetan and
Klingon), which is finished.

It's due when all of these hold and the owner says "release":

- [x] Grammar at 72 lessons for Amharic, Arabic, Armenian, Bengali, Burmese,
      Chinese, French, Georgian, German, Greek, Gujarati, Hebrew, Hindi,
      Italian, Japanese (73), Kannada, Khmer, Korean, Lao, Malayalam,
      Mongolian, Odia, Punjabi, Russian, Sinhala, Taiwanese, Tamil, Telugu
      and Thai (#66, #68–#92, #94), with level labels fixed (#93)
- [x] Latin grammar to 72 (#95)
- [x] Tibetan grammar 6 → 24 (#97)
- [x] Klingon grammar 10 → 24 (#98)
- [ ] CI green on `main`
- [ ] A PR that removes "Draft." from `release-notes/v0.1.4.md` and checks
      every bullet against what merged, with nothing else in it
- [ ] **Draft release** run by hand with `v0.1.4`; the owner publishes
- [ ] Pin-bump PRs in LanguageStudentDesk (with the `data-pin` label) and
      squirrelator, one each

Left out on purpose: more grammar for Aramaic, Cherokee, Inuktitut, Manipuri
and Tamazight. Their lessons are all source-cited, and adding more needs
published sources. They don't hold v0.1.4 back.

## After v0.1.4

- [ ] Code-pack columns for the other tested languages (#56)
- [ ] Fill the meaning-matrix columns that have 20 to 42 of the 89 rows, then
      add columns for the 22 languages without one (squirrelator#26). Latin,
      Greek and Russian now render all 103 rows, and French, German and
      Italian have new full columns; Arabic, Hindi, Hebrew, Thai, Georgian,
      Armenian, Bengali, Tamil and Klingon are still partial.
- [x] The Syriac alphabet for Aramaic (LanguageStudentDesk#201): a 22-letter
      Estrangela course in `alphabets/syriac.json` with drafted strokes
- [ ] Recorded reviews (`REVIEW.md`) for every language (see `REVIEWING.md`)
- [ ] v0.2.0 (MINOR): programming courses and keyword maps (`programming/`),
      character variants (`variants/`) and the first regional and historical
      varieties (LanguageStudentDesk#200)

`main` stays open between releases. LanguageStudentDesk and squirrelator move
their `data/` pin only to a tagged release, never to an untagged commit, and
each move is its own PR.

## How a release is made

1. When the checklist above is done, a PR adds `release-notes/<version>.md`
   (what's in it, in plain words, and what was left out). Nothing else goes
   in that PR.
2. After it merges, the **Draft release** workflow is run by hand with the
   version. It runs every check, exports the language packs, and makes a
   **draft** GitHub Release targeting that `main` commit, with the packs and
   a `SHA256SUMS.txt` attached. It never creates or moves a tag itself.
3. The owner clicks **Publish**. Publishing creates the tag.
