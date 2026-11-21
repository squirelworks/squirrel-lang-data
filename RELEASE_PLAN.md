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
      rewrites, Hangul stroke fixes.
- [x] **v0.1.4** (2026-11-05, `d5e05a4`): the code pack and its columns,
      Latin, English and Klingon inflection tables, and the grammar
      expansion to 72 lessons.
- [x] **v0.1.5** (2026-11-13, `ffd03a7`): French, German and Italian matrix
      columns, Latin, Greek and Russian filled to every row, English
      contractions and `@partitive` (#105, #109), and the Syriac
      (Estrangela) alphabet (#106). LanguageStudentDesk
      (squirelworks/LanguageStudentDesk#319) and squirrelator (squirelworks/squirrelator#49) both pin
      this tag.

## Known caveats in v0.1.5

- **The Syriac strokes are a machine draft** from Noto Sans Syriac. They
  pass the stroke checks but no person has compared them with a writing
  primer, and `languages/aramaic/` has no `REVIEW.md` yet.
- **The new French, German and Italian columns, and the Latin, Greek and
  Russian fills, were written for this project.** They pass the validators
  and squirrelator's round trip; no native speaker has reviewed them, and
  the existing `REVIEW.md` logs for those languages predate them.

## Next: v0.1.6

Everything merged since v0.1.5 is collected in `release-notes/v0.1.6.md`
(still marked Draft): Arabic, Hindi, Hebrew and Thai filled (#111),
Bengali, Armenian, Georgian and Tamil filled (#112), Klingon filled
including the code pack (#113), the 21 kana/kanji stroke redraws (#114),
mechanical reviews for Armenian/Bengali/Georgian/Tamil/Klingon (#116),
Gujarati/Kannada/Malayalam/Telugu columns (#117), `gen_features.py`
`--check` payload-only (#118), Burmese/Khmer/Lao/Mongolian columns
(#119), Odia/Punjabi/Sinhala/Tibetan columns (#121),
Amharic/Cherokee/Taiwanese columns (#123),
Aramaic/Manipuri/Tamazight columns (#125), Inuktitut column (#127), and
mechanical reviews for Gujarati/Kannada/Malayalam/Telugu/Burmese/Khmer
(#128). Syriac Estrangela stroke review (#129) and Tifinagh ⴰ redraw
(#131) are merged. Programming courses (#140–#178), Math/Electronics
trees (#147–#150), and the Inuktitut `?` `@question` cleanup sit on
`main` too; tip SHA is refreshed when the notes finalize PR lands.

It's due when all of these hold and the owner says "release":

- [x] Arabic / Hindi / Hebrew / Thai matrix fills and mechanical reviews
      (#111)
- [x] Bengali / Armenian / Georgian / Tamil matrix fills (#112)
- [x] Klingon matrix fill and code-pack rows (#113)
- [x] Kana and kanji stroke redraws for the final-frame check (#114)
- [x] Mechanical REVIEW.md for Armenian, Bengali, Georgian, Tamil, Klingon
      (#116)
- [x] Gujarati / Kannada / Malayalam / Telugu columns (#117)
- [x] `gen_features.py --check` ignores header SHA drift (#118)
- [x] Burmese / Khmer / Lao / Mongolian columns (#119)
- [x] Odia / Punjabi / Sinhala / Tibetan columns (#121)
- [x] Amharic / Cherokee / Taiwanese columns (#123)
- [x] Aramaic / Manipuri / Tamazight columns (#125)
- [x] Inuktitut column (#127)
- [x] Mechanical REVIEW.md for Gujarati, Kannada, Malayalam, Telugu,
      Burmese, Khmer (#128)
- [x] Syriac Estrangela stroke review (#129)
- [x] Tifinagh ⴰ redraw (#131)
- [x] Mechanical REVIEW.md for twelve more matrix languages (#132)
- [ ] CI green on `main`
- [ ] A PR that removes "Draft." from `release-notes/v0.1.6.md` and checks
      every bullet against what merged, with nothing else in it
- [ ] **Draft release** run by hand with `v0.1.6`; the owner publishes
- [ ] Pin-bump PRs in LanguageStudentDesk (with the `data-pin` label) and
      squirrelator, one each. The Desk's should also drop the 21 cleared
      kana/kanji entries from strokecheck `baseline.json`
      (squirelworks/LanguageStudentDesk#188).

Open **few, sizeable PRs, one theme each, and merge them one after
another**; batch several languages in one PR where the theme is the same.

## After v0.1.6

Still PATCH-sized unless noted:

- [x] Review the 22 Syriac strokes against a published primer (#129).
- [x] Tifinagh ⴰ redraw (#131). Hangul ㅇ cleared on the Desk via
      min_coverage (squirelworks/LanguageStudentDesk#326). Drop
      kana/kanji and `tifinagh.ⴰ` from baseline on the pin bump
      (squirelworks/LanguageStudentDesk#188).
- [ ] Recorded reviews (`REVIEW.md`) for the languages without one, and a
      dated entry for the new and filled columns (see `REVIEWING.md`;
      squirelworks/LanguageStudentDesk#198). Mechanical-only entries now
      also cover Gujarati through Khmer (#128) and Amharic through Tibetan
      (#132).
- [ ] Meaning-matrix columns: every language folder now has one (through
      #127). Further fills are row quality and native-speaker review, not
      missing files.

v0.2.0 (MINOR):

- [ ] Programming courses and keyword maps (`programming/`), so the
      Programming Learner and squirrelator's code generators share them
      (squirelworks/LanguageStudentDesk#195, #196). Schemas
      (`programming-course@1`, `programming-catalog@1`), `programming/catalog.json`
      and a pilot `programming/slick/` course start the move; remaining courses
      follow a few per PR.
- [ ] Character variants (`variants/`) from Unihan, with traditional and
      simplified Chinese linked both ways (squirelworks/LanguageStudentDesk#200).
- [ ] The first regional variety end to end: Cantonese (Jyutping)
      (squirelworks/LanguageStudentDesk#200).
- [ ] Serto and Madnhaya Syriac shapes, after the Estrangela review
      (squirelworks/LanguageStudentDesk#201).

After each tag: one pin-bump PR in LanguageStudentDesk (with the `data-pin`
label), then one in squirrelator.

`main` stays open between releases. LanguageStudentDesk and squirrelator move
their `data/` pin only to a tagged release, never to an untagged commit, and
each move is its own PR.

## Dictionary packs: a separate release track

Dictionary packs (#181) release on their own, independent of the data tags
above and of the SquirrelGo app releases. Apps download or update packs
without an app update; the Japanese Dictionary also bundles one.

- **Tags:** `dictionaries-vMAJOR.MINOR.PATCH`. MAJOR: a `dictpack@N` change
  apps must be updated for. MINOR: new packs, languages or sources. PATCH:
  source refreshes (a new JMdict) and fixes.
- **Assets:** `dictionaries.json` (the manifest: each pack's id, definition
  language, tier, format, version, sizes, SHA-256 and sources), one
  `dict-<id>.sqlite.gz` per pack, the starter packs and `SHA256SUMS.txt`.
- **Made by** a hand-started `dictionary-packs.yml` workflow (#186) that
  fetches the sources pinned in `tools/dictionaries/sources.json`, builds and
  checks the packs, and makes a **draft**. The owner publishes. Never marked
  latest, so `releases/latest` stays the data release. Tags are never moved
  or reused, releases never deleted.
- **Notes:** `release-notes/dictionaries-v<version>.md`, naming source
  versions and pack sizes, in its own PR before the run.
- Data releases don't attach dictionary packs, and a pack release doesn't
  need a data tag; it records the `main` commit it was built from.

## How a release is made

1. When the checklist above is done, a PR adds `release-notes/<version>.md`
   (what's in it, in plain words, and what was left out). Nothing else goes
   in that PR.
2. After it merges, the **Draft release** workflow is run by hand with the
   version. It runs every check, exports the language packs, and makes a
   **draft** GitHub Release targeting that `main` commit, with the packs and
   a `SHA256SUMS.txt` attached. It never creates or moves a tag itself.
3. The owner clicks **Publish**. Publishing creates the tag.
