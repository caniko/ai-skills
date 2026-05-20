---
name: claude-plan-routing
description: Select the right Claude 4.x model and extended-thinking budget for plan execution tasks, then dispatch via the Agent tool. Use when an agent or orchestrator needs to route a plan step, sub-task, or full workflow to the optimal Claude model+thinking combination. Triggers on "which Claude model should I use", "route this Claude task", "thinking budget", or when building multi-agent Claude plans that need tiered model selection. Sister skill to `gpt-plan-routing`.
---

# Claude plan execution routing

Use this skill to select the right Claude model and extended-thinking budget for a given plan step or workflow, and then **dispatch the work via the Agent tool**. The goal is to match task complexity and role-in-plan to the cheapest combination that meets quality requirements, and execute the routing decision in one motion.

## Dispatch contract: Agent tool inherits parent effort

The Agent tool exposes a `model` parameter but **no `thinking` / `effort` parameter**. Spawned agents inherit the parent's current effort/thinking level. This means:

> **Before invoking `Agent({...})` for any routed step, the operator (the human running this session) MUST set the parent's effort to the routed thinking tier.** Effort cannot be raised mid-spawn.

When this skill produces a routing recommendation, it MUST output a dispatch block in this shape:

```
1. Set effort: /effort <tier>      ← human runs this before step 2
2. Spawn agent:
   Agent({
     subagent_type: "<type>",
     description: "<3-5 word summary>",
     model: "<haiku|sonnet|opus>",
     prompt: "<self-contained brief>"
   })
```

The first line is a human-executed precondition. The second is the tool call the orchestrator should issue afterward, on the same turn or a subsequent one. If multiple routed steps need different efforts, list each as its own block and label them so the operator can step through them sequentially.

**Why effort, not model alone, has to be set first:** the model parameter on `Agent` does override the parent's model, but there is no analogous override for thinking budget. The spawned agent's thinking budget is inherited from the parent at spawn time. Without raising effort first, an Opus 4.7 orchestrator spawned by a `medium`-effort parent will run at `medium` regardless of what the routing table prescribed.

**Special case — Haiku 4.5 leaves:** Haiku has no thinking lever at all. For Haiku-routed steps, omit the "Set effort" line and spawn directly. The operator does not need to lower effort first; the Haiku model simply ignores any inherited thinking budget.

**Special case — staying in the main thread:** if the routing decision is for the current orchestrator (i.e., the agent reading this skill is itself the right model for the work), no Agent tool call is needed. Output a dispatch block that says `Spawn agent: (none — continue in main thread)` and surface the effort instruction so the operator can adjust if needed.

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

### Claude Opus 4.7 — frontier orchestration
- Model ID: `claude-opus-4-7` (1M-context variant: `claude-opus-4-7[1m]`)
- Context: 200K standard; 1M-context variant available for very large plans (premium)
- Effort levels available: `low`, `medium`, `high`, `extra high`, `max` (full five-tier ladder)
- Default thinking: `medium`
- Strengths: highest plan coherence, best at ambiguous and novel problems, strongest self-correction, holds long-horizon context across many sub-agents
- Use when: top-level planner or primary orchestrator for any complex workflow; ambiguous or partially-specified plans; multi-sub-agent coordination; high-stakes one-shot work where retry cost dominates the model cost

