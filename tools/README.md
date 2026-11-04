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
| `importers/cedict.py` | Imports the most frequent Chinese words, with CC-CEDICT pinyin and meanings, into `languages/chinese/vocab.jsonl`, tagging words already there instead of adding them twice. Needs `pip install "wordfreq[cjk]"`; the dictionary is fetched into `cache/`. |
| `importers/freq.py` | Core, common and rare frequency tags from wordfreq, for importers. |
| `importers/hangul.py` | Hangul to Revised Romanization, for importers. |
| `importers/freq_tags.py` | Adds a frequency tag (core, common, rare, from wordfreq) to every vocabulary word that has none, for each language wordfreq covers. Needs `pip install "wordfreq[cjk,mecab]"`. |
| `importers/jlpt_tanos.py` | Imports the JLPT N5 to N1 word lists into `languages/japanese/vocab.jsonl`, tagging words already there instead of adding them twice. Needs `pip install "wordfreq[mecab]"` for the frequency tags; the lists are fetched into `cache/`. |
| `importers/kana.py` | Kana to Hepburn romaji, for importers. |
| `importers/krdict.py` | Imports the graded words of the NIKL Basic Korean Dictionary into `languages/hangul/vocab.jsonl`, tagging words already there instead of adding them twice. Needs `pip install "wordfreq[mecab]"`; the dictionary is fetched into `cache/`. |
| `gen_reference.py` | Generates LanguageStudentDesk's `languages/<id>/reference.json` cards. `--check` reports drift. |
| `migrate/lsd_reference.py` | The one-time conversion of LanguageStudentDesk's reference cards to `reference@1`. |
| `check_characters.py` | Character tables: each script table's language and script match its folder and file name, script keys are unique across the repo, characters aren't listed twice and groups sit together; each tradition's readings sit with its language, and the shared CJK table holds exactly the characters some tradition reads. |
| `gen_characters.py` | Generates LanguageStudentDesk's `languages/<id>/characters.js`, `cjk/characters.js` and the kanji, hanzi and hanja reading files, and with `--kanji-app` SquirrelGo Kanji's `www/data/kanji.js`. `--check` reports drift. |
| `migrate/lsd_characters.py` | The one-time conversion of LanguageStudentDesk's character tables to `characters@1`, `cjk@1` and `cjk-readings@1` (needs node). |
| `importers/cjk_unihan.py` | Imports the hanzi and hanja readings, and the radicals and stroke counts of new shared CJK characters, from the Unihan database and the HSK 3.0 word lists (downloaded by hand; see the tool). |
| `check_strokes.py` | Stroke files: the set matches the file name, no character is listed twice, every stroke is path data a browser draws to the end and stays in the box, KanjiVG sets have a label per stroke, and stroke counts match the shared CJK table. The rendered check against a font runs in LanguageStudentDesk. |
| `gen_strokes.py` | Generates the SquirrelGo apps' stroke files (Alphabets, Kana, Kanji, Bopomofo, Klingon, and the Android copies apps commit) from `strokes/`. `--check` reports drift. |
| `migrate/lsd_strokes.py` | The one-time conversion of the apps' stroke files to `strokes@1` (needs node). |
| `check_alphabets.py` | SquirrelGo Alphabets courses: the id matches the file name, no character is taught twice, every character has strokes in `strokes/<id>.jsonl`, and joined letter forms only go with right-to-left scripts. |
| `gen_alphabets.py` | Generates SquirrelGo Alphabets' `www/data/<id>.js` course files from `alphabets/`. `--check` reports drift. |
| `migrate/lsd_alphabets.py` | The one-time conversion of SquirrelGo Alphabets' course files to `alphabet@1` (needs node). |
| `check_meaning.py` | The meaning matrix: meaning and sentence ids are unique, sentences and phrasings point at content meanings, and every language column renders known sentences with known meanings, carrying exactly each sentence's meanings. Reports unused meanings and sentences no column renders yet. |
| `gen_meaning.py` | Generates LanguageStudentDesk's `translation-learner/data/matrix.js` and one `<language>.js` column per file in `meaning/columns/`. `--check` reports drift. |
| `migrate/lsd_meaning.py` | The one-time conversion of LanguageStudentDesk's Translation Learner matrix and columns to `meaning@1`, `sentences@1`, `phrasings@1` and `columns@1` (needs node). |
| `check_vocab_links.py` | Links between vocabulary and meaning units: every vocab id is exactly an id in that language's `vocab.jsonl`, listed once and in its order, and every meaning is a content meaning. Reports column words whose card isn't linked to the token's meaning. |
| `gen_vocab_links.py` | Generates LanguageStudentDesk's `translation-learner/data/vocab-links.js` (`window.TL_VOCAB_LINKS`) from `meaning/vocab-links/`. `--check` reports drift. |
| `migrate/vocab_links_from_columns.py` | Seeds `meaning/vocab-links/<language>.jsonl` from the words the meaning columns use, keeping a link only when the card's English shares a word with the meaning's. `--glosses` also links starter-deck cards whose English is exactly a meaning's main English. The result is then reviewed by hand. |
| `export.py` | Exports language packs (see the repo README): every language, or the ones named, in every format or the ones given with `--format`, into `build/packs/` or `--out`. |
| `packs/` | The pack formats. `packs/__init__.py` reads a language folder once, and each format module writes it out and checks what it wrote. |
| `check_export.py` | Exports every language in every format into a temporary folder: every repo file is in the pack unchanged, each format's own check passes, and two exports are identical. |
