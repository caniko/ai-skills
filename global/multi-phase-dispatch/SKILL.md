---
name: multi-phase-dispatch
description: Shared reference for the parallel sub-layer model used by `multi-phase-plan-codex`, `multi-phase-plan-claude`, `multi-phase-plan-mixed`, and `multi-phase-plan-opencode`. Defines the sub-layer concept ("a layer consists of several layers"), the eligibility checklist, the on-disk layout for multi-sub-layer phases, and per-sub-layer routing rules. The user runs phases themselves — this skill does NOT generate orchestration scripts. Not user-invokable on its own; flavour skills load it.
---

# Multi-phase dispatch (shared parallel-layering reference)

DRY reference shared by every `multi-phase-plan-*` flavour. The flavour skills own:

- Which routing skill picks the model + effort per step.
- The exact form of the "Recommended model" callout block in each phase file.

This skill owns:

- The parallel sub-layer model ("a layer consists of several layers").
- The eligibility checklist that decides whether a phase splits into sub-layers.
- The on-disk layout for multi-sub-layer phases.
- Per-sub-layer routing guidance.

**This skill does not generate run scripts, dispatch shims, logging harnesses, or cross-phase orchestrators.** The user runs each phase themselves (typically by opening a fresh agent session pointed at the phase markdown). Phase docs are the artifact; orchestration is the user's job.

## The parallel sub-layer model ("a layer consists of several layers")

A **phase** is a "layer" in the plan. A phase whose work decomposes naturally into N disjoint streams may declare those streams as **sub-layers** — separate markdown files in a phase directory, each independently consumable by a fresh agent session. This is opt-in per phase — phases with a single coherent stream of work stay as a single layer (one markdown file).

### Sub-layer eligibility checklist

A phase qualifies for sub-layers only if **all** are true:

- The work decomposes into ≥ 2 disjoint streams (different files, different concerns, different repos).
- Each stream has its own coherent acceptance subcriteria, independently checkable.
- The streams do not need to communicate mid-execution (only the phase-level merge matters).
- The streams can be retried independently if one fails.
- The streams don't all collapse onto the same provider-side resource bottleneck (e.g., 8 sub-layers that each hammer the same external API serialise on rate limits regardless of how the user fans them out).

If any of these fail, keep the phase as a single layer — splitting buys nothing and complicates the merge. "Edit half the file in sub-01, the other half in sub-02" is a classic anti-pattern.

### Sub-layer routing

Each sub-layer is routed independently through the flavour's routing skill — the sub-layer is itself usually a *leaf node* or small *sub-agent* role, regardless of the parent phase's role. Default sub-layers to cheaper tiers than the parent orchestrator. Routing every sub-layer to the top tier defeats the cost benefit of parallelisation.

## On-disk layout

Single-layer phases stay as flat `NN-<slug>.md` files under the plan directory. Multi-sub-layer phases become a directory:

```
docs/src/planning/<plan-name>/
├── 01-foo.md                       # single-layer phase
├── 02-bar/                         # multi-sub-layer phase
│   ├── README.md                   # phase-level overview + merge plan
│   ├── sub-01-<slug>.md            # one sub-layer, fully standalone
│   ├── sub-02-<slug>.md            # — each with its own routing callout
│   └── sub-03-<slug>.md
└── 03-baz.md
```

Phase number `NN` is two-digit ordinal. Slug is `kebab-case`.

No `run-NN-<slug>.sh`, no `run-all.sh`, no `.runs/` log directory. The user dispatches phases (and sub-layers) themselves via whichever mechanism they prefer — fresh agent sessions, manual review, IDE side-pane, etc.

### Per-sub-layer file shape

Each `sub-NN-<slug>.md` is itself a standalone phase doc per the base `multi-phase-plan` shape (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference), with the flavour's routing callout at the top. The sub-layer doc must be self-contained — when the user dispatches it, the consuming agent only sees that one file. No cross-sub-layer references for content; inline shared context into each one.

### Phase `README.md` shape (multi-sub-layer phases only)

```markdown
# Phase NN — <Title>

> **Recommended model for merge/orchestration: <flavour fills this in>**

## Sub-layers

| # | Slug | Model | Touches | Sub-layer file |
|---|------|-------|---------|----------------|
| 01 | <slug> | <flavour-specific> | <files> | [sub-01-<slug>.md](./sub-01-<slug>.md) |
| 02 | <slug> | <flavour-specific> | <files> | [sub-02-<slug>.md](./sub-02-<slug>.md) |
| 03 | <slug> | <flavour-specific> | <files> | [sub-03-<slug>.md](./sub-03-<slug>.md) |

## Goal (phase-level)

<Outcome the merged sub-layers achieve together.>

## Why this matters now

<…>

## Out of scope

<…>

## Merge plan

<How the sub-layers' outputs are combined into one commit. Who runs
the merge (the user, after dispatching the sub-layers). What
conflicts to expect and how to resolve them.>

## Phase-level acceptance criteria

<Criteria that can only be checked after all sub-layers complete.
Per-sub-layer criteria live in the sub-layer file. These are also
what the verify mode checks at the phase level.>

## Reference

<…>
```

The phase README is for the human reading the plan. It describes how the user is expected to fan out the sub-layers and merge them. It does not prescribe a script or harness.

## Shared flavour skeleton

