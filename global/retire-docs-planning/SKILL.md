---
name: retire-docs-planning
description: Retire obsolete planning or roadmap documentation by mapping durable guidance into stable docs, removing planning-only pages from navigation, and deleting no-longer-useful planning files. Use when a repository has `docs/.../planning`, phase docs, roadmap chapters, migration checklists, or similar execution notes that should stop being published once the underlying work has shipped.
---

# Retire Docs Planning

Use this skill to remove planning sections from published documentation without losing knowledge that now belongs in the stable docs.

Read [references/retirement-checklist.md](references/retirement-checklist.md) at the start of the run. Read [references/lessons.md](references/lessons.md) before editing anything, and update it before you finish.

When retirement depends on whether a plan actually landed, invoke **`plan-progress-review`** first unless the caller explicitly uses `clean-shipped <plan-dir>`. Use its status report to decide which planning pages are complete enough to retire, which unfinished work must stay visible, and which claims are blocked by missing evidence.

## Modes

- **`general`** (default) — run the full workflow: inventory, classify, re-verify time-sensitive claims, fold durable knowledge into stable docs, remove the planning surface, validate, and self-improve.
- **`clean-shipped <plan-dir>`** (fast path) — for callers that have already proven `<plan-dir>` fully shipped. Skip steps 1-3: inventory, classify, and re-verify. Start at step 4, then run step 5 and step 6. For step 5, remove the plan with `git rm -r <plan-dir>` and prune any `SUMMARY.md` entries that pointed at it. This mode expects the caller to have proven every acceptance criterion passed and that there are no `missed-signal:` surprises. The retirement is unconditional: **do not prompt, do not ask for confirmation, do not list "durable bits worth preserving" for user approval**.

## Migration criteria

Contributor-worthy durable knowledge includes anything a future contributor would need after the plan disappears:

- current user-facing behavior, API semantics, compatibility rules, and invariants;
- non-obvious constraints, gotchas, architectural decisions, and maintainer guidance;
- release, validation, or runbook commands that still match current workflows and metadata;
- feature-flag, packaging, CI, or source-layout details that stable docs do not already cover.

Do not migrate execution-only artifacts: phase structure, parallelism waves, routing tables, model choices, calibration metadata, dependency graphs, branch names, "run this in a fresh session" instructions, "Why this matters now" framing, or "after this lands" language.

Prefer migrating real contributor knowledge over discarding it; redundancy in stable docs is recoverable, lost knowledge is not. Edit existing stable docs in place, such as `docs/src/`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, API docs, getting-started docs, compatibility references, release docs, or maintenance docs. Do not create a new "retired plan" or "post-mortem" page unless the repository already has a conventional home for one.

## Workflow

### 1. Inventory the published docs and the planning content

- Locate the book navigation or equivalent published-doc entrypoint first.
- Enumerate the planning pages that are currently published.
- Enumerate the stable docs that already exist and could absorb durable knowledge.
- If the pages describe active or recently executed work, run `plan-progress-review` before classifying content.

### 2. Classify the planning content before editing

Split each planning statement into one of three buckets:

- Durable product or maintenance knowledge that belongs in stable docs.
- Execution scaffolding that should disappear once the work is done.
- Claims that require verification from the current repo state before they can be preserved.
- Unfinished or blocked work that should remain as planning content instead of being retired.

Apply the Migration criteria above when sorting: preserve durable behavior, constraints, invariants, release checks, and maintainer guidance; discard execution scaffolding.

### 3. Re-verify every time-sensitive claim from source artifacts

Never promote planning assumptions into stable docs without checking the current source of truth.

- Verify versioned install guidance against files such as `Cargo.toml`, lockfiles, release notes, and actual Git tags.
- Verify feature flags, API names, and compatibility semantics from the code and tests, not from the plan.
- Verify release and CI instructions from the current workflows and packaging metadata.
- If a foundational artifact is missing or contradictory, stop and report the missing source, why it matters, how to regenerate it, and how to validate the fix.

### 4. Fold durable knowledge into stable docs

Use the Migration criteria above as the canonical preservation rule. Keep wording present-tense and product-focused, and place each durable fact near the stable docs surface where future contributors will look for it.

### 5. Remove the planning surface cleanly

- Remove planning entries from nav files such as `SUMMARY.md`.
- Delete obsolete planning files once their durable content has been absorbed.
- Keep or rewrite any plan that `plan-progress-review` marked `partial`, `not-started`, `blocked`, or `unknown` unless the user explicitly wants it consolidated elsewhere.
- If an unresolved future roadmap must be retained, move or classify it outside the active planning tree and update navigation instead of deleting it.
- Remove empty planning directories when practical.
- Search for leftover references to the retired planning section and resolve them.

### 6. Validate the retirement

- Inspect the diff to confirm you preserved durable knowledge and removed only obsolete execution scaffolding.
- Run targeted checks that fit the repo, such as doc builds, link/reference searches, or lightweight tests.
- At minimum, search for stale planning references after the edits.
- If the repository commits generated docs such as mdBook `docs/book`, rebuild
  them before the final stale-reference search so search indexes and rendered
  HTML do not retain deleted planning text.

### 7. Self-improve before you finish

This skill must improve itself on every successful run.

Before ending the task:

1. Append at least one dated lesson to [references/lessons.md](references/lessons.md).
2. If the lesson changes the default workflow, patch `SKILL.md` in the same run.
3. Keep lessons short, concrete, and reusable across repositories.
4. Prefer improving the workflow text over accumulating redundant lessons when the same issue recurs.

## Output Standard

- State where the planning knowledge was folded.
- State which planning files or directories were removed.
- State any plan-progress status used to justify retirement or retention, or the clean verify guarantee supplied by a `clean-shipped` caller.
- State what you verified and what you could not verify.
- If you had to stop, name the missing or invalid artifact, the upstream producer that must fix it, the exact command or workflow to regenerate it, and the validation command that proves it is fixed.

## References

- Clean verify auto-retire caller: [../multi-phase-plan/SKILL.md](../multi-phase-plan/SKILL.md).
