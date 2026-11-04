# Sources

Every outside source this repo's content comes from, with its license and the
attribution it asks for. A PR that imports content adds its source here. The
repo's content as a whole is under CC BY-SA 4.0 (see `LICENSE`), so a source is
only imported when its license fits that.

| Source | Used for | License | Attribution |
|---|---|---|---|
| Wiktionary | Lemmas and grammar notes behind the grammar courses (examples are original) | CC BY-SA 4.0 | Wiktionary contributors, https://www.wiktionary.org |
| Wikipedia and Simple English Wikipedia | Grammar overviews behind the grammar courses (examples are original) | CC BY-SA 4.0 | Wikipedia contributors, https://www.wikipedia.org |
| Wikibooks, "Modern Meitei/Common phrases" | Manipuri grammar course phrases | CC BY-SA 4.0 | Wikibooks contributors, https://en.wikibooks.org/wiki/Modern_Meitei |
| FSI Amharic Basic Course; FSI Italian | Amharic and Italian grammar courses | Public domain (US government work) | Foreign Service Institute |
| Allen and Greenough, *New Latin Grammar* (1903) | Latin grammar course | Public domain | via Perseus and Dickinson College Commentaries |
| A. J. Primrose, *A Manipuri Grammar, Vocabulary, and Phrase Book* (1888) | Manipuri grammar course | Public domain | |
| Jonathan Waller, JLPT Resources (tanos.co.uk) | Japanese JLPT N5 to N1 vocabulary decks and level tags | CC BY | Jonathan Waller, http://www.tanos.co.uk/jlpt/ |
| yomitan-jlpt-vocab (Stephen Kraus), the cleaned-up copy of Waller's lists the import reads | Japanese JLPT vocabulary (common spellings checked against JMdict) | CC BY-SA 4.0 | https://github.com/stephenmk/yomitan-jlpt-vocab |
| National Institute of Korean Language, Basic Korean Dictionary (한국어기초사전) | Korean graded vocabulary decks (beginner, intermediate, advanced) and level tags | CC BY-SA 2.0 KR (adaptations shared under CC BY-SA 4.0, as it allows) | 국립국어원 한국어기초사전, https://krdict.korean.go.kr, read via https://github.com/spellcheck-ko/korean-dict-nikl-krdict |
| JLPT official site | Level summaries and FAQ by the Japan Foundation and JEES: short quotations of the official JLPT level descriptions on the Japanese reference card | Quoted with attribution; not under this repo's license | https://www.jlpt.jp/e/about/levelsummary.html, https://www.jlpt.jp/e/faq/ |
| CC-CEDICT (MDBG and contributors) | Chinese pinyin and English meanings for the most-common-words decks | CC BY-SA 4.0 | CC-CEDICT, https://cc-cedict.org, read from the cc-cedict npm package |
| TOPIK level descriptors | The National Institute for International Education's description of each TOPIK level: short quotations on the Korean reference card | Quoted with attribution; not under this repo's license | Read via https://en.wikipedia.org/wiki/Test_of_Proficiency_in_Korean (official site: https://www.topik.go.kr) |
| Unicode Han Database (Unihan), Unicode 17.0 | Hanzi pinyin, meanings and traditional forms; hanja education readings and meanings; radicals and stroke counts of CJK characters that are not kanji | Unicode License v3 | Unicode, Inc., https://www.unicode.org/reports/tr38/ |
| complete-hsk-vocabulary (drkameleon) | Which characters belong to HSK 3.0 levels 1 to 6, and the lowest level each appears at | MIT | https://github.com/drkameleon/complete-hsk-vocabulary |
| HSK level standard | The 2021 grading standard's description of its three stages and nine levels (a short quotation) and the official word count per level, on the Chinese reference card | Quoted with attribution; the counts are facts | https://institut-confucius.univ-larochelle.fr (announcement, 31 March 2021); counts via https://en.wikipedia.org/wiki/Hanyu_Shuiping_Kaoshi |
| CEFR global scale | The Council of Europe's Common European Framework of Reference (2001), global scale: the first sentence of each level, quoted on the French, German, Italian, Greek and Russian reference cards and grammar notes | Quoted with attribution; the Council of Europe holds the copyright of the scales; not under this repo's license | https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions, https://rm.coe.int/168045b15e |
| KanjiVG (Ulrich Apel), release r20250816 | Stroke order for kanji and kana (`strokes/kanji.jsonl`, `kana.jsonl`, `hiragana.jsonl`, `katakana.jsonl`) | CC BY-SA 3.0 | Copyright (C) 2009-2024 Ulrich Apel, https://kanjivg.tagaini.net |
| Noto fonts (Google and contributors) | Glyph shapes the other scripts' strokes were drafted over (by LanguageStudentDesk's SquirrelGo-Apps/tools/strokegen) and then checked and redrawn by hand | SIL Open Font License 1.1 | https://fonts.google.com/noto |
| wordfreq (Robyn Speer and contributors) | Frequency tags (core, common, rare) on vocabulary | CC BY-SA 4.0 (data) | https://github.com/rspeer/wordfreq |

Content written for this project is marked as original in its file and isn't
listed here.

The kanji readings (`languages/japanese/characters/kanji.jsonl`) came from
LanguageStudentDesk's Jōyō table, which doesn't record where they first came
from; their notes say so.

Some courses also checked facts (no text) against copyrighted grammars, which
their `notes` cite as further reading: S. L. Chelliah, *A Grammar of Meithei*
(1997), and N. Sanatombi Devi, "Earlier Works on Tense and Aspect in Manipuri
(Meeteilon)", *Language in India* 16:10 (2016).

Apps that ship this data show these credits, for example on an About screen.
