---
name: multi-phase-plan-claude
description: Claude flavour of the multi-phase-plan shape — produces standalone phase markdown files routed via `claude-plan-routing` (Opus 4.7 / Sonnet 4.6 / Haiku 4.5). The user runs the phases themselves; this skill does NOT emit run scripts or dispatch shims. Supports a "verify" mode (inherited from `multi-phase-plan`) that checks each phase's Acceptance criteria against the current repo state; on a fully successful verify, auto-migrates contributor-worthy knowledge into the project's contributor docs and retires the plan files. Use when the work will be executed by Claude Code sessions, or when the user says "claude plan", "multi-phase plan for claude", "fan out with claude", or "verify".
---

# Multi-phase plan (Claude flavour)

Claude-specific wrapper. Loads two shared skills:

- **`multi-phase-plan`** — base shape spec (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference, plus optional Risk profile / Strategy / Rollback drill / Failure modes for high-risk phases). Read it first for the commit-count split rule, dependency table, anti-patterns, chat-reply guidance, and the **verify mode** specification.
- **`multi-phase-dispatch`** — the parallel sub-layer model ("a layer consists of several layers"), eligibility checklist, and on-disk layout for multi-sub-layer phases.

This file only documents what's specific to Claude:

1. Model routing via `claude-plan-routing` (Opus 4.7 / Sonnet 4.6 / Haiku 4.5).
2. The Claude-flavoured "Recommended Claude model" callout block.

Modes (plan / verify / calibrate), the generic plan workflow, the routing-summary framing, and the calibration hook are shared — see [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared flavour skeleton". Verify mode is inherited from `multi-phase-plan` — see its verify section.

## 1. Model routing via `claude-plan-routing`

For each phase (and each sub-layer, when present), consult **`claude-plan-routing`** with the step's:
- **Task complexity**: trivial / moderate / complex / frontier.
- **Role in plan**: leaf / sub-agent / orchestrator / top-level planner.

Look up the routing matrix and pick the cheapest `(model, thinking)` combination that holds the quality bar.

Model picker (the only valid model IDs for this flavour):

| Tier | Model ID | When |
|------|----------|------|
| Frontier orchestration | `claude-opus-4-7` | Top-level planner, complex orchestrators, frontier-novel work |
| Production workhorse | `claude-sonnet-4-6` | Most sub-agents and orchestrators; the right default |
| Fast leaf executor | `claude-haiku-4-5-20251001` | Leaf nodes, high-fan-out dispatch, latency-sensitive steps |

Thinking budget tiers (per `claude-plan-routing`) are **per-model**:
- **Opus 4.7** — full ladder: `low` / `medium` / `high` / `extra high` / `max`. Default `medium`.
- **Sonnet 4.6** — `low` / `medium` / `high` / `max` (no `extra high`). Default `medium`.
- **Haiku 4.5** — **no thinking lever** (omit the field or write `n/a`). If quality misses, promote to Sonnet 4.6 / `low`; never write a `thinking` value for a Haiku call.

Promote one tier at a time only with a stated reason; `max` is reserved for genuine outliers.

1M-context variants (`claude-opus-4-7[1m]`, `claude-sonnet-4-6[1m]`) only when prompt + context > 200K.

## 2. Callout block format

At the top of every phase file (or sub-layer file), immediately under the `# Phase N — Title` heading:

```markdown
> **Recommended Claude model: <Opus 4.7 | Sonnet 4.6 | Haiku 4.5> — thinking `<see below>`**
>
> Model ID: `<claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5-20251001>`
>
> <One paragraph rationale: complexity, role in plan, what would
> happen if a smaller model or lower thinking budget ran this.
> Reference the claude-plan-routing matrix's axes (task complexity ×
> role-in-plan) implicitly — don't name the matrix in the file, just
> produce a recommendation that matches what the matrix would yield.>
```

Valid `thinking` values, **per model**:
- Opus 4.7 → `low` | `medium` | `high` | `extra high` | `max`
- Sonnet 4.6 → `low` | `medium` | `high` | `max` (no `extra high`)
- Haiku 4.5 → omit the `thinking` field, or write `n/a`. Haiku has no extended-thinking lever; do not invent one.

Examples of valid callout headers:

```
> **Recommended Claude model: Opus 4.7 — thinking `extra high`**
> **Recommended Claude model: Sonnet 4.6 — thinking `high`**
> **Recommended Claude model: Haiku 4.5 — thinking `n/a`**
```

The Claude routing summary table uses `Models` cells like `Sonnet 4.6 / medium`, `Sonnet ×2 (medium, low), Haiku ×1 (no thinking)`, `Opus 4.7 / extra high`. Run each phase via fresh Claude Code session, IDE side-pane, Agent tool, etc.

## Claude-specific anti-patterns

- **Routing every sub-layer to Opus 4.7.** Sub-layers are leaf-ish; default to Sonnet 4.6 or Haiku 4.5. Reserve Opus for the merge step that combines the sub-layers, if anything.
- **Using `extra high` or `max` thinking for routine phases.** These tiers are for frontier work; if every phase wants `max`, the routing is wrong (see `claude-plan-routing`'s key heuristics).
- **Writing `extra high` for a Sonnet phase.** Sonnet 4.6's ladder skips that tier. The only valid Sonnet values are `low` / `medium` / `high` / `max`. If a Sonnet phase wants more than `high`, either jump to `max` (rare) or promote the model to Opus 4.7 at the appropriate tier.
- **Writing any `thinking` value for a Haiku phase.** Haiku 4.5 has no extended-thinking lever. The callout's `thinking` field must be `n/a` (or omitted). If quality misses, promote the *model* to Sonnet 4.6 at `low`/`medium` — don't pretend Haiku has a dial.
- **Forgetting prompt caching.** Long phase prompts that fan out to many sub-layers benefit from prompt caching. Put the stable preamble (Working tree, Goal, Why, Out of scope) at the top of each sub-layer file and the variable per-sub-layer content at the bottom — the prefix is what the cache keys on.

Shared anti-patterns (no orchestration scripts; verify is not a re-plan trigger) live in [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared anti-patterns".

## Reference

- Base shape spec + verify mode: **`multi-phase-plan`**.
- Parallel layering: **`multi-phase-dispatch`**.
- Model selection: **`claude-plan-routing`** (routing table + key heuristics).
- Sister flavours: **`multi-phase-plan-codex`**, **`multi-phase-plan-mixed`**, **`multi-phase-plan-opencode`**.
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
