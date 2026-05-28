---
name: plan-routing-axes
description: Shared routing axes, provider-agnostic heuristics, and the base output-block template loaded by the two plan-routing skills (claude-plan-routing and gpt-plan-routing). Not a standalone router — it carries no model tiers, IDs, or pricing, so it should not trigger on its own.
---

# Plan-routing axes (shared reference)

Shared reference — not user-invokable on its own; loaded by claude-plan-routing and gpt-plan-routing.

This skill owns the provider-agnostic core that both plan-routing sister skills depend on: the two decision axes, the cross-provider heuristics, and the base shape of a routing output block. Each sister skill loads this and adds its own provider-specific model tiers, IDs, effort/thinking ladders, pricing, and dispatch mechanics on top.

## Decision variables

Evaluate each plan step on two axes before selecting:

**Task complexity** — how much reasoning is required:
- Trivial: well-defined input → output, no ambiguity, no tool chaining
- Moderate: multi-tool, some branching, recoverable errors
- Complex: ambiguous goals, multi-file/multi-system, requires self-correction
- Frontier: open-ended, long-horizon, novel problem, hardest evals

**Role in plan** — where the step sits in the execution hierarchy:
- Leaf node: executes a single concrete action, defined by an orchestrator above it
- Sub-agent: runs a bounded workflow (3–10 steps), may call leaf tools
- Orchestrator: decomposes goals, assigns to sub-agents, monitors outcomes
- Top-level planner: owns the entire plan; handles ambiguity, replanning, inter-agent coordination

## Provider-agnostic heuristics

**Start at medium, dial from there.** Never default to the top of the effort/thinking ladder without a clear reason — every step up roughly multiplies the reasoning-token bill with diminishing returns on well-defined tasks. Always start at `medium` and move up only if the step shows measurable quality loss.

**Tier your effort/thinking within a plan.** Use high tiers only on the orchestrator and on genuinely frontier-complex leaves; assign low/medium to the bulk of leaf nodes. Token costs compound across every step, so misallocation at scale is expensive.

**Stronger-model/high ≈ next-tier-down/medium for orchestration coherence.** Running the cheaper model at `high` is often roughly cost-equivalent to the stronger model at `medium`, and the stronger model produces tighter plans. When you reach `high` on the cheaper tier for orchestration work, test the stronger tier at `medium`.

**Throughput vs quality.** For parallel leaf execution (> 10 concurrent leaves), prefer the cheapest tier to avoid rate limits and control cost. Promote only the steps that fail quality checks.

## Base output-block template

Every routing recommendation includes a block with these fields. Each sister skill specializes the model/effort vocabulary (and may append a provider-specific dispatch section):

```
Model: <model>
Effort or Thinking: <tier>
Rationale: <complexity × role, plus any context-size or latency drivers>
Estimated cost multiplier: <relative to a named baseline tier>
Upgrade trigger: <observable condition → the next tier or model to promote to>
```
