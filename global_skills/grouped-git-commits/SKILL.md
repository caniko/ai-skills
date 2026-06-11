---
name: grouped-git-commits
description: Commit all current Git worktree changes in coherent, reviewable groups. Use when the user asks to commit everything, commit in groups, split a dirty tree into sensible commits, preserve staged and unstaged work while committing, or prepare local changes for later publishing without pushing.
---

# Grouped Git Commits

## Overview

Create small, truthful commits from an existing dirty worktree without losing
user changes or inventing intent. The workflow is discovery-first: inspect the
actual diff, group by behavioral purpose, commit each group, then confirm the
final state.

## Workflow

1. Inspect repository state before staging anything:

```bash
git status --short
git branch --show-current
git diff --stat
git diff --cached --stat
```

2. Read the relevant diffs. Use `git diff -- <paths>` and
   `git diff --cached -- <paths>` for tracked changes; use `rg --files` and
   targeted `sed`/`nl` for untracked trees. Do not rely on filenames alone.

3. Group changes by one primary purpose per commit. Prefer these boundaries:

- Functional code and matching tests
- CI, packaging, release, or build tooling
- Documentation or planning artifacts
- Generated lockfile or manifest updates tied to the change that caused them
- Mechanical formatting only when it is separable

4. Stage pathspecs explicitly for each group:

```bash
git add path/to/file path/to/dir
git diff --cached --stat
git diff --cached --check
git commit -m "Imperative summary"
```

5. Repeat until `git status --short` is clean or only intentionally uncommitted
   files remain. Report the remaining files if anything is left.

## Guardrails

- Never run destructive cleanup (`git reset --hard`, `git checkout --`,
  `git clean`) unless the user explicitly requested it.
- Do not silently fold unrelated staged changes into the next commit. If
  staged state does not match the intended group, inspect it and either commit
  it as its own group or restage deliberately.
- Do not fabricate missing context. If a required generated artifact,
  validation source, or upstream input is absent, stop and report the exact
  missing item and the command or workflow needed to regenerate it.
- Do not amend or rebase existing commits unless the user specifically asks.
- Use conventional, imperative commit subjects that describe the grouped
  behavior, not the file operation.

## Validation

Run checks that are proportional to the change and practical in the current
repo. At minimum:

- `git diff --cached --check` before each commit
- `git status --short` after the last commit
- Any focused test, formatter, or validation command that is obvious from the
  files changed

If validation is skipped, say exactly why.
