---
name: consolidate-plan-sets
description: Consolidate multiple existing planning document sets into one current monolithic plan set after auditing what has already landed. Use when a repository has several active or stale plan directories, phase sets, roadmap checklists, or migration plans that should be collapsed into one active plan directory. Always invoke this together with a multi-phase plan flavour such as `multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed` so the resulting consolidated set uses the target provider's routing language and execution assumptions.
---

# Consolidate Plan Sets

Use this skill to replace many overlapping plan sets with one current monolithic plan set for the remaining work: a single plan directory with an overview and many phase files.

This skill depends on two other skills:

- **`plan-progress-review`** — audit existing plans and classify what is done, stale, unfinished, or blocked.
- **One multi-phase plan flavour** — `multi-phase-plan-codex`, `multi-phase-plan-claude`, or `multi-phase-plan-mixed`. The chosen flavour supplies provider-specific model callouts, routing language, and execution assumptions.

If no multi-phase flavour is explicit in the user request, do not write the consolidated plan set. Ask which executing provider the plan targets. In `plan-and-verify prep consolidate` invocations, the orchestrator picks the default — see [`plan-and-verify`](../plan-and-verify/SKILL.md) "Default flavour for prep/plan dispatch". When invoked standalone, this skill still asks.

## Workflow

### 1. Audit existing plan progress

Run `plan-progress-review` first.

- Inventory all plan sets in scope.
- Verify acceptance criteria and plan claims against the current repo state.
- Classify each item as `done`, `partial`, `not-started`, `obsolete`, `blocked`, or `unknown`.
- Stop if foundational artifacts are missing or contradictory and the missing evidence would change what belongs in the consolidated plan.

### 2. Decide what survives

Carry forward only:

- Unfinished work that is still relevant.
- Durable constraints, invariants, and dependency facts needed to execute that unfinished work.
- Verification commands that still match the current repo.
- Known blockers with exact regeneration and validation commands.

Do not carry forward:

- Completed steps.
- Obsolete approaches.
- Checked boxes with no current evidence.
- Phase numbering from old plans.
- Branch names, model-routing notes, or "fresh session" instructions from retired plans.

### 3. Build one consolidated plan set

Write one self-contained plan directory, not several new plan directories and not a single flattened summary file.

Default location:

```text
docs/src/planning/<consolidated-plan-name>/
```

Use the selected multi-phase flavour for provider-specific routing language and phase-file structure, but collapse the old plan families into one directory. The output is still a multi-phase plan set: `README.md` plus `NN-<slug>.md` phase files, with optional sub-layer directories when the selected flavour and work decomposition require them.

The consolidated plan set must include:

- `README.md` as the plan-set orchestrator index, with provider/model recommendation callout from the selected flavour.
- Scope: which old plan sets were consolidated.
- Current state summary from `plan-progress-review`.
- Phase table with dependency order and safe parallelism.
- Parallelism layer in `README.md`: execution waves that show which phases can run at the same time, what each wave unlocks, and when the plan is exhausted.
- A `## Planner Handoff` section in `README.md` that emits the `plan-handoff` schema literally, using its required fields and optional fields only when evidence supports them. Fill required fields from the consolidated `README.md` path, `plan-progress-review` current-state summary, selected multi-phase flavour, surviving phase-table work, known audit blockers, and whole-set acceptance criteria.
- Whole-set acceptance criteria.
- One standalone phase file per remaining work slice, following the selected multi-phase flavour's required shape.
- A coverage or retirement report proving how each old plan set's intent is represented, retired, retained, or rejected.
- Files likely touched, pitfalls, blocked items, and recovery steps in the relevant phase files.
- References to durable source artifacts, not to stale plan prose unless the old plan is the only historical source.

The `README.md` is not optional filler. It is the coordination surface for the plan set and must let a user answer, without opening every phase file first:

- What is the current repo state?
- Which phase starts first?
- Which phases can be run in parallel right now?
- Which phases unlock after each wave?
- Which phases must serialize because they touch the same files or depend on prior validation?
- What command or evidence proves the whole plan set is complete?
- What dossier-shaped contract can a future planner consume to extend or re-route this plan set?

Do not collapse many days or subsystems of remaining work into a handful of milestone paragraphs. If the old material had many independent execution tracks, the consolidated set should have many phase files.

### 4. Retire or unwire superseded plan sets

After the consolidated plan set exists:

- Remove old plan-set entries from navigation if they should no longer be published.
- Delete old plan files only when their remaining relevant work is represented in the consolidated plan set and any durable knowledge is preserved elsewhere.
- Keep any plan with `blocked` or `unknown` items if deleting it would lose the only pointer to missing evidence.

If the task is only to draft the consolidated set, leave old plans in place and report what can be removed later.

### 5. Validate

- Confirm every old plan set is either represented, retired, retained with a reason, or explicitly out of scope.
- Confirm every old plan-set intention has an entry in the coverage report.
- Search for stale references to removed plan files.
- Run the documentation build or link checks when the repository provides them.
- Re-run targeted checks for any acceptance criteria whose status changed while consolidating.

## Output Standard

- Name the selected multi-phase flavour and why it matches the intended executing provider.
- State where the consolidated plan set was written and how many phase files it contains.
- List old plan sets as `represented`, `retired`, `retained`, or `out of scope`.
- State what was verified and what could not be verified.
- If blocked, name the missing or invalid artifact, the upstream producer, the exact command or workflow to regenerate it, and the validation command that proves it is fixed.

## Anti-Patterns

- Do not create several new plan sets. This skill produces exactly one consolidated plan set.
- Do not flatten a large plan family into one summary file. "Monolithic" means one active plan directory, not one markdown file.
- Do not merge stale assumptions just because they appear in multiple plans.
- Do not invent a provider recommendation; use the selected multi-phase flavour's routing rules.
- Do not delete an old plan before its remaining useful work is represented or intentionally rejected.

## Reference

- **`plan-handoff`** — authoritative `## Planner Handoff` schema and required/optional field contract.
