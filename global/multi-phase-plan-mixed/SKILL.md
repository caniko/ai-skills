---
name: multi-phase-plan-mixed
description: Cross-provider flavour of the multi-phase-plan shape — routes each phase (and each sub-layer) to whichever provider (Claude or Codex/GPT-5.x) offers the best efficiency for that step's complexity × role, by consulting both `claude-plan-routing` and `gpt-plan-routing`. Produces a single phase doc set with explicit provider/model recommendations per phase. The user runs the phases themselves; this skill does NOT emit run scripts or dispatch shims. Supports a "verify" mode (inherited from `multi-phase-plan`) that checks each phase's Acceptance criteria against the current repo state; on a fully successful verify, auto-migrates contributor-worthy knowledge into the project's contributor docs and retires the plan files. Use when efficiency (cost-per-quality) is the optimization target, or when the user says "mixed plan", "use both providers", "cheapest viable plan", "cross-provider plan", or "verify".
---

# Multi-phase plan (mixed-provider flavour)

Cross-provider wrapper. Loads three shared skills plus both routing skills:

- **`multi-phase-plan`** — base shape spec + verify mode.
- **`multi-phase-dispatch`** — parallel sub-layer model + on-disk layout.
- **`gpt-plan-routing`** — GPT-5.x model + reasoning_effort selection.
- **`claude-plan-routing`** — Claude 4.x model + thinking-budget selection.

This file documents only what's cross-provider-specific:

1. The unified routing principle ("cheapest viable across both providers").
2. The cross-provider routing table (which provider/model wins per `complexity × role`).
3. The mixed callout block (declares provider explicitly).
4. Switch-cost rules — provider switching is not free; bias toward grouping adjacent same-provider phases.

