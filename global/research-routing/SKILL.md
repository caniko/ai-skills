---
name: research-routing
description: "Routing meta-skill for research-shaped requests. Given a request that needs evidence-backed investigation, picks the right specialist skill: long-horizon-research (generic), plan-research (multi-phase prep), simit-dependent-fixes (simit-grounded), nixpkgs-build-failure-pr (nixpkgs build-grounded), host-a-healthcheck (host-a-grounded), plan-progress-review (plan-audit-grounded), northstar (high-stakes situational), workspace-check (single-crate-grounded). Decision support only - performs no edits. Use when you have a research-shaped ask but are not sure which specialist owns it."
---

# Research routing

## Purpose

Use this skill to route a research-shaped request to the right specialist before doing the investigation. The goal is to avoid defaulting to generic dossier work when a domain-grounded skill already knows the required sources, commands, validation flow, and failure modes. This skill is decision support only - it performs no edits and does not run the selected research workflow.

## Routing table

| Request shape | Skill | Trigger heuristics |
|---|---|---|
| Multi-phase planning prep | [`plan-research`](../plan-research/SKILL.md) | User wants to plan a refactor, migration, cleanup, or long-term work; output will feed `multi-phase-plan-*` afterward |
| Simit ecosystem | [`simit-dependent-fixes`](../simit-dependent-fixes/SKILL.md) | Mentions simit, downstream-of-simit projects, simit release migration, simit-generated CI/flake drift, or registry sweeps |
| Nixpkgs build failure | [`nixpkgs-build-failure-pr`](../nixpkgs-build-failure-pr/SKILL.md) | User supplies a failing nix build log, ofborg failure, Hydra failure, compiler error, dependency failure, or derivation failure; goal is a nixpkgs PR fix |
| Thething host health | [`host-a-healthcheck`](../host-a-healthcheck/SKILL.md) | Mentions host-a, a specific NixOS host; checking reachability, post-deploy sanity, aliveness, failed units, or host health |
| Audit existing plan sets | [`plan-progress-review`](../plan-progress-review/SKILL.md) | User asks for progress/status/retirement/consolidation of existing plan dirs, phase docs, roadmap checklists, migration plans, or planning directories |
| High-stakes pre-implementation summary | [`northstar`](../northstar/SKILL.md) | Complicated situation with many constraints, partial truths, competing paths, or consequential decisions; needs a concise orienting summary before implementation planning |
| Single-crate-vs-workspace decision | [`workspace-check`](../workspace-check/SKILL.md) | Single-crate Rust project; deciding whether file count, LOC, module shape, or growth pressure justify a Cargo workspace |
| Anything else | [`long-horizon-research`](../long-horizon-research/SKILL.md) | Fall-through for generic evidence-backed investigation and durable research dossiers |

## Decision tree

1. Is the request planning prep for a refactor, migration, cleanup, or long-term work? Recommend `plan-research`.
2. Does the request name a registered domain: simit, nixpkgs build failure, host-a, or a single-crate workspace decision? Recommend the corresponding specialist.
3. Is the request asking to audit existing plans, phase docs, roadmap checklists, or planning directories? Recommend `plan-progress-review`.
4. Is the request asking for a concise summary of a complicated situation before implementation? Recommend `northstar`.
5. Otherwise recommend `long-horizon-research`.

## Multi-route handling

When a request fits more than one category, recommend the most specific grounded specialist first. For example, "plan a simit refactor" should start with `simit-dependent-fixes` because simit-specific downstream discovery and generated-file rules are load-bearing; that specialist may then invoke `plan-research` or `long-horizon-research` as a sub-step.

Prefer domain ownership over generic research whenever the domain skill has required commands, sources, validation gates, or repo-specific constraints. Use the generic fall-through only after ruling out a listed specialist.

## What the router is not

This is not a dispatcher. It returns a recommendation and rationale; the caller invokes the chosen skill themselves.

This is not a plan-execution model selector. Use the `carter` CLI (via [`multi-phase-plan`](../multi-phase-plan/SKILL.md)) for model/effort routing.

This is not an edit workflow. It should not patch files, run domain commands, or perform the research inside this skill.

## Anti-patterns

- Picking `long-horizon-research` for a domain that has a specialist; that defeats the point of the router.
- Routing every request through this skill; most requests are clear enough to invoke the relevant skill directly.
- Treating any "audit" request as `plan-progress-review`; require plan, phase, roadmap, migration, or planning-document language.
- Invoking the selected skill on the user's behalf from this router; recommend first, execute only when the caller explicitly proceeds.

## Output format

When using this skill to make a routing recommendation, output:

```
Recommended skill: simit-dependent-fixes
Rationale: the request is simit-grounded and asks about downstream breakage after a release migration.
Fallback: long-horizon-research only if the simit registry context is irrelevant or unavailable.
Next action: invoke the recommended skill directly; this router performs no edits.
```

## Reference

- Specialist targets and their trigger heuristics: the Routing table above.
- Model/effort routing: the `carter` CLI, invoked via [`multi-phase-plan`](../multi-phase-plan/SKILL.md).
