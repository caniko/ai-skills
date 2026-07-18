---
name: grouped-git-commits
description: Commit current Git changes in coherent groups. Use for commit requests, dirty-tree splitting, staging preservation, or local commits without pushing.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Grouped Git Commits

This skill is the canonical reference for everything about commits. Other
skills may add repository orchestration, child/parent ordering, or publication
rules, but they must defer all commit discovery, grouping, format selection,
message construction, validation, changelog, and guardrail decisions to this
skill.

Treat each invocation as an independent pass over every staged, unstaged,
untracked, and deleted path. The request authorizes committing all current
work; do not leave files aside as unrelated. If clean, report that no commit
was needed and do not create an empty commit.

## Commit-format gate

Conventional Commits are the default. A repository-local documented, enforced,
or clearly dominant different subject format overrides that default. Before
composing any subject, inspect the complete changeset and the repository's
authority:

```sh
git status --short
git diff
git diff --cached
git log -20 --format='%s'
git config --get commit.template
```

Also inspect documented contributor guidance and any commit-msg or commitlint
configuration when present. Do not infer a format from the paths named in the
request or from one old commit. The recent log is evidence, not permission to
invent a third format.

Classify the repository's format before staging:

1. If the repository documents or enforces a different subject format, use
   that format while retaining an imperative, behavior-focused subject.
2. If no written or enforced rule exists but recent history clearly follows a
   different subject format, use that format.
3. Otherwise, use Conventional Commits. This includes mixed history and a
   repository whose documented, enforced, or clearly dominant format is
   Conventional Commits; record a mixed-history fallback in the handoff when
   it matters.

The Conventional format is:

```text
<type>[optional scope][!]: <imperative description>

[optional body]

[optional footer(s)]
```

Recognize and validate all of these forms: `feat:`, `feat(scope):`, `feat!:`,
`feat(scope)!:`, `revert:`, and a normal type with a `BREAKING CHANGE:` footer.
Use the agreed lower-case type from this set: `feat`, `fix`, `docs`, `style`,
`refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`. A breaking
change requires `!` before the colon or an uppercase `BREAKING CHANGE:` footer;
the footer token uses hyphens rather than spaces (`Reviewed-by`, not
`Reviewed by`). Separate subject, body, and footer sections with blank lines.

For either format, keep the subject imperative and specific, prefer 50
characters and do not exceed 72 where the repository permits it, and do not
end it with a period. Never use vague subjects such as `update`, `fix stuff`,
or `wip`, and never mix unrelated groups. For Conventional Commits, `feat`
maps to a minor release, `fix` to a patch release, and `!` or
`BREAKING CHANGE:` to a major release; breaking markers override the type.

Choose the type from the actual group: `feat` for a user-visible capability,
`fix` for a defect, `refactor` for behavior-preserving code, `perf` for a
measured optimization, `test` for tests, `docs` for documentation, `style` for
format-only changes, `build` for dependencies/build tooling, `ci` for CI,
`chore` for maintenance or generated metadata, and `revert` only for reverting
an earlier commit. Do not call a generated lockfile refresh a feature, and do
not call a git or file move a behavior change without evidence.

## Workflow

1. Discover before staging:

   ```sh
   git status --short
   git branch --show-current
   git diff --stat
   git diff --cached --stat
   ```

2. Read tracked diffs and inspect every untracked file with `rg --files` and
   targeted views. Group by behavioral purpose: code/tests, CI/build/release,
   docs/plans, generated lock/manifest changes, and separable formatting. Do
   not propose a subject until all staged and unstaged changes have been
   reviewed.
3. Stage explicit pathspecs and check before each commit:

   ```sh
   git add <paths>
   git diff --cached --stat
   git diff --cached --check
   git commit -m "<subject in the selected repository format>"
   ```

   Re-check the selected subject against the format gate after staging. If a
   body or footer is needed, pass it as a separate message paragraph and keep
   the required blank lines. Let the repository's commit-msg hook or commitlint
   validate the message when available; otherwise apply the same checks before
   invoking `git commit`.

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
- Do not silently convert a repository's documented non-Conventional format to
  Conventional Commits, or the reverse. When the format cannot be established
  from repository guidance, hooks, or history, use the Conventional fallback
  above and say so.

## Final validation

Require `git diff --cached --check` before every commit, a clean
`git status --short` afterward, changelog entries when versioning requires
them, and any obvious focused test/formatter for the changed files. Confirm
that every created subject matches the selected repository format and report
any skipped validation or format fallback and why.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