The flavour skills (`multi-phase-plan-codex`, `-claude`, `-mixed`, `-opencode`) share the same modes, plan workflow, routing-summary framing, and calibration hook. They are defined once here; each flavour adds only its routing skill(s), callout-block template, and routing-specific anti-patterns.

### Modes (inherited from `multi-phase-plan`)

Each flavour is invoked in one of three modes, inherited from [`multi-phase-plan`](../multi-phase-plan/SKILL.md):

- **plan** — the default. Produce the phase doc set per the workflow below. Dossier-aware: when invoked with a Planner Handoff dossier path (per `multi-phase-plan` "Dossier-aware planning"), read the dossier's plan-handoff section and use it as the planning brief. See the base skill for field reads, override rules, and missing-field behavior.
- **verify** — inherited from `multi-phase-plan`; see its verify section. The user has already executed the phases; verify only audits the result and (on a clean verify) auto-retires.
- **calibrate** — invoke the base skill's `calibrate` mode; see `multi-phase-plan` and its `references/calibration.md` "Mode: calibrate". The flavour's routing skill(s) are *not* consulted for calibrate — it analyzes past plans, it doesn't route new ones. Shells out to `skillnet calibration walkthrough`; users with the skillnet HM module enabled have the binary and config available (`programs.skillnet.enable = true` via ai-skills' re-exported HM module), but calibration remains an explicit CLI workflow.

### Plan workflow

1. Load [`multi-phase-plan`](../multi-phase-plan/SKILL.md) (base shape spec + verify mode) and this skill (parallel sub-layer model).
2. Inventory the work, group into phases, build the dependency table (per the base skill).
3. For each phase, decide single-layer vs multi-sub-layer using the eligibility checklist above.
4. Route each phase (and each sub-layer) through the flavour's routing skill(s); emit the flavour's callout block at the top of each file.
5. Write phase files / phase directories per the on-disk layout above. **Do not generate run scripts, dispatch shims, log directories, or `run-all.sh` orchestrators.** The user runs each phase themselves in a fresh session.
6. Wire into `docs/src/SUMMARY.md` if mdBook is in use.
7. Reply with the flavour's routing summary table, parallelism matrix, and a one-line reminder: *"Run the phases yourself; prompt `verify` when done to audit acceptance criteria."*
8. **Record for calibration.** Follow the base skill's end-of-plan hook: run `skillnet calibration init <plan-dir>`, and if any meta-heuristic fires, run `skillnet calibration record <plan-dir>`. Surface in the chat reply per the base workflow.

### Routing summary in chat reply

Each flavour replies with a routing summary table (Phase × Layout × Sub-layers × Models × Blocking?, plus a Provider column for the mixed flavour), the parallelism matrix, and any setup notes. No `Dispatch` column — the user picks how they want to run each phase (fresh session, IDE side-pane, Agent tool, etc.).

### Shared anti-patterns (all flavours)

- **Emitting `run-*.sh` scripts, dispatch shims, or `run-all.sh` orchestrators.** Not these skills' job (see "Emitting orchestration scripts" below). The user runs phases themselves. If they want orchestration, they'll wire it themselves or use a separate tool.
- **Treating "verify" as a re-plan trigger.** Verify reads existing phase docs and audits them against the repo state — it does not rewrite phases or re-route models/providers.

## Parallelism guidance

Default each phase to "independent unless flagged" — explicit constraints belong in the phase doc, not in tribal knowledge. The base `multi-phase-plan` skill defines the dependency table; sub-layers inherit the same rules within a phase.

Within a multi-sub-layer phase, the user is free to:
- Open N agent sessions and dispatch all sub-layers in parallel.
- Dispatch them sequentially if they prefer to read intermediate diffs.
- Skip a sub-layer and revisit it later (sub-layers are independent by construction).

The plan does not lock the user into any one dispatch strategy.

## Anti-patterns owned by this skill

- **Forcing sub-layers onto every phase.** Most phases are one coherent stream; one markdown file. Sub-layers are opt-in for genuinely disjoint parallelisable work. Splitting coherent work into 2–3 sub-layers makes the merge harder than the original work.
- **Sub-layers that touch the same file.** Defeats parallelism — the merge becomes manual conflict resolution. If two sub-layers want the same file, fold them into one sub-layer.
- **Routing every sub-layer to the top tier.** Sub-layers are leaf-ish by construction. Default to the cheap tier of the flavour's routing matrix; reserve the top tier for the merge step (or skip it entirely).
- **Sub-layer prompts that depend on each other.** Each `sub-NN-<slug>.md` is self-contained — no "see sub-02 for context". Put shared context in the phase `README.md` and inline it per sub-layer file.
- **Emitting orchestration scripts.** The user runs phases themselves. Generating `run-*.sh` files, dispatch shims, parallel `wait`-loops, log directories, or `case $provider` switches is out of scope for this skill family. If the user wants automation, they will ask for it explicitly (or use a separate tool like `/yeehaw`).

## Reference

- Base shape spec: **`multi-phase-plan`**.
- Flavours that load this skill:
  - **`multi-phase-plan-codex`** — Codex / GPT-5.x routing callout.
  - **`multi-phase-plan-claude`** — Claude routing callout.
  - **`multi-phase-plan-mixed`** — cross-provider routing callout.
  - **`multi-phase-plan-opencode`** — opencode / DeepSeek v4 routing callout + export mode.
