---
name: renew-planning-tree
description: Consolidate and retire an outdated planning documentation tree by auditing stale, complete, partial, blocked, and unknown plan sets; producing one current multi-phase plan set with a chosen provider flavour; folding durable knowledge into stable docs; pruning published navigation; and scheduling or deleting residual planning files. Use when a repo has `docs/src/planning`, roadmap phase sets, execution matrices, old verify snapshots, or mixed complete/partial plans that should become one active plan surface.
---

# Renew Planning Tree

Use this skill when the user's goal is broader than drafting one plan: the planning tree itself is stale and must be renewed into a single current plan set while complete work is retired and partial work is preserved.

This skill composes existing skills:

- `plan-progress-review` for evidence-backed classification.
- `consolidate-plan-sets` for the single active replacement plan.
- A multi-phase flavour, usually named by the user (`multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed`).
- `retire-docs-planning` for durable-knowledge migration and planning-surface removal.

## Workflow

### 1. Establish Scope And Entrypoints

Locate published documentation entrypoints first: `docs/src/SUMMARY.md`, sidebars, route manifests, or README navigation. Inventory both published plan entries and unlinked planning files under the requested tree.

If no multi-phase flavour is explicit, ask for the executor/provider before writing the replacement plan. If a flavour is explicit, use it.

### 2. Run Progress Review

Classify every in-scope plan set, phase, one-off planning note, and verify snapshot with `plan-progress-review` statuses:

- `done`
- `partial`
- `not-started`
- `obsolete`
- `blocked`
- `unknown`

Verify claims against current source, stable docs, tests, manifests, logs, and workflows. A checked box or old verify note is a lead, not proof.

Stop instead of guessing when a foundational artifact is missing or contradictory. Report:

- the missing or invalid artifact,
- why it is required,
- the upstream producer,
- the exact command or workflow to regenerate it,
- the validation command that proves it is fixed.

### 3. Decide What Survives

Carry forward only:

- unfinished work that is still relevant,
- durable constraints needed to execute that work,
- current verification commands,
- known blockers with regeneration and validation commands,
- stable-doc gaps that must be closed before deletion.

Do not carry forward:

- completed execution steps,
- stale model-routing notes,
- old phase numbering,
- branch names or stale dates,
- aspirational claims unsupported by current evidence.

If old planning files are still referenced by source fixtures, stable docs, or roadmap pages, either move the durable artifact to a stable home before deletion or create a final cleanup phase that performs that link repair. Do not delete files that current source still `include_str!`s unless the source is updated in the same run.

### 4. Build One Current Plan Set

Create exactly one active plan directory, normally:

```text
docs/src/planning/<current-plan-name>/
```

Use the selected multi-phase flavour's README and phase-file structure. The README must include:

- model/provider callout,
- scope and current-state summary,
- evidence-backed status table for old plan families,
- phase table with dependencies and safe parallelism,
- parallelism layer,
- whole-set acceptance criteria,
- global constraints,
- coverage/retirement report for every old plan set,
- `## Planner Handoff` using the `plan-handoff` schema.

Each phase file must be self-contained. Include exact current evidence for why the phase exists, especially failing commands or source probes.

### 5. Retire The Published Planning Surface

Update navigation so readers see the new current plan, not the stale forest. Remove links to completed or superseded plan sets from `SUMMARY.md` or equivalent.

Delete old planning files only after durable knowledge has been folded into stable docs and references are repaired. If deletion is unsafe because live references remain, leave the old files unlisted and add a final phase in the new plan to complete the deletion after link repair.

Use `retire-docs-planning` rules for durable knowledge:

- preserve current behavior, APIs, invariants, compatibility, validation commands, and maintainer guidance,
- discard execution scaffolding, phase tables, old routing, and "run in fresh session" text,
- write present-tense stable docs.

### 6. Validate

Run targeted checks appropriate to the repo:

- stale-reference search for old slugs and titles,
- docs build or mdBook build,
- targeted tests that changed a status from partial/unknown to done,
- skill validation if a reusable skill was created or updated.

If the docs build is blocked by unrelated concurrent edits, report the blocker and still prove the changed scope with targeted stale-reference searches and navigation diffs.

### 7. Report

Final output must state:

- selected multi-phase flavour,
- replacement plan directory and phase count,
- old plan sets represented, retired, retained, or blocked,
- durable knowledge folded into stable docs,
- planning files or navigation entries removed,
- checks run and their results,
- missing artifacts or validation gaps.

## Anti-Patterns

- Do not create several new plan sets.
- Do not flatten the replacement into a single summary page when phases are needed.
- Do not delete old plans before their live references and durable knowledge are handled.
- Do not copy stale acceptance criteria into the new plan without re-verifying current source.
- Do not preserve old provider routing or execution scaffolding as product knowledge.
- Do not fabricate deployment, DNS, CI, or test evidence.

## References

- `plan-progress-review`
- `consolidate-plan-sets`
- `retire-docs-planning`
- `multi-phase-plan-codex`
- `multi-phase-plan-claude`
- `multi-phase-plan-mixed`
- `plan-handoff`
