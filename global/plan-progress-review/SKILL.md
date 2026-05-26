---
name: plan-progress-review
description: Common reference skill for auditing existing planning documents against current repository state. Use when Codex needs to check progress of existing plan sets, phase docs, roadmap checklists, migration plans, or planning directories before retiring, consolidating, verifying, or rewriting them. Produces a factual status report only; it does not create a new plan or edit docs by itself.
---

# Plan Progress Review

Use this reference skill to determine which parts of existing plans are done, still relevant, obsolete, contradictory, or unverifiable.

This skill is intentionally edit-free. It gathers evidence for another skill, such as `retire-docs-planning`, `consolidate-plan-sets`, or a multi-phase plan flavour.

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

Ignore model-routing callouts except to preserve which provider the plan was written for when a caller needs that context.

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

### 6. Emit a planner handoff in producer mode only

**Producer mode only**: if invoked directly by the user as the entrypoint for a downstream multi-phase planner, append a `## Planner Handoff` section to the progress report conforming to the [`plan-handoff`](../plan-handoff/SKILL.md) schema.

Required fields:

- Dossier path: this progress report's file.
- Current-state summary: the table's overall takeaways.
- Recommended planner flavour: use the canonical downstream-flavour rule
  from [`plan-and-verify`](../plan-and-verify/SKILL.md) "Default flavour
  for prep/plan dispatch".
- Work that should become phases: each unfinished-but-still-relevant item from the table.
- Known blockers: each `blocked` row.
- Acceptance evidence to preserve: verification commands the table cites.

**Evidence supplier mode**: if invoked internally by another skill, do not emit a handoff. The calling skill consumes the table directly and writes its own handoff when needed.

## Handoff Rules

- For `retire-docs-planning`: pass along which planning content is complete enough to retire and which durable knowledge still needs to be folded into stable docs.
- For `consolidate-plan-sets`: pass along only unfinished, still-relevant work plus any durable constraints needed by the new monolith plan.
- For multi-phase plan verify mode: do not duplicate the verifier; use this skill for broader plan-set triage across multiple existing plan directories.
- **Producer vs supplier mode**: emit the handoff section only when this skill is the user-facing entrypoint. When called internally by `retire-docs-planning`, `consolidate-plan-sets`, or `multi-phase-plan` verify, the caller owns the handoff and this skill does not duplicate it.

## Anti-Patterns

- Do not rewrite plans while auditing progress.
- Do not treat planning prose as source of truth.
- Do not preserve provider-routing notes as product knowledge.
- Do not mark an item complete because a file exists; verify the behavior, contract, or command the plan required.

## Reference

- [`plan-handoff`](../plan-handoff/SKILL.md): shared `## Planner Handoff` schema for producer-mode reports.
