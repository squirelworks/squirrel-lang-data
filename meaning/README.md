# meaning

The shared units of meaning, and the sentences every language renders from
them. The Translation Learner checks a translation by matching these units,
and the meaning network is trained on them.

| File | Schema | What it holds |
|---|---|---|
| `meanings.jsonl` | `meaning@1` | Each unit of meaning once, language-neutral: content meanings with the English that may carry them, and grammar meanings (ids starting with `@`) with a label. |
| `sentences.jsonl` | `sentences@1` | The rows: model English, other natural English, and the content meanings every rendering must carry. |
| `phrasings.jsonl` | `phrasings@1` | English that carries a meaning only next to others ("take" is *go* next to *bus*), or lets English leave one out. |
| `columns/<language>.jsonl` | `columns@1` | One language's renderings of the rows, token by token, each token pointing back at meanings. |
| `vocab-links/<language>.jsonl` | `vocab-links@1` | Which content meanings each card in `languages/<language>/vocab.jsonl` carries, by vocab id, so vocabulary, translation and the network share the same units. |

All of it was written for this project. `tools/check_meaning.py` checks that
every column carries exactly each sentence's meanings, and
`tools/gen_meaning.py` writes the files the Translation Learner loads.
`tools/check_vocab_links.py` checks the vocabulary links against the decks and
meanings, and `tools/gen_vocab_links.py` writes them out for LanguageStudentDesk.
