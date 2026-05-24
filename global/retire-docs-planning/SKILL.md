---
name: retire-docs-planning
description: Retire obsolete planning or roadmap documentation by mapping durable guidance into stable docs, removing planning-only pages from navigation, and deleting no-longer-useful planning files. Use when a repository has `docs/.../planning`, phase docs, roadmap chapters, migration checklists, or similar execution notes that should stop being published once the underlying work has shipped.
---

# Retire Docs Planning

Use this skill to remove planning sections from published documentation without losing knowledge that now belongs in the stable docs.

Read [references/retirement-checklist.md](references/retirement-checklist.md) at the start of the run. Read [references/lessons.md](references/lessons.md) before editing anything, and update it before you finish.

When retirement depends on whether a plan actually landed, invoke **`plan-progress-review`** first. Use its status report to decide which planning pages are complete enough to retire, which unfinished work must stay visible, and which claims are blocked by missing evidence.

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

Do not copy phase structure, model-routing notes, branch names, or “run this in a fresh session” instructions into stable docs. Preserve behavior, constraints, invariants, release checks, and maintainer guidance.

### 3. Re-verify every time-sensitive claim from source artifacts

Never promote planning assumptions into stable docs without checking the current source of truth.

- Verify versioned install guidance against files such as `Cargo.toml`, lockfiles, release notes, and actual Git tags.
- Verify feature flags, API names, and compatibility semantics from the code and tests, not from the plan.
- Verify release and CI instructions from the current workflows and packaging metadata.
- If a foundational artifact is missing or contradictory, stop and report the missing source, why it matters, how to regenerate it, and how to validate the fix.

### 4. Fold durable knowledge into stable docs

- Prefer updating existing stable pages over creating a new “retired plan” page.
- Put user-facing API behavior in API or getting-started docs.
- Put semantic rules and invariants in compatibility or reference docs.
- Put maintainer and validation guidance in release or maintenance docs.
- Keep wording present-tense and product-focused. Remove “Phase”, “next step”, and “after this lands” language.

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
- State any plan-progress status used to justify retirement or retention.
- State what you verified and what you could not verify.
- If you had to stop, name the missing or invalid artifact, the upstream producer that must fix it, the exact command or workflow to regenerate it, and the validation command that proves it is fixed.
