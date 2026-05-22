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

## Modes

This skill is invoked in one of two modes, inherited from `multi-phase-plan`:

- **plan** — the default. Produce the phase doc set per the workflow below.
- **verify** — when the user says "verify" (or "check the phases", "did it all land"), do **not** re-plan. Run the verify workflow from `multi-phase-plan` against the most recent (or named) plan directory: read each phase's `## Acceptance criteria`, prove or disprove each item against the current repo state, and emit a per-phase pass/fail report. The user has already executed the phases themselves; verify just audits the result. On a fully successful verify, the post-verify step from `multi-phase-plan` automatically migrates any contributor-worthy knowledge into the project's contributor docs and `git rm`s the plan directory — see the base skill for the migration criteria and retirement steps.

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

Match the recommendation to the phase's complexity × role coordinates — don't inflate. Resist the urge to uniformly route to `max` "to be safe".

## 2. Callout block format

At the top of every phase file (or sub-layer file), immediately under the `# Phase N — Title` heading:

```markdown
> **Recommended Codex model: GPT 5.5 <tier>**
>
> <One paragraph rationale: complexity, role in plan, what would
> happen if a smaller model ran this. Reference the gpt-plan-routing
> matrix's axes (task complexity × role-in-plan) implicitly — don't
> name the matrix in the file, just produce a recommendation that
> matches what the matrix would yield.>
```

## Plan workflow

1. Load **`multi-phase-plan`** (base shape spec + verify mode) and **`multi-phase-dispatch`** (parallel sub-layer model).
2. Inventory the work, group into phases, build the dependency table (per the base skill).
3. For each phase, decide single-layer vs multi-sub-layer using the eligibility checklist in `multi-phase-dispatch`.
4. Route each phase (and each sub-layer) through **`gpt-plan-routing`**; emit the Codex callout block at the top of each file.
5. Write phase files / phase directories per the layout in `multi-phase-dispatch`. **Do not generate run scripts, dispatch shims, log directories, or `run-all.sh` orchestrators.** The user runs each phase themselves in a fresh Codex session.
6. Wire into `docs/src/SUMMARY.md` if mdBook is in use.
7. Reply with the Codex routing summary table, parallelism matrix, and a one-line reminder: *"Run the phases yourself; prompt `verify` when done to audit acceptance criteria."*

## Routing summary in chat reply

| Phase | Layout | Sub-layers | Models | Blocking? |
|---|---|---|---|---|
| 01 | flat | — | 5.5 medium | no |
| 02 | dir | 3 | 5.4 ×2, 5.4-mini ×1 | no |
| 03 | flat | — | 5.5 high | depends on 02 |

Plus the parallelism matrix and any setup notes. No `Dispatch` column — the user picks how they want to run each phase (fresh `codex exec` session, IDE side-pane, etc.).

## Example: 5-phase pre-landing-cleanup set

| Phase | Slug | Model | Why |
|---|---|---|---|
| A | dice-partition-forget | `5.5 medium` | Diagnosis in hand, fix is 4 lines, but needs smoke-log interpretation to verify. |
| B | warning-cleanup | `5.5 low` | Three mechanical edits, no design content, no log reading. |
| C | webpki-deprecations | `5.5 high` | Mechanical edits *plus* a non-trivial path choice (patch vendor / re-vendor / bump). The design call needs context, not raw output volume. |
| D | crosvm-version-override | `5.5 medium` | External-repo edit + commit + push without supervision; needs judgement on intentional-vs-bug. |
| E | nixos-scripted-initrd | `5.5 max` | Boot-order, GPU readiness, parallel-VM race exposure. Mediocre work ships a subtle regression. Worth `max`. |

The pattern: route to the cheapest tier that holds the quality bar for *this specific phase's* complexity × role.

## Codex-specific anti-patterns

- **Routing every phase to `max`.** `gpt-plan-routing` explicitly warns against this — it multiplies cost with diminishing returns. Use `low` and `medium` aggressively for mechanical phases; reserve `max` for genuinely frontier-complex work.
- **Emitting `run-*.sh` scripts, dispatch shims, or `run-all.sh` orchestrators.** Not this skill's job. The user runs phases themselves. If they want orchestration, they'll wire it themselves or use a separate tool.
- **Treating "verify" as a re-plan trigger.** Verify reads existing phase docs and audits them against the repo state — it does not rewrite phases or re-route models.

## Reference

- Base shape spec + verify mode: **`multi-phase-plan`**.
- Parallel layering: **`multi-phase-dispatch`**.
- Model selection: **`gpt-plan-routing`** (routing table + key heuristics).
- Sister flavours: **`multi-phase-plan-claude`**, **`multi-phase-plan-mixed`**.
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
