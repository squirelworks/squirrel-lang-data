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

## v0.1.0: the first frozen data release

This is the point where the data is "crystallised" and attention moves to
testing the apps for usability and accuracy. It's due when everything below
is on `main` and CI is green there.

Already on `main`:

- [x] Schemas, validators and formatter (#3); `features.json` (#1, #6)
- [x] Language meta and registry generator (#4), Aramaic (#5, #8, #11)
- [x] Vocabulary (#7), grammar (#9) and reference cards (#10)
- [x] Language-pack export (#12)
- [x] JLPT vocabulary (#13), Korean NIKL vocabulary (#15), Chinese frequency
      vocabulary (#17)
- [x] Korean and Chinese grammar levels (#19, #21)

Merged since the plan was written:

- [x] Meaning matrix moved from LanguageStudentDesk (#14)
- [x] Japanese grammar levels and JLPT plan (#16)
- [x] JLPT, TOPIK and HSK level reference cards (#18, #20, #22)
- [x] Aramaic reference cards (#23)

Also in v0.1.0, because it merged before the freeze: the character tables
(#25).

Not waited for: strokes, variants and programming courses. They go to v0.2.0.
Strokes move only after LanguageStudentDesk's stroke checks pass on them. Until content moves here,
the apps keep reading it from their own repo.

PRs opened after this list was written don't hold v0.1.0 back. They go into
the next release.

## After v0.1.0

- `main` stays open; new content keeps landing there for v0.2.0.
- LanguageStudentDesk and squirrelator pin their `data/` submodule to the
  `v0.1.0` commit while the apps are tested, and only move it to another
  release (v0.1.x or v0.2.0), never to an untagged commit, while testing.
- Problems found in testing are fixed on `main` and shipped as v0.1.1,
  v0.1.2, and so on.

## How a release is made

1. When the checklist above is done, a PR adds `release-notes/<version>.md`
   (what's in it, in plain words, and what was left out). Nothing else goes
   in that PR.
2. After it merges, the **Draft release** workflow is run by hand with the
   version. It runs every check, exports the language packs, and makes a
   **draft** GitHub Release targeting that `main` commit, with the packs and
   a `SHA256SUMS.txt` attached. It never creates or moves a tag itself.
3. The owner clicks **Publish**. Publishing creates the tag.
