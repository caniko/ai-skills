---
name: multi-phase-dispatch
description: Shared reference for the parallel-layering model and CLI-bundle generation used by `multi-phase-plan-codex`, `multi-phase-plan-claude`, and `multi-phase-plan-mixed`. Defines the sub-layer concept ("a layer consists of several layers"), the on-disk layout for multi-sub-layer phases, the auto-generated `run-NN-<slug>.sh` template, and the cross-phase orchestrator script. Each flavour skill supplies its own CLI invocation contract; this skill owns everything else. Not user-invokable on its own — flavour skills load it.
---

# Multi-phase dispatch (shared parallel-layering + CLI-bundle reference)

DRY reference shared by every `multi-phase-plan-*` flavour. The flavour skills own:

- Which routing skill picks the model + effort per step.
- The exact form of the "Recommended model" callout block in each phase file.
- The exact **CLI invocation contract** (which binary, which flags) used inside the dispatch scripts.

This skill owns the rest of the parallel-execution surface — when and how to split a phase into parallel sub-layers, the on-disk layout, the run-script template (with placeholders the flavour fills in), the logging contract, and the cross-phase orchestrator. Flavour skills load this skill rather than copying its content.

## The parallel sub-layer model ("a layer consists of several layers")

A **phase** is a "layer" in the plan. A phase whose work decomposes naturally into N disjoint streams may declare those streams as **sub-layers** that fan out as parallel CLI calls. This is opt-in per phase — phases with a single coherent stream of work stay as a single layer (one CLI call).

### Sub-layer eligibility checklist

A phase qualifies for sub-layers only if **all** are true:

- The work decomposes into ≥ 2 disjoint streams (different files, different concerns, different repos).
- Each stream has its own coherent acceptance subcriteria, independently checkable.
- The streams do not need to communicate mid-execution (only the phase-level merge matters).
- The streams can be retried independently if one fails.
- The streams don't all collapse onto the same provider-side resource bottleneck (e.g., 8 sub-layers that each hammer the same external API serialise on rate limits regardless of your fan-out).

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
├── 03-baz.md
├── run-02-bar.sh                   # dispatch script for phase 02
└── run-all.sh                      # optional cross-phase orchestrator
```

Phase number `NN` is two-digit ordinal. Slug is `kebab-case`. The directory and its sibling `run-NN-<slug>.sh` share the same `NN-<slug>` stem.

### Per-sub-layer file shape

Each `sub-NN-<slug>.md` is itself a standalone phase doc per the base `multi-phase-plan` shape (Working tree / Goal / Why / Out of scope / Plan / Acceptance criteria / Files likely touched / Pitfalls / Reference), with the flavour's routing callout at the top. The sub-layer doc must be self-contained — the CLI call that consumes it receives only that file as its prompt context. No cross-sub-layer references for content; inline shared context into each one.

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
the merge (typically the orchestrator agent that dispatched the
sub-layers). What conflicts to expect and how to resolve them.>

## Phase-level acceptance criteria

<Criteria that can only be checked after all sub-layers complete.
Per-sub-layer criteria live in the sub-layer file.>

## Dispatch

Run `bash run-NN-<slug>.sh` from `docs/src/planning/<plan-name>/`.

## Reference

<…>
```

## Run-script template (`run-NN-<slug>.sh`)

For every multi-sub-layer phase, generate a sibling shell script that fans the sub-layers out in parallel, waits, and reports per-sub-layer exit status. The script lives next to the phase directory under the plan root. Skip the script entirely for single-sub-layer phases — the user invokes one CLI call directly.

The template below uses two flavour-supplied substitutions:

- **`{INVOKE_LINE}`** — the shell command that runs one sub-layer. It receives the variables `$model` (model id), `$prompt` (the sub-layer markdown content), `$slug` (sub-layer slug), and `$log` (per-sub-layer log path). It must redirect both stdout and stderr to `$log` and exit with the CLI's exit code.
- **`{SUB_LIST_BLOCK}`** — one `run_sub …` line per sub-layer, listing the slug, the model id from that sub-layer's routing callout, and the sub-layer markdown filename. For mixed-provider plans, this list also encodes the provider per line (see `multi-phase-plan-mixed`).

```bash
#!/usr/bin/env bash
# Auto-generated by multi-phase-plan-<flavour>.
# Phase NN — <Title>
# Dispatches the phase's sub-layers as parallel CLI calls.
#
# Run from the plan-name directory:
#   cd docs/src/planning/<plan-name>
#   bash run-NN-<slug>.sh
#
# Override the working directory the sub-layers operate in via WORKDIR=...
# Override the model per sub-layer by editing the call lines below.
set -uo pipefail

WORKDIR="${WORKDIR:-$(git rev-parse --show-toplevel)}"
PHASE_DIR="$(cd "$(dirname "$0")" && pwd)/NN-<slug>"
LOG_DIR="$PHASE_DIR/.runs/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$LOG_DIR"

echo "Phase NN dispatch → $LOG_DIR"
echo "Working directory for sub-layers: $WORKDIR"

declare -A PIDS=()
declare -A MODELS=()

run_sub() {
  # Args: slug, model, sub-layer-filename, [extra args passed to INVOKE_LINE]
  local slug="$1" model="$2" file="$3"
  shift 3
  local prompt log
  prompt="$(cat "$PHASE_DIR/$file")"
  log="$LOG_DIR/$slug.log"
  (
    cd "$WORKDIR"
    {INVOKE_LINE}
  ) &
  PIDS["$slug"]=$!
  MODELS["$slug"]="$model"
  echo "  → $slug ($model) PID ${PIDS[$slug]} → $log"
}

# --- sub-layers ---
{SUB_LIST_BLOCK}
# ------------------

FAIL=0
for slug in "${!PIDS[@]}"; do
  if wait "${PIDS[$slug]}"; then
    echo "  ✓ $slug (${MODELS[$slug]})"
  else
    rc=$?
    echo "  ✗ $slug (${MODELS[$slug]}, exit $rc) — see $LOG_DIR/$slug.log"
    FAIL=1
  fi
done

if [[ $FAIL -ne 0 ]]; then
  echo "Phase NN: one or more sub-layers failed. Logs: $LOG_DIR"
  exit 1
fi

echo "Phase NN: all sub-layers completed. Logs: $LOG_DIR"
echo "Next: review diffs, then perform the phase-level merge per the README."
```

