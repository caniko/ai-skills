---
name: grouped-git-commits
description: Automatically commit every current Git worktree change in coherent, reviewable groups. Use when the user asks to commit, commit again, commit everything, split a dirty tree, preserve staged and unstaged work, or prepare local changes without pushing. Each invocation commits all work present at invocation time.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Grouped Git Commits

Treat each invocation as an independent pass over every staged, unstaged,
untracked, and deleted path. The request authorizes committing all current
work; do not leave files aside as unrelated. If clean, report that no commit
was needed and do not create an empty commit.

## Workflow

1. Discover before staging:

   ```sh
   git status --short
   git branch --show-current
   git diff --stat
   git diff --cached --stat
   ```

2. Read tracked diffs and inspect untracked files with `rg --files` and
   targeted views. Group by behavioral purpose: code/tests, CI/build/release,
   docs/plans, generated lock/manifest changes, and separable formatting.
3. Stage explicit pathspecs and check before each commit:

   ```sh
   git add <paths>
   git diff --cached --stat
   git diff --cached --check
   git commit -m "Imperative summary"
   ```

4. Repeat discovery until `git status --short` is clean. Report every commit.
5. If the repository has explicit version metadata, add `[Unreleased]`
   changelog entries for the grouped behavioral changes as a separate docs or
   chore commit; otherwise skip changelog work.

## Guardrails

- Never run `git reset --hard`, `git checkout --`, or `git clean` without
  explicit user authorization.
- Do not silently fold staged changes into a mismatched group; commit them as
  their own truthful group or deliberately restage them.
- Do not amend or rebase existing commits unless requested.
- If a required generated artifact or validation source is missing, stop and
  report its producer, regeneration workflow, and validation command.
- Use conventional imperative subjects describing behavior, not file moves.

## Final validation

Require `git diff --cached --check` before every commit, a clean
`git status --short` afterward, changelog entries when versioning requires
them, and any obvious focused test/formatter for the changed files. Report any
skipped validation and why.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
