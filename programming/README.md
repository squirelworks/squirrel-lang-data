# Programming courses

Each folder under `programming/<id>/` holds a `course.json` with schema
`programming-course@1`. The catalog at `programming/catalog.json`
(`programming-catalog@1`) lists every course the Programming Learner and
related tools know about.

Course text is original under this repo's license. Language shapes are
cited in `SOURCES.md`.

## Layout

- `catalog.json` — ids, names, eras, groups (`modern`, `older`, `joke`) and blurbs
- `<id>/course.json` — lessons, keywords, builtins and practice for that language

Keyword maps shared with squirrelator's Phase 4 generators will land beside
the course packs in a later seam. Until then, keywords live on each course
object.

## Checks

```bash
python3 tools/check_programming.py
tools/check_all.sh
```