### Claude Sonnet 4.6 — production workhorse
- Model ID: `claude-sonnet-4-6`
- Context: 200K (1M-context variant available)
- Effort levels available: `low`, `medium`, `high`, `max` (no `extra high` — Sonnet's thinking ladder skips that tier; `max` is the cap)
- Default thinking: `medium`
- Strengths: strong across all plan-execution dimensions; substantially cheaper than Opus while retaining most of its planning quality; the right default for most production sub-agent work
- Use when: primary orchestrator where Opus cost is not justified; batch pipelines; most production plan deployments; sub-agents that handle a non-trivial bounded workflow

### Claude Haiku 4.5 — fast leaf executor
- Model ID: `claude-haiku-4-5-20251001`
- Context: 200K
- Effort levels available: **none — Haiku 4.5 has no extended-thinking lever**. Don't write a thinking-budget recommendation for Haiku; omit the field or use `n/a`. Quality dial happens at the model-tier level (promote to Sonnet) rather than within Haiku.
- Strengths: fastest Claude tier, lowest cost, very high throughput; well-suited to high-fan-out leaf execution
- Use when: leaf nodes with clear tool params; high-volume structured dispatch; latency-sensitive steps; large parallel fan-outs where rate limits and cost matter more than peak quality

---

## Extended thinking budgets

Claude's `thinking.budget_tokens` parameter controls how many tokens the model is allowed to spend on internal reasoning before producing user-visible output. **The ladder is per-model — not every Claude 4.x model exposes every tier:**

| Tier | Approx budget | Latency | Available on | Use for |
|------|---------------|---------|--------------|---------|
| `low` | ~2K tokens | fast | Opus 4.7, Sonnet 4.6 | leaf nodes with clear params; high-throughput dispatch; latency-sensitive steps; the cheapest tier that still benefits from any reasoning at all |
| `medium` | ~8K tokens | medium | Opus 4.7, Sonnet 4.6 | default for most plan steps; balanced quality/cost/latency; the right starting point |
| `high` | ~24K tokens | slow | Opus 4.7, Sonnet 4.6 | hard multi-system orchestration; complex acceptance criteria; error-recovery-critical steps; first upgrade from medium when quality matters |
| `extra high` | ~48K tokens | very slow | **Opus 4.7 only** | frontier orchestration; top-level planning over many sub-agents; ambiguous goals that need extensive self-correction. Sonnet does not expose this tier — promote to Opus if you need more than Sonnet's `high` |
| `max` | model maximum (≥ 64K, model-dependent) | slowest | Opus 4.7, Sonnet 4.6 | hardest async tasks; eval harnesses; long-horizon plans (20h+); novel problems where the model needs every token to converge. Cap this — most plan steps never need it |

**Haiku 4.5 has no extended-thinking lever.** Don't recommend a budget for it. If quality at Haiku falls short, promote the step to Sonnet 4.6 at `medium` rather than trying to dial Haiku up.

Cost implication: thinking tokens are billed as output tokens. In a multi-step plan, budget-tiering compounds — use the minimum budget that passes your quality bar per step.

Pin exact `budget_tokens` values per project if you need reproducibility — these tiers are intentionally qualitative because the cost-effective sweet spot shifts as model pricing evolves.

---

## Routing table

Match **task complexity × role** to the recommended combination. Haiku 4.5 entries have no effort tier (it has no extended-thinking lever); Sonnet 4.6 caps at `max` (no `extra high`); Opus 4.7 has the full ladder.

```
Role            | Trivial            | Moderate            | Complex             | Frontier
----------------|--------------------|---------------------|---------------------|-----------------------
Leaf node       | Haiku 4.5          | Haiku 4.5           | Sonnet 4.6/low      | Sonnet 4.6/medium
Sub-agent       | Haiku 4.5          | Sonnet 4.6/low      | Sonnet 4.6/medium   | Sonnet 4.6/high
Orchestrator    | Sonnet 4.6/medium  | Sonnet 4.6/medium   | Sonnet 4.6/high     | Opus 4.7/high
Top-level plnr  | Sonnet 4.6/medium  | Sonnet 4.6/high     | Opus 4.7/high       | Opus 4.7/extra high
```

`max` is reserved for genuine outliers — eval harnesses, multi-day async runs, novel research problems. It should not appear in a normal plan; if every phase wants `max`, the routing is wrong. On Sonnet, `max` is the only available "above-high" tier (no `extra high` exists); use it sparingly. On Opus, prefer `extra high` before `max`.

**Coding-specific note**: Sonnet 4.6 and Haiku 4.5 are both strong on agentic coding. For pure coding leaf work, prefer Haiku 4.5 over Sonnet 4.6/low — comparable quality, lower cost, lower latency, and no thinking-token bill at all.

**Haiku promotion rule**: If a Haiku leaf is producing quality misses, *do not* try to "increase its effort" (no such lever exists). Promote it to Sonnet 4.6 at `low` or `medium` instead. The decision is binary at the Haiku/Sonnet boundary.

**1M-context override**: any phase whose prompt + acceptance criteria + context dump exceeds 200K tokens must use the 1M-context variant of Opus 4.7 or Sonnet 4.6. Chunk or summarize before forcing a Haiku 4.5 step into >200K of context.

---

## Key heuristics

**Start at medium, dial from there.** Never default to `high` or above without a clear reason — every step up roughly doubles the thinking-token bill with diminishing returns on well-defined tasks. Always start at `medium` and move up only if the step shows measurable quality loss. This rule applies to Opus and Sonnet; Haiku has no dial to turn.

**Sonnet 4.6 at high ≈ Opus 4.7 at medium** for orchestration plan coherence. If you're running Sonnet at `high`, test Opus at `medium` — it's often roughly cost-equivalent and produces tighter plans. Sonnet at `max` is the right escape hatch when you need more than `high` but don't want to switch to Opus; otherwise prefer promoting to Opus.

**Skip `extra high` and `max` unless you've benchmarked.** The biggest cost increases sit at the top of the ladder. On Opus, promote `high` → `extra high` → `max` one step at a time, each only after observing quality degradation at the previous tier. On Sonnet the jump is `high` → `max` (no `extra high`); make that jump even more reluctantly because the cost gap is wider.

**Don't try to dial Haiku up.** Haiku 4.5 has no thinking budget. If a Haiku leaf is missing the quality bar, promote it to Sonnet 4.6 at `low`/`medium` — don't add a `thinking` field to a Haiku call. The decision at the Haiku/Sonnet boundary is binary.

**Tier your thinking within a plan.** Use `high`+ only on the orchestrator and on genuinely frontier-complex leaves. Assign `low` / `medium` to the bulk of leaf nodes (or use Haiku, which has no thinking spend at all). Token costs compound across every step, so budget misallocation at scale is expensive.

**Throughput vs quality tradeoff.** For parallel leaf execution (> 10 concurrent steps), prefer Haiku 4.5 to avoid rate limits and control cost. Promote to Sonnet 4.6 / `medium` only for steps that fail quality checks.

**Prompt caching is load-bearing for plan execution.** Long phase-doc prompts that are dispatched to many sub-agents in parallel should rely on prompt caching. Structure phase files so the stable preamble (Working tree, Goal, Why, Out of scope, Reference) is at the top and the variable per-sub-layer content is at the bottom — the prefix is what's cached.

**Don't use Opus 4.7 as a default.** Opus is substantially more expensive than Sonnet. Reserve it for the actual top-level planner and for frontier-complex orchestrators. Most plan steps — even non-trivial ones — should land on Sonnet 4.6.

---

## Output format for routing decisions

Every routing recommendation MUST include both the routing analysis AND a dispatch block telling the operator how to actually execute it. The dispatch block has two parts: an operator precondition (set effort on the parent before spawning), and the Agent tool call (with model override but no thinking parameter, since the Agent tool doesn't expose one).

### Sonnet sub-agent

```
Model: claude-sonnet-4-6
Thinking: medium
Rationale: sub-agent orchestrating a 5-step coding workflow; moderate complexity; latency-tolerant batch context
Estimated cost multiplier vs Haiku (thinking-off baseline): ~6×
Upgrade trigger: if error recovery fails > 20% of steps → promote to Opus 4.7 / high

Dispatch:
  1. Operator: set parent effort to `medium` (e.g. `/effort medium`) so the spawned agent inherits the right thinking budget.
  2. Orchestrator: invoke
     Agent({
       subagent_type: "general-purpose",
       description: "<3-5 word summary>",
       model: "sonnet",
       prompt: "<self-contained brief that doesn't assume conversation context>"
     })
```

### Opus orchestrator at high effort

```
Model: claude-opus-4-7
Thinking: high
Rationale: top-level planner over an ambiguous multi-system refactor with risky downstream impact
Estimated cost multiplier vs Sonnet/medium: ~5×
Upgrade trigger: if it stalls on replanning loops → promote to extra high (one tier, not two)

Dispatch:
  1. Operator: set parent effort to `high` (e.g. `/effort high`) BEFORE invoking the agent. Agent tool cannot raise thinking budget at spawn time — only inherit.
  2. Orchestrator: invoke
     Agent({
       subagent_type: "general-purpose",
       description: "<3-5 word summary>",
       model: "opus",
       prompt: "<self-contained brief>"
     })
```

### Haiku leaf (no thinking field at all)

```
Model: claude-haiku-4-5-20251001
Thinking: n/a
Rationale: high-fan-out mechanical edit; clear tool params; latency-sensitive
Estimated cost multiplier vs Sonnet/low: ~0.2×
Upgrade trigger: if quality misses → promote to Sonnet 4.6 / low (no in-model dial available)

Dispatch:
  1. Operator: no effort change needed (Haiku ignores inherited thinking budget).
  2. Orchestrator: invoke
     Agent({
       subagent_type: "general-purpose",     # or "Explore" for read-only lookups
       description: "<3-5 word summary>",
       model: "haiku",
       prompt: "<self-contained brief>"
     })
```

### Staying in the main thread

```
Model: claude-opus-4-7   (or whichever model is currently running)
Thinking: medium
Rationale: <why the current agent is the right runner — usually "holds load-bearing context that would cost more to re-establish in a sub-agent">

Dispatch:
  1. Operator: confirm parent effort is `medium`; raise via `/effort <tier>` if the routing tier is higher than the current one.
  2. Spawn agent: (none — continue in main thread; no Agent tool call needed)
```

### Multi-step plans

When routing a workflow with multiple differently-tiered steps, output one dispatch block per step in execution order. Label them so the operator can step through. Adjacent steps with the same effort tier can share one operator precondition:

```
=== Step A.1: Add HeroAnnouncement to gossip ===
Model: claude-sonnet-4-6 / Thinking: medium
Rationale: ...
Dispatch:
  1. Operator: /effort medium
  2. Agent({ subagent_type: "general-purpose", model: "sonnet", description: "...", prompt: "..." })

=== Step A.2: Fix AutoPlayerDecision leak ===
Model: claude-sonnet-4-6 / Thinking: high
Rationale: ...
Dispatch:
  1. Operator: /effort high   (raise from medium)
  2. Agent({ subagent_type: "general-purpose", model: "sonnet", description: "...", prompt: "..." })
```
