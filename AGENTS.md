# Rules for agents working in this repo

This repo holds content only. Several agents open PRs here, and another agent
reviews and merges them. The PR guard blocks a PR whose diff would undo work
already on `main`; the full story is in `.github/MERGING.md`.

## If you open PRs

1. Start a branch from the latest `origin/main`. One seam per PR: one content
   type, one language, one import, or one tool.
2. Put a `Scope:` line at the top of the PR body naming the folders or files the
   PR may change, e.g. `Scope: languages/greek/, SOURCES.md`. The guard fails the
   PR if it changes anything else.
3. Content is plain JSON or JSONL that names its schema. Imported content comes
   from a script under `tools/`, and the PR body names the source and its
   license. Add the source to `SOURCES.md` in the same PR.
4. A PR that moves content in from another repo names the commit it was copied
   from.
5. Never commit app code, build output, or large downloaded files.
6. When your PR conflicts with main, fix it yourself:
   `git fetch origin main && git merge origin/main`, combine both sides of every
   conflict, run `python3 .github/scripts/pr_guard.py --base origin/main --head HEAD`,
   and push. Never use `-s ours`, `-X ours` or `git checkout --ours .`.
7. Never force-push or rewrite pushed history.

## If you merge PRs

1. Merge only when every check is green, including **PR guard / guard**, and the
   PR's "Merge verdict" comment says **SAFE TO MERGE**.
2. Don't resolve merge conflicts that need judgement. Skip the PR; the agent that
   opened it fixes it.
3. Use "Squash and merge". Never merge with failing or pending checks.
