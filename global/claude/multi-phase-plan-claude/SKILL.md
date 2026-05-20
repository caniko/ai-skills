---
name: multi-phase-plan-claude
description: Claude flavour of the multi-phase-plan shape — produces standalone phase markdown files routed via `claude-plan-routing` (Opus 4.7 / Sonnet 4.6 / Haiku 4.5), plus per-phase CLI bundles that launch parallel sub-layer `claude` calls. Use when the work will be executed by Claude Code sessions, or when the user says "claude plan", "multi-phase plan for claude", "fan out with claude". Loads `multi-phase-plan` for the phase-file shape and `multi-phase-dispatch` for the parallel sub-layer model and run-script template; this skill only supplies the Claude-specific routing callout and CLI invocation contract.
---

# Multi-phase plan (Claude flavour)

Claude-specific wrapper. Loads two shared skills:

- **`multi-phase-plan`** — base shape spec (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference, plus optional Risk profile / Strategy / Rollback drill / Failure modes for high-risk phases). Read it first for the commit-count split rule, dependency table, anti-patterns, and chat-reply guidance.
- **`multi-phase-dispatch`** — the parallel sub-layer model ("a layer consists of several layers"), eligibility checklist, on-disk layout for multi-sub-layer phases, `run-NN-<slug>.sh` template, logging contract, and `run-all.sh` cross-phase orchestrator.

This file only documents what's specific to Claude:

1. Model routing via `claude-plan-routing` (Opus 4.7 / Sonnet 4.6 / Haiku 4.5).
2. The Claude-flavoured "Recommended Claude model" callout block.
3. The Claude CLI invocation contract used inside the dispatch scripts.

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

## 3. CLI invocation contract

The dispatch script template lives in `multi-phase-dispatch`. The Claude flavour supplies the **`{INVOKE_LINE}`** substitution that runs one sub-layer non-interactively:

```bash
claude --model "$model" --print "$prompt" >"$log" 2>&1
```

The corresponding **`{SUB_LIST_BLOCK}`** uses three positional args (slug, model, sub-layer-filename):

```bash
run_sub "sub-01-<slug>" "claude-sonnet-4-6"         "sub-01-<slug>.md"
run_sub "sub-02-<slug>" "claude-haiku-4-5-20251001" "sub-02-<slug>.md"
run_sub "sub-03-<slug>" "claude-sonnet-4-6"         "sub-03-<slug>.md"
```

Single-layer phases (no sub-layer directory) are dispatched directly:

```bash
claude --model claude-sonnet-4-6 --print "$(cat 01-foo.md)"
```

Notes:
- Thinking budget is configured on the Claude side via the API or environment, not as a CLI flag (the `--thinking` flag accepts only `enable`/`disable` in the bundled CLI). Use the project's standard mechanism for setting `thinking.budget_tokens` per the routing recommendation, or trust the model default if your harness doesn't expose it. The recommended-thinking field in the callout block is for the human reading the phase doc, and for any harness that does honour it.
- Do not emit `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`, or auth bypass flags. The user opts in at invocation time if they want them.
- Do not emit `--session-id` overrides — each sub-layer gets a fresh session by design.

## Workflow

1. Load **`multi-phase-plan`** (base shape spec) and **`multi-phase-dispatch`** (parallel sub-layer model + run-script template).
2. Inventory the work, group into phases, build the dependency table (per the base skill).
3. For each phase, decide single-layer vs multi-sub-layer using the eligibility checklist in `multi-phase-dispatch`.
4. Route each phase (and each sub-layer) through **`claude-plan-routing`**; emit the Claude callout block at the top of each file.
5. Write phase files / phase directories per the layout in `multi-phase-dispatch`.
6. For each multi-sub-layer phase, generate `run-NN-<slug>.sh` using the dispatch template with the Claude `{INVOKE_LINE}` and `{SUB_LIST_BLOCK}` substitutions above.
7. Optionally emit `run-all.sh` if independent phases can themselves fan out.
8. Wire into `docs/src/SUMMARY.md` if mdBook is in use.
9. Reply with the Claude routing summary table, parallelism matrix, and dispatch instructions.

## Routing summary in chat reply

| Phase | Layout | Sub-layers | Models | Blocking? | Dispatch |
|---|---|---|---|---|---|
| 01 | flat | — | Sonnet 4.6 / medium | no | `claude --model claude-sonnet-4-6 -p "$(cat 01-foo.md)"` |
| 02 | dir | 3 | Sonnet ×2 (medium, low), Haiku ×1 (no thinking) | no | `bash run-02-bar.sh` |
| 03 | flat | — | Opus 4.7 / extra high | depends on 02 | `claude --model claude-opus-4-7 -p "$(cat 03-baz.md)"` |

Plus the parallelism matrix (which phases can fan out together via `run-all.sh`, which must serialise) and any setup notes (`chmod +x run-*.sh`, `cd docs/src/planning/<plan-name>` before running).

## Claude-specific anti-patterns

(Generic parallel-dispatch anti-patterns live in `multi-phase-dispatch`; this list is Claude-specific only.)

- **Routing every sub-layer to Opus 4.7.** Sub-layers are leaf-ish; default to Sonnet 4.6 or Haiku 4.5. Reserve Opus for the orchestrator that merges the sub-layers, if anything.
- **Using `extra high` or `max` thinking for routine phases.** These tiers are for frontier work; if every phase wants `max`, the routing is wrong (see `claude-plan-routing`'s key heuristics).
- **Writing `extra high` for a Sonnet phase.** Sonnet 4.6's ladder skips that tier. The only valid Sonnet values are `low` / `medium` / `high` / `max`. If a Sonnet phase wants more than `high`, either jump to `max` (rare) or promote the model to Opus 4.7 at the appropriate tier.
- **Writing any `thinking` value for a Haiku phase.** Haiku 4.5 has no extended-thinking lever. The callout's `thinking` field must be `n/a` (or omitted). If quality misses, promote the *model* to Sonnet 4.6 at `low`/`medium` — don't pretend Haiku has a dial.
- **Forgetting prompt caching.** Long phase prompts that fan out to many sub-layers benefit from prompt caching. Put the stable preamble (Working tree, Goal, Why, Out of scope) at the top of each sub-layer file and the variable per-sub-layer content at the bottom — the prefix is what the cache keys on.
- **Mixing Codex model IDs into the run script.** This flavour emits Claude calls only. If a phase wants a Codex sub-layer, use **`multi-phase-plan-mixed`** instead.

## Reference

- Base shape spec: **`multi-phase-plan`**.
- Parallel layering + CLI dispatch: **`multi-phase-dispatch`**.
- Model selection: **`claude-plan-routing`** (routing table + key heuristics).
- Sister flavours: **`multi-phase-plan-codex`**, **`multi-phase-plan-mixed`**.
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
