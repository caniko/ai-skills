---
name: multi-phase-plan-codex
description: Codex / GPT-5.x flavour of the multi-phase-plan shape — produces standalone phase markdown files routed via `gpt-plan-routing`. The user runs the phases themselves; this skill does NOT emit run scripts or dispatch shims. Supports a "verify" mode (inherited from `multi-phase-plan`) that checks each phase's Acceptance criteria against the current repo state; on a fully successful verify, auto-migrates contributor-worthy knowledge into the project's contributor docs and retires the plan files. Use when the work will be executed by Codex sessions (or any GPT-5.x agent), or when the user says "codex plan", "GPT plan", "multi-phase plan for codex", or "verify".
---

# Multi-phase plan (Codex flavour)

Codex-specific wrapper. Loads two shared skills:

- **`multi-phase-plan`** — base shape spec (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference, plus optional Risk profile / Strategy / Rollback drill / Failure modes for high-risk phases). Read it first for the commit-count split rule, dependency table, anti-patterns, chat-reply guidance, and the **verify mode** specification.
- **`multi-phase-dispatch`** — the parallel sub-layer model ("a layer consists of several layers"), eligibility checklist, and on-disk layout for multi-sub-layer phases.

This file only documents what's specific to Codex:

1. Model routing via `gpt-plan-routing`.
2. The Codex-flavoured "Recommended Codex model" callout block.

Modes (plan / verify / calibrate), the generic plan workflow, the routing-summary framing, and the calibration hook are shared — see [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared flavour skeleton". Verify mode is inherited from `multi-phase-plan` — see its verify section.

## 1. Model routing via `gpt-plan-routing`

For each phase (and each sub-layer, when present), consult **`gpt-plan-routing`** with the step's:
- **Task complexity**: trivial / moderate / complex / frontier.
- **Role in plan**: leaf / sub-agent / orchestrator / top-level planner.

Look up the routing matrix and pick the cheapest `(model, reasoning_effort)` combination that holds the quality bar.

Tier shorthand used in the callout block:
- `5.5 max` → frontier complexity at top-level / orchestrator roles.
- `5.5 high` → complex orchestration or non-trivial design decisions.
- `5.5 medium` → routine default for moderate complexity.
- `5.5 low` → trivial mechanical work.
- `deepseek-v4-pro high|max` → budget substitute for complex bounded work / cheap orchestration (per `gpt-plan-routing` "Budget override").
- `deepseek-v4-flash high` → cost-floor leaf / high-fan-out mechanical work.

DeepSeek v4 steps run through Codex's openai-compatible provider config and expose only two effective effort values (`high`, `max`) — never write `low`/`medium` for a DeepSeek callout; see `gpt-plan-routing` "DeepSeek v4 budget tiers".

Match the recommendation to the phase's complexity × role coordinates — don't inflate. Resist the urge to uniformly route to `max` "to be safe".

## 2. Callout block format

At the top of every phase file (or sub-layer file), immediately under the `# Phase N — Title` heading:

```markdown
> **Recommended Codex model: <GPT 5.5 <tier> | DeepSeek v4 <Flash high | Pro high|max>>**
>
> <One paragraph rationale: complexity, role in plan, what would
> happen if a smaller model ran this. Reference the gpt-plan-routing
> matrix's axes (task complexity × role-in-plan) implicitly — don't
> name the matrix in the file, just produce a recommendation that
> matches what the matrix would yield.>
```

The Codex routing summary table uses `Models` cells like `5.5 medium`, `5.4 ×2, 5.4-mini ×1`, `deepseek-v4-flash ×3 (high)`, `5.5 high`. Run each phase via fresh `codex exec` session, IDE side-pane, etc.

For the worked routing example, see the chessbender 5-phase set in [`multi-phase-plan`](../multi-phase-plan/SKILL.md) "Example".

## Codex-specific anti-patterns

- **Routing every phase to `max`.** `gpt-plan-routing` explicitly warns against this — it multiplies cost with diminishing returns. Use `low` and `medium` aggressively for mechanical phases; reserve `max` for genuinely frontier-complex work.

Shared anti-patterns (no orchestration scripts; verify is not a re-plan trigger) live in [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared anti-patterns".

## Reference

- Base shape spec + verify mode: **`multi-phase-plan`**.
- Parallel layering: **`multi-phase-dispatch`**.
- Model selection: **`gpt-plan-routing`** (routing table + key heuristics).
- Sister flavours: **`multi-phase-plan-claude`**, **`multi-phase-plan-mixed`**, **`multi-phase-plan-opencode`**.
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
