---
name: plan-progress-review
description: Audit plans against repository state before retiring, consolidating, verifying, or rewriting phase docs, roadmaps, and migration checklists; report status only.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Plan Progress Review

Use this reference skill to determine which parts of existing plans are done, still relevant, obsolete, contradictory, or unverifiable.

This skill is intentionally edit-free. It gathers evidence for the active harness
or for a documentation-retirement task.

## Workflow

### 1. Locate plan artifacts

- Find planning directories, roadmap pages, phase docs, migration checklists, and mdBook `SUMMARY.md` entries.
- Prefer published docs entrypoints first, then unlinked plan files.
- If the user named a plan, scope the audit to that plan unless related plans are required to understand dependencies.

### 2. Extract objective claims

For each plan artifact, record:

- Goal or intended end state.
- Acceptance criteria or completion checklist.
- Files, crates, services, or docs the plan says should change.
- Explicit dependencies between phases or plan sets.
- Verification commands, expected log lines, version numbers, feature names, and branch/tag references.

Treat model, provider, effort, and dispatch callouts as execution metadata. Do
not preserve them as repository facts or make them part of the status result.

### 3. Verify against source artifacts

Check every claim against the current source of truth:

- Use code, tests, manifests, lockfiles, workflows, release metadata, generated docs, and Git history as evidence.
- Run the smallest targeted command that proves or disproves an acceptance criterion when static inspection is insufficient.
- Treat contradictory or missing foundational evidence as `blocked`, not as incomplete work.
- Never infer completion from checked boxes alone; a checked box is a lead, not proof.

### 4. Classify each item

Use these statuses:

- `done` — objective evidence proves the item landed.
- `partial` — some required evidence landed, but at least one required part is missing.
- `not-started` — no relevant evidence found.
- `obsolete` — the plan no longer applies because the repository changed direction or the target artifact no longer exists.
- `blocked` — required evidence is missing, contradictory, or cannot be generated in the current environment.
- `unknown` — the plan statement is too vague to derive an objective check.

Prefer `blocked` over guessing when a foundational artifact is missing.

### 5. Produce a progress report

Return a concise report with:

| Plan | Item | Status | Evidence | Next action |
|---|---|---|---|---|

Also include:

- Plans that are fully complete and candidates for retirement.
- Plans with unfinished work that should be preserved or replanned.
- Stale assumptions or contradictions that must not be copied into new docs.
- Missing artifacts, their likely upstream producer, the command or workflow to regenerate them, and the validation command that proves they are fixed.

### 6. Keep the result harness-neutral

Return the status table and evidence to the caller. The active LLM harness
decides whether the remaining work becomes a plan, a queue, or direct execution.
Do not emit model, provider, effort, or dispatch recommendations.

## Consumer Rules

- For `retire-docs-planning`: pass along which planning content is complete enough to retire and which durable knowledge still needs to be folded into stable docs.
- For an execution harness: pass along only unfinished, still-relevant work plus
  durable constraints and the exact evidence needed to verify it.

## Anti-Patterns

- Do not rewrite plans while auditing progress.
- Do not treat planning prose as source of truth.
- Do not preserve provider-routing notes as product knowledge.
- Do not mark an item complete because a file exists; verify the behavior, contract, or command the plan required.

## Reference

- [`retire-docs-planning`](../retire-docs-planning/SKILL.md): consumer for
  deciding whether planning documentation can be removed.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
