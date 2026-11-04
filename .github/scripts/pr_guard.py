#!/usr/bin/env python3
"""PR guard: stop a pull request from quietly undoing work already on main.

A merge can go wrong in a way GitHub happily squash-merges: main is merged
into the branch, a conflict is resolved by keeping the branch's side, and the
PR's diff now deletes or reverts everything main gained in the meantime.

Checks, all against the merge base with main (the same diff GitHub squashes):

1. Merge-only changes. A file the PR changes must have been touched by one of
   the branch's own (non-merge) commits. A file that differs from main only
   because of a merge commit is a lost conflict resolution, so the PR fails.
   This holds whatever the merge history looks like.
2. Scope. A "Scope:" line in the PR body lists the folders or files the PR may
   change, e.g. "Scope: programming-learner/, README.md". Any other changed
   file fails. Without the line, the scope is the top-level folders the
   branch's own commits touched (reported, not enforced).
3. Mass deletion. Deleting more than DELETE_LIMIT files needs the
   "deletions-ok" label.

Usage: pr_guard.py --base <main ref> --head <branch ref> [--body-file F] [--labels a,b]
Locally: python3 .github/scripts/pr_guard.py --base origin/main --head HEAD
"""
import argparse
import fnmatch
import re
import subprocess
import sys

DELETE_LIMIT = 100
LIST_LIMIT = 40


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def parse_scope(body):
    entries = []
    for m in re.finditer(r"^\s*[*_`]*Scope[*_`]*\s*:\s*(.+)$", body or "", re.I | re.M):
        if "<" in m.group(1):  # the template's unfilled placeholder
            continue
        entries += [e.strip("`*_ ") for e in re.split(r"[,\s]+", m.group(1))]
    return [e.lstrip("./") if e.startswith("./") else e for e in entries if e]


def in_scope(path, scope):
    for s in scope:
        if s in ("*", "**", "/"):
            return True
        if s.endswith("/") and path.startswith(s):
            return True
        if path == s or path.startswith(s.rstrip("/") + "/") or fnmatch.fnmatch(path, s):
            return True
    return False


def show(title, paths):
    print(f"\n{title} ({len(paths)}):")
    for p in paths[:LIST_LIMIT]:
        print(f"  {p}")
    if len(paths) > LIST_LIMIT:
        print(f"  ... and {len(paths) - LIST_LIMIT} more")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--body-file")
    ap.add_argument("--labels", default="")
    a = ap.parse_args()

    body = open(a.body_file, encoding="utf-8").read() if a.body_file else ""
    labels = {l.strip() for l in a.labels.split(",") if l.strip()}

    base = git("merge-base", a.base, a.head).strip()
    changes = {}
    for line in git("diff", "--name-status", "--no-renames", base, a.head).splitlines():
        status, path = line.split("\t", 1)
        changes[path] = status[0]
    own = set(git("log", "--no-merges", "--format=", "--name-only", f"{a.base}..{a.head}").split("\n")) - {""}

    failed = False
    print(f"Merge base {base[:10]}; {len(changes)} files changed; "
          f"{len(own)} files touched by the branch's own commits.")

    merge_only = sorted(p for p in changes if p not in own)
    if merge_only:
        failed = True
        deleted = [p for p in merge_only if changes[p] == "D"]
        print("\nFAIL: these files change only through a merge commit, never through the "
              "branch's own commits. That is what a conflict resolved to the wrong side "
              "looks like: main's version is being thrown away.")
        if deleted:
            show("Deleted by a merge", deleted)
        show("Changed only by a merge", [f"{changes[p]} {p}" for p in merge_only if changes[p] != "D"])
        print("\nFix: merge main into the branch again and keep main's side for every file "
              "above (git checkout origin/main -- <file>), or redo the merge without "
              "'ours'. Do not resolve conflicts in GitHub's web editor.")

    scope = parse_scope(body)
    if scope:
        outside = sorted(p for p in changes if not in_scope(p, scope))
        print(f"\nScope: {', '.join(scope)}")
        if outside:
            failed = True
            print("FAIL: files changed outside the PR's Scope line.")
            show("Outside scope", [f"{changes[p]} {p}" for p in outside])
            print("\nFix: drop those changes, or add the folder to the Scope line if the PR "
                  "really means to change it.")
    else:
        tops = sorted({p.split("/", 1)[0] + ("/" if "/" in p else "") for p in own})
        print(f"\nNo 'Scope:' line in the PR body. Inferred scope from own commits: {', '.join(tops) or '(none)'}")
        print("Add a line like 'Scope: " + (", ".join(tops[:3]) or "my-folder/") +
              "' to the PR body to have it enforced.")

    deletions = sorted(p for p, s in changes.items() if s == "D")
    if len(deletions) > DELETE_LIMIT and "deletions-ok" not in labels:
        failed = True
        print(f"\nFAIL: the PR deletes {len(deletions)} files (limit {DELETE_LIMIT}). "
              "If that is intended, add the 'deletions-ok' label.")
        show("Deleted", deletions)

    print("\nPR guard: " + ("FAILED" if failed else "passed"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