### Per-flavour `{INVOKE_LINE}` examples

These belong in the flavour skill, not here — but the canonical forms are:

- **Codex** (`multi-phase-plan-codex`):
  `codex exec --model "$model" --skip-git-repo-check "$prompt" >"$log" 2>&1`
- **Claude** (`multi-phase-plan-claude`):
  `claude --model "$model" --print "$prompt" >"$log" 2>&1`
- **Mixed** (`multi-phase-plan-mixed`):
  A `case "$1" in codex) …; claude) …; esac` shim where the provider is the first argument to `run_sub`. The flavour skill defines the exact dispatch form.

If a project uses a different CLI binary (e.g., a vendored wrapper, an MCP-aware launcher), the flavour skill names that override.

## Logging contract

Every sub-layer must produce one log file at `LOG_DIR/<slug>.log` containing the full stdout + stderr of the CLI invocation. The directory is timestamp-stamped so repeat runs don't clobber prior logs. The orchestrator's post-mortem (when a sub-layer fails) starts from these logs — never assume the CLI surfaces the failure in real time.

Don't silently filter or pipe the CLI output. The whole point is to capture everything the CLI emitted so a fresh session can diagnose a failure without re-running.

## Cross-phase orchestrator (`run-all.sh`)

If multiple multi-sub-layer phases can themselves run in parallel (their "Can parallel with" cell in the base skill's dependency table contains another phase), additionally emit `run-all.sh` at the plan-name root. It dispatches independent phases' `run-NN-*.sh` scripts in parallel, then advances to the next dependency layer.

Skip `run-all.sh` if no phase pair is parallelisable — chaining `run-NN-*.sh` scripts sequentially is just `&&` in the dispatch instructions, no script needed.

Template (sketch — the flavour skill expands the layers from the dependency table):

```bash
#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")"

echo "Layer 1 (parallel): 01-foo, 02-bar"
bash run-01-foo.sh &
bash run-02-bar.sh &
wait || { echo "Layer 1 failed"; exit 1; }

echo "Layer 2 (sequential): 03-baz"
bash run-03-baz.sh || exit 1

echo "Layer 3 (parallel): 04-qux, 05-quux"
bash run-04-qux.sh &
bash run-05-quux.sh &
wait || { echo "Layer 3 failed"; exit 1; }

echo "All phases completed."
```

The "layers" here are *dependency layers* in the phase DAG, not sub-layers within a phase. Don't confuse the two: a dependency layer is a set of phases that can fan out together; a sub-layer is a parallel stream within a single phase. A plan can have both.

## What the chat reply should include (dispatch row)

The flavour skill's chat-reply table should have a `Dispatch` column with the exact command to run for each phase:

| Phase | Layout | Sub-layers | Models | Dispatch |
|---|---|---|---|---|
| 01 | flat | — | <model> | `<flavour CLI> -p "$(cat 01-foo.md)"` |
| 02 | dir | 3 | … | `bash run-02-bar.sh` |
| 03 | flat | — | <model> | `<flavour CLI> -p "$(cat 03-baz.md)"` |

Plus dispatch instructions: `chmod +x run-*.sh && cd docs/src/planning/<plan-name>` once before running anything, and either `bash run-all.sh` for the parallel orchestrator or a sequential `&&` chain when no orchestrator exists.

## Anti-patterns owned by this skill

- **Forcing sub-layers onto every phase.** Most phases are one coherent stream; one CLI call. Sub-layers are opt-in for genuinely disjoint parallelisable work. Splitting coherent work into 2–3 sub-layers makes the merge harder than the original work.
- **Sub-layers that touch the same file.** Defeats parallelism — the merge becomes manual conflict resolution. If two sub-layers want the same file, fold them into one sub-layer.
- **Routing every sub-layer to the top tier.** Sub-layers are leaf-ish by construction. Default to the cheap tier of the flavour's routing matrix; reserve the top tier for the merge/orchestrator (or skip it entirely).
- **Hard-coding the working directory in the script.** Keep `WORKDIR="${WORKDIR:-$(git rev-parse --show-toplevel)}"` so the same script works in a worktree or after a checkout move.
- **Sub-layer prompts that depend on each other.** Each `sub-NN-<slug>.md` is self-contained — no "see sub-02 for context". Put shared context in the phase `README.md` and inline it per sub-layer file.
- **Skipping per-sub-layer log files.** Without `LOG_DIR/<slug>.log`, a partial failure in a 5-way fan-out is a black box. The logging contract is load-bearing.
- **Adding `--dangerously-skip-permissions` or auth bypass flags into the generated script.** The user opts into those at invocation time; the planner doesn't bake them in.

## Reference

- Base shape spec: **`multi-phase-plan`**.
- Flavours that load this skill:
  - **`multi-phase-plan-codex`** — Codex / GPT-5.x CLI invocation contract.
  - **`multi-phase-plan-claude`** — Claude CLI invocation contract.
  - **`multi-phase-plan-mixed`** — provider-switching dispatch.