Modes (plan / verify / calibrate), the generic plan workflow, the routing-summary framing, and the calibration hook are shared — see [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared flavour skeleton". Verify is provider-agnostic and inherited from `multi-phase-plan` — see its verify section. The mixed flavour consults *both* routing skills at step 4 of the shared plan workflow and emits the mixed callout block (below) at step 5.

## 1. The efficiency principle

For every step (phase or sub-layer), consult **both** routing skills and pick the `(provider, model, effort)` triple that has the best **cost-per-quality** for the step's complexity × role coordinates. Quality is the minimum bar that satisfies the phase's acceptance criteria; cost is the expected wall-time billable spend for that step.

The selection is not just "cheapest model" — Haiku at low effort is the cheapest Claude tier, but it's the wrong choice for an ambiguous orchestration step that will retry 4 times before converging. Optimize total expected cost across attempts, not unit cost of one attempt.

When two providers tie on quality at a given price point, prefer the provider that:
1. **Has the better tool for the step's job** (see the provider-strengths matrix below).
2. **Minimizes provider switches in the plan** (see switch-cost rules).
3. **Keeps prompt-cache hits warm** (Claude's prompt caching is mature; if the same prompt prefix is being dispatched to N sub-layers, Claude often wins on cache economics even when per-token pricing is closer).

## 2. Provider strengths matrix

Use these to break ties or to override the routing table when a step has a known strength match:

| Step pattern | Prefer | Why |
|---|---|---|
| Pure mechanical edits, high fan-out leaves | **GPT-5.4-mini** | Cheapest agentic-coding tier; very high throughput |
| Coding-specific bounded workflow | **GPT-5.4-mini** or **Haiku 4.5** | Comparable cost; pick by what's already warm in the plan |
| Long-horizon agentic terminal sessions | **GPT-5.4** (computer use) or **5.3-Codex** | OpenAI side has the strongest computer-use evals |
| Plan-coherence-heavy orchestration over many sub-agents | **Opus 4.7** or **GPT-5.5** | Both excellent; compare cost per the routing tables |
| Prompt-cache-friendly batch dispatch (same prefix → N sub-layers) | **Claude** (Sonnet or Haiku) | Mature prompt caching, ~90% discount on the cached prefix |
| Ambiguous, novel problem requiring extensive self-correction | **Opus 4.7** at `high`/`extra high` | Best convergence on open-ended problems |
| One-shot frontier task where retry cost dominates | **Opus 4.7** at `extra high` or **GPT-5.5** at `xhigh` | Pick by per-task pricing; both are top-tier |
| Latency-sensitive leaf (UI-driving, sub-second perceived) | **Haiku 4.5** at `low` | Fastest Claude tier; lowest TTFT |
| 1M-context spans (> 200K tokens) | **GPT-5.4/5.5** (1M default) or **Claude 1M variants** | Both have 1M options; Claude's 1M is premium-billed |

## 3. Unified routing table (cost-efficiency default)

Match **task complexity × role** to the recommended `(provider/model/effort)`. This is the **cost-efficient default** before applying strength overrides:

```
Role            | Trivial               | Moderate              | Complex                   | Frontier
----------------|-----------------------|-----------------------|---------------------------|---------------------------
Leaf node       | gpt 5.4-mini/low      | gpt 5.4-mini/medium   | claude haiku 4.5 (no dial)| claude sonnet 4.6/medium
Sub-agent       | claude haiku 4.5      | gpt 5.4/low           | claude sonnet 4.6/medium  | claude sonnet 4.6/high
Orchestrator    | gpt 5.4/medium        | gpt 5.4/high          | claude sonnet 4.6/high    | claude opus 4.7/high
Top-level plnr  | claude sonnet 4.6/med | claude sonnet 4.6/high| claude opus 4.7/high      | claude opus 4.7/extra high
```

Notes on the table:
- Haiku 4.5 cells have no effort tier — the model has no thinking lever. If quality at Haiku misses, the next step is a *model* promotion to Sonnet 4.6 at `low`/`medium`, not an effort bump.
- Sonnet 4.6 caps at `max` (no `extra high`); the only Claude tier that exposes `extra high` is Opus 4.7. In the table above, the `extra high` cell is therefore Opus-only.
- Codex effort uses `xhigh`, not `extra high` — keep the per-provider spelling.

This default reflects today's price/quality landscape:
- **Codex wins the cheap end** (`gpt-5.4-mini/low` ≪ Haiku at the same role on per-token price, though Haiku's no-thinking-bill flattens the gap at very low volume).
- **Claude wins the orchestration tier** (Sonnet at medium ≈ GPT-5.4 at high in plan coherence, often cheaper net of thinking tokens; prompt caching widens the gap on repeated dispatch).
- **Claude Opus owns top-of-stack** for top-level planning. GPT-5.5 is a substitutable peer; use it when GPT-5.5/xhigh's specific evals matter for the domain.

Re-derive this table per major model release — the equilibrium shifts.

**Coding-specific override**: replace any leaf-node recommendation with `gpt-5.4-mini` (or `5.3-Codex` on legacy pipelines) when the leaf is purely coding work. Saves ~1.5–2× over Claude leaf tiers on bulk coding.

**Computer-use override**: if a phase involves driving a desktop / browser / terminal autonomously, prefer `gpt-5.4` regardless of the table's recommendation — OpenAI's computer-use API is the differentiator.

## 4. Switch-cost rules

Provider switching is not free, even though it doesn't show up in per-token pricing:

- **No cache reuse across providers.** A Claude phase followed by a Codex phase pays full-rate input on both. Two adjacent Claude phases sharing a long preamble can hit prompt-cache; two adjacent Codex phases share Codex's cache.
- **No session continuity across providers.** A Codex phase that ran `codex exec` does not leave behind state that a `claude` follow-up can resume.
- **Cognitive overhead for the user.** The user is the one running phases — switching providers mid-plan means they juggle two CLIs / two sessions. Group same-provider phases when the routing table is indifferent.

Therefore, when two `(provider, model, effort)` choices tie on cost-per-quality:

1. Pick the provider that matches the **previous** phase in the dependency layer. Same provider → cache reuse + simpler hand-off.
2. If neither phase has a previous neighbor, pick by **expected number of phases at that provider** — if 4 of 6 phases are already routed to Claude, route the ambiguous one to Claude.
3. Only break the tie *toward the other provider* when the strength matrix or unified table strongly prefers it.

The win from a 5% cheaper unit price is usually erased by losing a prompt-cache hit on a long preamble.

## 5. Callout block format (mixed)

At the top of every phase file (or sub-layer file), declare the provider explicitly:

```markdown
> **Recommended: <Claude Opus 4.7 / Claude Sonnet 4.6 / Claude Haiku 4.5 / GPT 5.5 / GPT 5.4 / GPT 5.4-mini / GPT 5.3-Codex>**
> **Effort: <see per-model rules below>**
>
> Provider: `<claude | codex>`
> Model ID: `<claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5-20251001 | gpt-5.5 | gpt-5.4 | gpt-5.4-mini | gpt-5.3-codex>`
>
> <One paragraph rationale: complexity, role in plan, and why this
> provider/model wins over the alternative. Cite the strength match
> (if any) or the cost-efficiency tie-break that picked this provider.
> If the alternative was within ~10%, name it explicitly so a future
> reader can re-evaluate when pricing shifts.>
```

**Per-model valid `Effort` values** (`claude-plan-routing` + `gpt-plan-routing`):

| Provider / model | Valid effort tiers |
|---|---|
| Claude Opus 4.7 | `low` / `medium` / `high` / `extra high` / `max` |
| Claude Sonnet 4.6 | `low` / `medium` / `high` / `max` (no `extra high`) |
| Claude Haiku 4.5 | **n/a** — no extended-thinking lever; write `n/a` or omit |
| GPT 5.5 / 5.4 / 5.4-mini / 5.3-Codex | `low` / `medium` / `high` / `xhigh` (Codex uses `xhigh`, not `extra high`) |

Don't invent effort values that the chosen model doesn't expose — picking `extra high` on Sonnet or any effort on Haiku is a routing bug. If quality at Haiku is insufficient, promote the *model* (to Sonnet or to a comparable Codex tier), not the effort.

The two-line `Recommended` / `Effort` header makes mixed plans skimmable — a reader can fan through the phase set and see the provider mix at a glance.

## Mixed routing pass

The shared plan workflow lives in [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Plan workflow". The mixed flavour specializes its routing step: route each phase (and each sub-layer) through **both** `gpt-plan-routing` and `claude-plan-routing`, then apply the unified routing table for the default pick, the provider-strengths matrix to override on strength match, and the switch-cost rules to break ties. Emit the mixed callout block (provider declared explicitly) at the top of each file. The user runs each phase in whichever provider's CLI the callout names; the one-line dispatch reminder names that provider.

## Routing summary in chat reply

The mixed flavour's summary table adds a `Provider` column so the user can see the mix at a glance:

| Phase | Layout | Sub-layers | Provider | Models | Cost rank* | Blocking? |
|---|---|---|---|---|---|---|
| 01 | flat | — | codex | 5.4-mini / low | 1 (cheapest) | no |
| 02 | dir | 3 | mixed | codex 5.4-mini ×1, claude haiku ×2 | 2 | no |
| 03 | flat | — | claude | sonnet 4.6 / medium | 4 | depends on 02 |
| 04 | flat | — | claude | opus 4.7 / high | 6 (most expensive) | depends on 03 |

(\*) Cost rank is a relative ordering within this plan, not an absolute spend estimate. Lets the user see the cost gradient and challenge any unexpectedly high entries.

Plus the parallelism matrix and any setup notes. Include a one-line **provider mix summary**: "4 phases Claude (Opus ×1, Sonnet ×1, Haiku ×2), 2 phases Codex (5.4-mini ×2); 1 provider switch in the chain."

## Mixed-specific anti-patterns

- **Provider switching every phase "for variety".** Each switch costs cache reuse and adds a hand-off boundary for the user. If the routing table doesn't strongly prefer one provider over the other, pick by switch-cost rules.
- **Picking the unit-cheapest model without accounting for retries.** A Haiku/low pick that retries 5 times costs more than a Sonnet/medium pick that lands first try. Optimize *expected total cost*, including likely retries on ambiguous steps.
- **Ignoring prompt caching when fan-out is large.** A multi-sub-layer phase with 6+ sub-layers sharing a long prompt preamble usually wins by going all-Claude (cached prefix) even when the unit-cheapest models are mixed.
- **Cross-provider sub-layers that share a working state.** Sub-layers running on different providers don't share session state, prompt cache, or any in-flight reasoning. If two sub-layers in a phase need to be in-sync on anything beyond the merged commit, they must be on the same provider — or, more often, they should not be sub-layers at all (collapse into one).

Shared anti-patterns (no orchestration scripts — including provider-switching `case` shims; verify is not a re-plan trigger) live in [`multi-phase-dispatch`](../multi-phase-dispatch/SKILL.md) "Shared anti-patterns".

## Reference

- Base shape spec + verify mode: **`multi-phase-plan`**.
- Parallel layering: **`multi-phase-dispatch`**.
- Per-provider routing: **`gpt-plan-routing`**, **`claude-plan-routing`**.
- Sister flavours: **`multi-phase-plan-codex`** (Codex-only), **`multi-phase-plan-claude`** (Claude-only).
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
