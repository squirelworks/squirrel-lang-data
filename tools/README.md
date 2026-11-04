# tools

Checks, formatters, generators and importers. Everything here runs on the
Python standard library, except importers that say what they need.

```
tools/check_all.sh          # every check CI runs (each tools/check_*.py)
python3 tools/fmt.py        # format every content file in place
```

| Tool | What it does |
|---|---|
| `check_schema.py` | Every content file names a schema in `schemas/` and follows it. JSONL files are checked line by line against the schema's `header` and `entry`. |
| `check_format.py` | Every content file is formatted the way `fmt.py` writes it. |
| `check_meta.py` | Languages and varieties: ids match folders and are unique, every variety's parent chain ends at its language, and each language lists its varieties. |
| `check_vocab.py` | Vocabulary: words sit in listed decks in header order, ids are unique, readings are given for every word or none. Reports words with no level or frequency tag yet. |
| `check_grammar.py` | Grammar courses: lesson ids are unique, drill answers are among their options, planned points link to real lessons, generated drills have their data. Reports lessons with no level yet. |
| `check_reference.py` | Reference cards: ids are unique, table rows match their head, card sources are in `SOURCES.md`. Reports cards with no level yet. |
| `check_tools.py` | The tools' own tests in `tests/`. |
| `fmt.py` | Formats content files: keys in schema order, two-space indent, short lists on one line, JSONL one entry per line. |
| `schema.py` | The JSON Schema validator the checks use. It rejects any keyword it doesn't support, so a schema can't be skipped silently. |
| `lib.py` | Shared helpers. |
| `gen_registry.py` | Generates LanguageStudentDesk's `languages/registry.js` and each `languages/<id>/meta.json` from the language meta here. `--check` reports drift. |
| `migrate/lsd_meta.py` | The one-time conversion of LanguageStudentDesk's language meta to `meta@1`, kept so the move can be repeated and checked. |
| `gen_vocab.py` | Generates LanguageStudentDesk's `languages/<id>/vocab.js` decks from `vocab.jsonl`. `--check` reports drift. |
| `migrate/lsd_vocab.py` | The one-time conversion of LanguageStudentDesk's `vocab.js` decks to `vocab@1` (needs node). |
| `gen_grammar.py` | Generates LanguageStudentDesk's `languages/<id>/grammar.js` courses from `grammar.json`. `--check` reports drift. |
| `migrate/lsd_grammar.py` | The one-time conversion of LanguageStudentDesk's `grammar.js` courses to `grammar@1` (needs node). |
| `importers/jlpt_tanos.py` | Imports the JLPT N5 to N1 word lists into `languages/japanese/vocab.jsonl`, tagging words already there instead of adding them twice. Needs `pip install "wordfreq[mecab]"` for the frequency tags; the lists are fetched into `cache/`. |
| `importers/kana.py` | Kana to Hepburn romaji, for importers. |
| `gen_reference.py` | Generates LanguageStudentDesk's `languages/<id>/reference.json` cards. `--check` reports drift. |
| `migrate/lsd_reference.py` | The one-time conversion of LanguageStudentDesk's reference cards to `reference@1`. |
| `export.py` | Exports language packs (see the repo README): every language, or the ones named, in every format or the ones given with `--format`, into `build/packs/` or `--out`. |
| `packs/` | The pack formats. `packs/__init__.py` reads a language folder once, and each format module writes it out and checks what it wrote. |
| `check_export.py` | Exports every language in every format into a temporary folder: every repo file is in the pack unchanged, each format's own check passes, and two exports are identical. |
