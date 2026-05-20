---
name: gpt-plan-routing
description: Select the right GPT-5.x model and reasoning effort level for plan execution tasks. Use when an agent or orchestrator needs to route a plan step, sub-task, or full workflow to the optimal model+effort combination. Triggers on: "which model should I use for this step", "route this task", "what effort level", or when building multi-agent plans that need tiered model selection.
---

# GPT plan execution routing

Use this skill to select the right model and `reasoning_effort` level for a given plan step or workflow. The goal is to match task complexity and role-in-plan to the cheapest combination that meets quality requirements.

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

---

## Model tiers

### GPT-5.5 — frontier orchestration
- Context: 1M tokens (standard window 272K; 2× surcharge above)
- Pricing: $5/$30 per MTok in/out (base)
- Default effort: `medium`
- Strengths: highest plan coherence, precise tool selection at scale, best error recovery, holds context across large systems
- Use when: top-level planner or primary orchestrator for any complex workflow; latency-tolerant long-horizon tasks; multi-agent coordination; ambiguous or partially-specified plans

### GPT-5.4 — production workhorse
- Context: 1M tokens (same surcharge structure)
- Pricing: $2.50/$15 per MTok in/out
- Default effort: `medium`
- Strengths: strong across all plan execution dimensions; native computer use (OSWorld 75%); cost-effective vs 5.5 for well-defined orchestration
- Use when: primary orchestrator where 5.5 cost is not justified; batch pipelines; agentic coding + computer-use flows; most production plan deployments

### GPT-5.4-mini — cost-efficient sub-agent
- Context: 400K tokens
- Pricing: ~$0.40/$1.60 per MTok in/out
- Strengths: 94% of 5.4 coding performance at 1/10th output cost; good tool precision at medium+; high throughput
- Use when: sub-agents and leaf nodes in larger plans; high-volume structured dispatch; cost-sensitive agentic loops where tasks are bounded and well-defined

### GPT-5.3-Codex — coding-specialist sub-agent
- Context: 400K tokens
- Pricing: $1.25/$10 per MTok in/out (being phased out; prefer 5.4-mini for new builds)
- Strengths: optimized for long-running terminal/coding workflows; supports interactive steering during execution; strong on SWE-Bench Pro and agentic coding evals
- Use when: coding-specific plan steps; terminal command sequences; existing 5.3-Codex pipelines not yet migrated

### GPT-5.3-mini — lightweight leaf executor
- Note: not a distinct API model ID; treated as GPT-5.3-Codex at low effort settings. For new builds, use GPT-5.4-mini instead.
- Use when: cost is the primary constraint and tasks are simple, sequential, and coding-focused

---

## Effort levels

All models expose `reasoning_effort` with these semantics for plan execution:

| Effort | Token overhead | Latency | Use for |
|--------|---------------|---------|---------|
| `low` | minimal | fast | leaf nodes with clear tool params; high-throughput dispatch; latency-sensitive steps |
| `medium` | moderate | medium | default for most plan steps; balanced quality/cost/latency; recommended starting point |
| `high` | 2× output vs low | slow | batch processing; multi-system plans; error-recovery critical; orchestrators where latency doesn't matter |
| `xhigh` | 3–5× output vs low | very slow | hardest async tasks; top-level planning on novel/ambiguous problems; eval harnesses; 20h+ tasks |

Cost implication: higher effort generates more reasoning tokens billed at normal output rates. In a multi-step plan, effort-tiering compounds — use the minimum effort level that passes your quality bar per step.

---

## Routing table

Match **task complexity × role** to the recommended combination:

```
Role            | Trivial          | Moderate          | Complex           | Frontier
----------------|------------------|-------------------|-------------------|------------------
Leaf node       | 5.4-mini/low     | 5.4-mini/medium   | 5.4-mini/high     | 5.4/medium
Sub-agent       | 5.4-mini/medium  | 5.4/low           | 5.4/medium        | 5.4/high
Orchestrator    | 5.4/medium       | 5.4/high          | 5.5/medium        | 5.5/high
Top-level plnr  | 5.5/medium       | 5.5/medium        | 5.5/high          | 5.5/xhigh
```

**Coding-specific override**: replace the model with 5.3-Codex (existing pipelines) or 5.4-mini (new builds) for any step whose output is purely code or terminal commands.

---

## Key heuristics

**Start at medium, dial from there.** Never default to `xhigh` without benchmarking — it increases cost 3–5× with diminishing returns on well-defined tasks. Always start at `medium` and move up only if evals show measurable quality gain.

**5.5/medium ≈ 5.4/high** in plan coherence with fewer tokens. If you're running 5.4 at `high`, test 5.5 at `medium` — it's often cheaper and better for orchestration-heavy workloads.

**Tier your effort within a plan.** Use `high`/`xhigh` only on the orchestrator; assign `low`/`medium` to leaf nodes. Token costs compound across every step, so effort misallocation at scale is expensive.

**Long-horizon needs large context.** Steps with > 50 prior plan steps or large codebase context require 5.4+ (1M context). 5.4-mini and 5.3-Codex cap at 400K — chunk or summarize before routing there.

**Throughput vs quality tradeoff.** For parallel leaf execution (> 10 concurrent steps), prefer 5.4-mini/low to avoid rate limits and control cost. Promote to 5.4/medium only for steps that fail quality checks.

**Use `low` before `none` for plan steps.** `none` disables reasoning entirely — suitable only for pure retrieval or classification, not for steps that involve tool selection or multi-step logic. Even a simple plan step benefits from `low` effort.

---

## Output format for routing decisions

When using this skill to make a routing recommendation, output:

```
Model: gpt-5.4
Effort: medium
Rationale: sub-agent orchestrating a 5-step coding workflow; moderate complexity; latency-tolerant batch context
Estimated cost multiplier vs low: ~1.5×
Upgrade trigger: if error recovery fails > 20% of steps → promote to gpt-5.4/high
```
