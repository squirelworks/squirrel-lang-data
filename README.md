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
