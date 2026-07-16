---
name: research-routing
description: Routing meta-skill for ambiguous research-shaped requests. Recommend the most specific evidence-backed specialist, with evidence-first-research as the fall-through. Use when the correct research owner is unclear; this skill performs no investigation or edits.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Research Routing

Recommend one specialist; do not invoke it or perform the research here. The
active harness owns planning, dispatch, and execution.

| Request shape | Recommended skill |
|---|---|
| Simit or downstream generated-file breakage | [`simit-dependent-fixes`](../simit-dependent-fixes/SKILL.md) |
| Nixpkgs build failure intended for a PR | [`nixpkgs-build-failure-pr`](../nixpkgs-build-failure-pr/SKILL.md) |
| Thething host health | canix project-local `host-a-status` |
| Existing plan/phase/roadmap progress or retirement | [`plan-progress-review`](../plan-progress-review/SKILL.md) |
| Complex pre-implementation situation needing orientation | [`evidence-first-research`](../evidence-first-research/SKILL.md) in orientation mode |
| Single-crate versus Cargo workspace decision | [`rust-workspace-check`](../rust-workspace-check/SKILL.md) |
| Anything else | [`evidence-first-research`](../evidence-first-research/SKILL.md) |

## Tie-breaking

1. Prefer the most specific registered domain when its required sources,
   commands, and validation gates apply.
2. Prefer `plan-progress-review` when the user names plans or phase docs.
3. Prefer orientation mode when the user needs a concise decision brief before
   implementation; otherwise use the generic research output selected after
   discovery.
4. If a required specialist is unavailable or its domain is irrelevant, use
   `evidence-first-research` and report the limitation.

## Output

```text
Recommended skill: <skill>
Rationale: <specific trigger and evidence boundary>
Fallback: evidence-first-research if the specialist is unavailable or irrelevant.
Next action: invoke the recommendation directly; this router performs no edits.
```

Do not route every request through this skill, select models/providers/effort,
or silently invoke the recommended skill. “Audit” alone is not enough for plan
progress review; require plan, phase, roadmap, migration, or planning language.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
