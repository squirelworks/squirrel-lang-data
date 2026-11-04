# squirrel-lang-data

The language content for the SquirrelGo platform: LanguageStudentDesk, the
SquirrelGo apps and squirrelator. Each of those repos pulls this one in as a git
submodule at `data/`, pinned to a commit, and builds from it. None of them keeps
its own copy.

## Layout

```
languages/<id>/      a language: meta, grammar, vocabulary, references,
                     characters, strokes and varieties
variants/            links between character forms (traditional and simplified,
                     shinjitai and kyūjitai, and so on)
meaning/             the meaning network
programming/<id>/    programming courses and keyword maps
features.json        every user-facing feature switch
schemas/             a versioned JSON Schema for every content type
tools/               importers, validators, generators and checks
SOURCES.md           every source, with its license and attribution
```

Content arrives one type at a time, so some folders don't exist yet.

## Rules for content

- The source of truth is plain data. Records (a language's meta, a grammar
  course, a reference card set, `features.json`) are JSON. Big lists (vocabulary,
  character tables, strokes, corpora) are JSONL, one entry per line, so a diff
  shows exactly which entries changed. Apps generate the files they ship (JS
  bundles, Android assets, Python modules) at build time with the generators in
  `tools/`.
- Every content file names the schema version it follows, and CI checks it. A
  JSON file has a top-level `"schema": "<type>@<version>"`. A JSONL file's first
  line is a header object with that field, and every line after it is one entry.
- Imported content comes from a script in `tools/`, so it can be regenerated, and
  its source and license are listed in `SOURCES.md`.
- No app code, UI or build output lives here. Large downloaded or generated files
  are fetched by tools and ignored by git.

## Using it from another repo

```
git submodule add https://github.com/squirelworks/squirrel-lang-data data
git submodule update --init          # after cloning a repo that uses it
```

Moving the pinned commit forward is its own PR in that repo.

## Language packs

`tools/export.py` exports each language's content as a pack: everything in
`languages/<id>/`, its varieties, the license and the credits, in a form other
programs can open without knowing this repo's layout. It needs only Python 3.

```
python3 tools/export.py                  # every language, every format, into build/packs/
python3 tools/export.py japanese latin   # just these languages
python3 tools/export.py --format folder  # just one format
python3 tools/export.py --out ~/packs    # write somewhere else
python3 tools/export.py --list           # the languages and formats
```

Formats:

- **folder**: `build/packs/<id>/`, the content as plain files split by type.
  The repo's own files are copied unchanged (`vocab/vocab.jsonl`,
  `grammar/grammar.json` and so on), next to easier views of them: one
  tab-separated file per vocabulary deck (`vocab/decks/`) and one JSON file per
  grammar lesson (`grammar/lessons/`). `pack.json` lists every file, the data
  commit, and how many words or lessons each part holds. Content types the
  export has no special view for are still copied, so nothing is left out.

Packs are build output, so `build/` is ignored by git. CI exports every
language in every format on each pull request and checks the packs against the
repo, without keeping them.

## Contributing

Every change goes through a pull request. See `AGENTS.md` and
`.github/MERGING.md`.

## License

- **Content** (everything outside `tools/`): [CC BY-SA 4.0](LICENSE). You may
  use, share and adapt it, including in commercial apps, as long as you credit
  the sources and share adaptations of the data under the same license. Shipping
  the data inside an app doesn't put the app's own code under CC BY-SA; the app
  shows the credits from `SOURCES.md` (for example on an About screen).
- **Code** in `tools/`: [MIT](tools/LICENSE).
- **Sources:** each one is listed in `SOURCES.md` with its own license. Only
  sources whose license fits CC BY-SA 4.0 are imported (for example CC BY,
  CC BY-SA 3.0 or 4.0, CC0, the Unicode license). Material under a license that
  doesn't fit, such as the Arphic Public License, stays out unless it's kept in
  its own folder under its own license and listed as such.
