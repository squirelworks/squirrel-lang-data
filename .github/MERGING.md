# How merging works here, and why it is safe now

## What kept going wrong

Many agent threads open PRs at once, and PRs are merged by hand or by another
agent. When two PRs touch the same file, the second one conflicts. Three
times so far (PRs #82, #86 and #87) the conflict was resolved by keeping the
branch's side, in GitHub's conflict editor or with "ours". The merge commit
then looked normal, but its files were the branch's old files. GitHub's diff
for the PR (branch against the point where it last met main) now showed
everything main had gained as deleted or reverted, and "Squash and merge"
applied exactly that. #82 alone undid about 1,300 files (commit 43a72f6).

A branch that is merely *behind* main is not the problem: GitHub squashes with
a three-way merge, so a stale branch with no bad merge in it lands correctly.
The problem is always a merge commit that threw main's side away.

## The guard

`.github/workflows/pr-guard.yml` runs `.github/scripts/pr_guard.py` on every PR
to main (on every push, and when the body or labels change). It fails when:

1. **A file changes only through a merge commit.** Every file in the PR's diff
   must have been touched by one of the branch's own commits. If a file
   differs from main only because of a merge, main's version was thrown away.
   This catches the rollback whatever the merge history looks like. Run on the
   past PRs, it flags #82, #86 and #87 and nothing else.
2. **A file is outside the PR's `Scope:` line.** The PR body's `Scope:` line
   lists the folders or files the PR may change. Without one, the guard prints
   the folders it inferred and does not enforce them.
3. **More than 100 files are deleted**, unless the PR has the `deletions-ok`
   label.

The check always runs main's copy of the script, so a PR cannot loosen its own
check. It also posts one comment on the PR, updated on every run, that starts
with **Merge verdict: SAFE TO MERGE** or **Merge verdict: DO NOT MERGE**, so
whoever merges has a single line to read.

Agents can run the same check locally before pushing:

    python3 .github/scripts/pr_guard.py --base origin/main --head HEAD

## Conflicts get fixed by the agent, not by the person merging

`.github/workflows/pr-conflicts.yml` runs after every push to main. Any open
PR that now conflicts gets the `merge-conflict` label and one comment asking
the Claude thread that owns the branch to merge main and resolve it (rules in
`AGENTS.md`). The label clears itself once the conflict is gone. Nobody
should ever press GitHub's "Resolve conflicts" button.

## One-time settings (repo owner)

Merge the PR that adds this file first, so the check exists on main. Then:

1. Open the repo on GitHub, **Settings → Rules → Rulesets → New ruleset →
   New branch ruleset**.
2. Name it `Protect main`, set **Enforcement status** to **Active**.
3. Under **Target branches**, **Add target → Include default branch**.
4. Tick **Require status checks to pass**, then **Add checks**, type `guard`
   and pick **guard** (GitHub Actions).
   Leave **Require branches to be up to date before merging** *unticked*:
   the guard does not need it, and with many parallel PRs it would make every
   merge invalidate all the others.
5. Keep **Block force pushes** ticked (it is on by default). Leave
   **Restrict deletions** ticked too.
6. **Create**.

Optional, in **Settings → General → Pull Requests**: untick **Allow merge
commits** and **Allow rebase merging** so only "Squash and merge" is offered,
which is what every PR here uses.

With that ruleset on, GitHub greys out the merge button on any PR that fails
the guard, so a bad merge cannot land even if someone tries.
