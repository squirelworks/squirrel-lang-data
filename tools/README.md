# tools

Checks, formatters, generators and importers. Everything here runs on the
Python standard library.

```
tools/check_all.sh          # every check CI runs (each tools/check_*.py)
python3 tools/fmt.py        # format every content file in place
```

| Tool | What it does |
|---|---|
| `check_schema.py` | Every content file names a schema in `schemas/` and follows it. JSONL files are checked line by line against the schema's `header` and `entry`. |
| `check_format.py` | Every content file is formatted the way `fmt.py` writes it. |
| `check_meta.py` | Languages and varieties: ids match folders and are unique, every variety's parent chain ends at its language, and each language lists its varieties. |
| `check_tools.py` | The tools' own tests in `tests/`. |
| `fmt.py` | Formats content files: keys in schema order, two-space indent, short lists on one line, JSONL one entry per line. |
| `schema.py` | The JSON Schema validator the checks use. It rejects any keyword it doesn't support, so a schema can't be skipped silently. |
| `lib.py` | Shared helpers. |
| `gen_registry.py` | Generates LanguageStudentDesk's `languages/registry.js` and each `languages/<id>/meta.json` from the language meta here. `--check` reports drift. |
| `migrate/lsd_meta.py` | The one-time conversion of LanguageStudentDesk's language meta to `meta@1`, kept so the move can be repeated and checked. |
