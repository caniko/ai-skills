---
name: plan-research
description: Pre-plan research wrapper around long-horizon-research that emits the plan-handoff schema for direct consumption by multi-phase-plan. Use before multi-phase-plan when the planning target needs evidence-backed research first. Also discoverable as multi-plan-research (alias). Routing constraints follow [plan-and-verify](../plan-and-verify/SKILL.md) "Default routing for prep/plan dispatch".
---

# Plan Research

## Purpose

Use this wrapper when evidence-backed research must feed a multi-phase planner. Load `long-horizon-research` as the base research workflow, load `plan-handoff` as the schema contract, and pair the resulting dossier with `multi-phase-plan` (which routes models via the `carter` CLI).

## When to use

- Before longterm planning, a large refactor or migration, stale plan consolidation, or "research before we call the multi-phase skill".
- When the target is consequential enough that a future planner needs traceable current-state evidence.
- When the output should become a research dossier with a literal `## Planner Handoff` section.

For non-planning research, invoke `long-horizon-research` directly, or use the [`research-routing`](../research-routing/SKILL.md) sibling to pick the right specialist.

## Discovery Alias

This skill is also available as `multi-plan-research` via directory symlink. Use `plan-research` in written references; the alias exists for grep and skill-search discoverability.

## Workflow

1. Establish the planning target: user goal, target repo, and any routing constraints (default per the Routing-Constraint Rule below).
2. Run the base `long-horizon-research` workflow: discover, audit existing plans when present, stop on blockers, apply the right-size gate, and write the dossier.
3. If the right-size gate downshifted to a `-findings.md` note, stop. This wrapper has nothing to add to a non-planning investigation; report the findings path and exit.
4. Otherwise, append `## Planner Handoff` to the dossier and emit the `plan-handoff` schema literally. Fill every required field with concrete evidence-backed content; fill optional fields only when dossier evidence supports them.
5. In the same dossier, add `## Candidate Phase Boundaries` with dependency table and parallelism notes. The schema's optional `Candidate phase boundaries` field references this section.
6. End the dossier with a planner brief: the exact prompt and context the user should feed to `multi-phase-plan` so it can consume the dossier.

## Routing-Constraint Rule

Routing constraints: see [`plan-and-verify`](../plan-and-verify/SKILL.md) "Default routing for prep/plan dispatch". This wrapper follows that rule when it fills `Routing constraints` in the Planner Handoff (`none` when the user named no provider or budget pressure).

## Output Standard

In the final response, state:

- Dossier path.
- Routing constraints recorded.
- Planner Handoff completeness: required fields filled and which optional fields were populated.
- Whether the base downshifted to a findings note.

## Anti-Patterns

- Emitting the handoff section in prose instead of the `plan-handoff` schema.
- Padding optional fields when evidence is absent.
- Recording routing constraints that conflict with the canonical
  `plan-and-verify` rule or the user's explicit provider signal.
- Routing models or writing phase files; that belongs to `multi-phase-plan` (and the `carter` CLI it calls).

## Reference

- `long-horizon-research` - base evidence dossier workflow.
- `plan-handoff` - literal Planner Handoff schema contract.
- `multi-phase-plan` - downstream planner (model routing via the `carter` CLI).
- `research-routing` - sibling router for non-planning research selection.
