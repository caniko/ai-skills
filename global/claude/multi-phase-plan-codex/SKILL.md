---
name: multi-phase-plan-codex
description: Codex / GPT-5.x flavour of the multi-phase-plan shape — produces standalone phase markdown files routed via `gpt-plan-routing`, plus per-phase CLI bundles that launch parallel sub-layer `codex` calls. Use when the work will be executed by Codex sessions (or any GPT-5.x agent), or when the user says "codex plan", "GPT plan", "multi-phase plan for codex". Loads `multi-phase-plan` for the phase-file shape and `multi-phase-dispatch` for the parallel sub-layer model and run-script template; this skill only supplies the Codex-specific routing callout and CLI invocation contract.
---

# Multi-phase plan (Codex flavour)

Codex-specific wrapper. Loads two shared skills:

- **`multi-phase-plan`** — base shape spec (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference, plus optional Risk profile / Strategy / Rollback drill / Failure modes for high-risk phases). Read it first for the commit-count split rule, dependency table, anti-patterns, and chat-reply guidance.
- **`multi-phase-dispatch`** — the parallel sub-layer model ("a layer consists of several layers"), eligibility checklist, on-disk layout for multi-sub-layer phases, `run-NN-<slug>.sh` template, logging contract, and `run-all.sh` cross-phase orchestrator.

This file only documents what's specific to Codex:

1. Model routing via `gpt-plan-routing`.
2. The Codex-flavoured "Recommended Codex model" callout block.
3. The Codex CLI invocation contract used inside the dispatch scripts.

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

## 3. CLI invocation contract

The dispatch script template lives in `multi-phase-dispatch`. The Codex flavour supplies the **`{INVOKE_LINE}`** substitution that runs one sub-layer non-interactively:

```bash
codex exec --model "$model" --skip-git-repo-check "$prompt" >"$log" 2>&1
```

The corresponding **`{SUB_LIST_BLOCK}`** uses three positional args (slug, model, sub-layer-filename):

```bash
run_sub "sub-01-<slug>" "gpt-5.4"      "sub-01-<slug>.md"
run_sub "sub-02-<slug>" "gpt-5.4-mini" "sub-02-<slug>.md"
run_sub "sub-03-<slug>" "gpt-5.4"      "sub-03-<slug>.md"
```

Single-layer phases (no sub-layer directory) are dispatched directly:

```bash
codex exec --model gpt-5.4 --skip-git-repo-check "$(cat 01-foo.md)"
```

Notes:
- `reasoning_effort` is set out-of-band (project default, env var, or codex profile) — the bundled `codex` CLI does not expose it as a per-call flag. The recommended-effort field in the callout block is for the human reading the phase doc, and for any harness that does honour it.
- Do not emit auth-bypass flags or destructive defaults. The user opts in at invocation time.
- If a project uses a wrapper around `codex` (a vendored launcher, an MCP-aware shim), substitute it for `codex exec` while keeping the same arg shape.

## Workflow

1. Load **`multi-phase-plan`** (base shape spec) and **`multi-phase-dispatch`** (parallel sub-layer model + run-script template).
2. Inventory the work, group into phases, build the dependency table (per the base skill).
3. For each phase, decide single-layer vs multi-sub-layer using the eligibility checklist in `multi-phase-dispatch`.
4. Route each phase (and each sub-layer) through **`gpt-plan-routing`**; emit the Codex callout block at the top of each file.
5. Write phase files / phase directories per the layout in `multi-phase-dispatch`.
6. For each multi-sub-layer phase, generate `run-NN-<slug>.sh` using the dispatch template with the Codex `{INVOKE_LINE}` and `{SUB_LIST_BLOCK}` substitutions above.
7. Optionally emit `run-all.sh` if independent phases can themselves fan out.
8. Wire into `docs/src/SUMMARY.md` if mdBook is in use.
9. Reply with the Codex routing summary table, parallelism matrix, and dispatch instructions.

## Routing summary in chat reply

| Phase | Layout | Sub-layers | Models | Blocking? | Dispatch |
|---|---|---|---|---|---|
| 01 | flat | — | 5.5 medium | no | `codex exec --model gpt-5.4 "$(cat 01-foo.md)"` |
| 02 | dir | 3 | 5.4 ×2, 5.4-mini ×1 | no | `bash run-02-bar.sh` |
| 03 | flat | — | 5.5 high | depends on 02 | `codex exec --model gpt-5.5 "$(cat 03-baz.md)"` |

Plus the parallelism matrix and any setup notes (`chmod +x run-*.sh`, `cd docs/src/planning/<plan-name>` before running).

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

(Generic parallel-dispatch anti-patterns live in `multi-phase-dispatch`; this list is Codex-specific only.)

- **Routing every phase to `max`.** `gpt-plan-routing` explicitly warns against this — it multiplies cost with diminishing returns. Use `low` and `medium` aggressively for mechanical phases; reserve `max` for genuinely frontier-complex work.
- **Mixing Claude model IDs into the run script.** This flavour emits Codex calls only. If a phase wants a Claude sub-layer, use **`multi-phase-plan-mixed`** instead.

## Reference

- Base shape spec: **`multi-phase-plan`**.
- Parallel layering + CLI dispatch: **`multi-phase-dispatch`**.
- Model selection: **`gpt-plan-routing`** (routing table + key heuristics).
- Sister flavours: **`multi-phase-plan-claude`**, **`multi-phase-plan-mixed`**.
- Project convention: `docs/src/planning/<plan-name>/{NN-<slug>.md | NN-<slug>/}`, indexed in `docs/src/SUMMARY.md`.
