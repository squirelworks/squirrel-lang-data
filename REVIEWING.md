# Reviewing a language

CI checks shape: schemas, duplicates, missing fields, broken links, stroke
counts. It can't tell you that a meaning is wrong, a drill teaches nothing or a
stroke goes the wrong way. A human review (or an agent working like one) does
that. This file is the checklist. Each review is logged in the language's
folder, in `languages/<id>/REVIEW.md`.

## How to run a review

1. Note the data commit you're reviewing (`git rev-parse --short HEAD`).
2. Work through the sections below that apply to the language. You don't have
   to do every section in one sitting; log what you covered.
3. File each problem as an issue with the **Content error** template, or fix it
   in a PR. One seam per PR, as in `AGENTS.md`.
4. Add a row to `languages/<id>/REVIEW.md` (create it from the template at the
   end of this file) with what you checked and what you found.

Sample at random. Look at the content the way the apps show it to a learner,
not only as JSON.

## Vocabulary (`vocab.jsonl`)

- [ ] Read 30 random words from each deck. Is each meaning right, and is it
      the sense a learner meets first?
- [ ] Readings and romanization match the word (kana, pinyin with tones,
      transliteration).
- [ ] No placeholders or editor's notes ("TODO", "??", "same as …?"), and no
      stray separators at the start or end of a meaning.
- [ ] Level tags (`level`) are estimates placed against the official
      descriptions, never copied from an unlicensed list. The deck or reference
      card says they're estimates.
- [ ] Hand-written decks: the words fit the deck's topic and the topic's level.

## Grammar (`grammar.json`)

- [ ] Every lesson has a real explanation and examples with a reading or
      romanization. Look for stubs: one example, a "…" reading, a section that
      just names the pattern.
- [ ] Fill in every fill-in drill with its answer and read the sentence. The
      blank must not already contain the answer (온＿다고 + 다고 = 온다고다고).
- [ ] Each drill tests the lesson's point. No filler drills ("Pattern level",
      "Korean puts… verb last") and no filler options ("opposite", "noun only").
- [ ] Only one option is right. Watch for a distractor that is also correct
      (예 as well as 네 for "yes").
- [ ] No two lessons teach the same thing under different ids.
- [ ] Each lesson's level and its "(about TOPIK/HSK/JLPT/CEFR N)" estimate are
      plausible against the official level descriptions.

## Characters and alphabets (`characters/`, `alphabets/`)

- [ ] Every example word contains its letter (decompose syllable blocks:
      Hangul jamo, Indic vowel signs). Vowel-sign lessons that use a carrier
      consonant are expected.
- [ ] Romanization and sound hints match the script's usual system (RR,
      Hepburn, pinyin, IAST, RTGS…).
- [ ] Groupings and lesson notes are true ("combined vowels wrap under and to
      the right", not "stand to the right").

## Strokes (`strokes/<set>.jsonl`)

- [ ] Render the set with each stroke's start numbered and check the order
      against the script's standard order (Hangul: top to bottom, left to
      right; kana: as taught in Japanese schools).
- [ ] Stroke count is right. Font-derived paths can leave a stub (ㅅ with
      three strokes) or join two strokes across a letter (ㅆ).

## References (`reference.json`)

- [ ] Every claim about an official standard (JLPT, TOPIK, HSK, CEFR) quotes
      or cites the official wording and source.
- [ ] Tables agree with the grammar and vocabulary they describe.

## Log template

Copy this into `languages/<id>/REVIEW.md`:

```markdown
# <Language> review log

The checklist is in REVIEWING.md at the repo root. Newest first.

| Date | Data commit | Reviewer | Covered | Found | Fixed in |
|---|---|---|---|---|---|
| YYYY-MM-DD | abc1234 | name | sections and sample sizes | what was wrong | #PR, #issue |
```
