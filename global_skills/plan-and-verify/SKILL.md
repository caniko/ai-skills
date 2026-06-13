---
name: plan-and-verify
description: End-to-end workflow for prep, plan, and verify around multi-phase planning. Three invocation modes — prep routes a task description to `plan-research` or `consolidate-plan-sets` and emits a dossier hand-off; plan produces the standalone phase doc set via `multi-phase-plan` (model+effort routing is delegated to the `carter` CLI; provider/budget constraints from the user's wording pass through as carter flags) and accepts `--from-dossier PATH`; verify reads each phase's "Acceptance criteria" checklist and proves (or disproves) each item against the current repo state. Triggers on "plan and verify", "prep then plan", "break into phases then check the work", "verify the phases", "did the agents complete the plan correctly", or any request to audit a phase doc set against the codebase.
---

# Plan-and-verify

A three-mode skill that bookends a multi-agent plan execution and its
evidence-gathering prelude (each mode is detailed in its own section below):

- **`prep`** — decide whether the work needs a dossier first, routing to
  **`plan-research`** (fresh research-then-plan) or **`consolidate-plan-sets`**
  (collapse existing plan sets), or declining for small work. Stops at the
  dossier boundary.
- **`plan`** — delegate to `multi-phase-plan` to produce standalone phase docs
  under `docs/src/planning/<plan-name>/`. Model+effort routing is owned by the
  `carter` CLI; routing-constraint and `--from-dossier` handling are in Mode 1.
- **`verify`** — after the phases are executed, audit repo state against each
  phase's "Acceptance criteria" and report pass/fail per item. Provider-
  agnostic: every plan set shares the `multi-phase-plan` shape, and sub-layer
  directories are transparent to the criteria reader.

The modes share no hidden state: `prep` produces a reviewable `## Planner
Handoff` dossier; `plan` produces the phase docs; `verify` consumes them after
execution. When no recognized mode token leads the invocation, default to
**`plan`** for backwards compatibility (`/plan-and-verify <task>` ≡
`/plan-and-verify plan <task>`, not `prep`).

## When to use

- The user asks to prepare or research a non-trivial planning target before
  phase docs are written. Use `prep` and its decision tree.
- The user describes a non-trivial body of work and wants both the plan
  decomposition *and* a later audit pass.
- The user has finished (or believes they have finished) executing a
  phase doc set and asks "did the agents do this properly?", "verify the
  phases", "check the acceptance criteria", or similar.
- Any time the user wants to know whether a previously written plan was
  actually carried out — even if the plan was written without this skill,
  as long as the phase docs follow the `multi-phase-plan` shape (each
  has an "Acceptance criteria" checklist).

Don't use this for one-off tasks or for plans without explicit
acceptance criteria — there is nothing to verify.

## Mode 0 — `prep`

Invocation:
- `/plan-and-verify prep <task description>` — auto-route via the decision tree.
- `/plan-and-verify prep research <task description>` — force research
  (dispatches to `plan-research`).
- `/plan-and-verify prep consolidate <plan-glob>` — force consolidation
  (dispatches to `consolidate-plan-sets`).
- Natural language ("prep this and then plan it") works the same way; extract
  routing constraints from wording.

Decision tree:

1. If existing plan dirs are in scope (user named one, or
   `docs/planning/*` has stale-looking sets), route to
   `consolidate-plan-sets`.
2. Else if the work is genuinely new (no existing plan dirs) but
   non-trivial (multi-day, multi-subsystem, or the user explicitly asked
   for research), route to `plan-research`.
3. Else (small, single-session, single-fix), route to **no prep** — suggest
   the user invoke `plan` directly with their free-text. If the user
   insisted on `prep`, route to `plan-research` and let its right-size gate
   downshift to a findings note.

### Default routing for prep/plan dispatch

The downstream planner is always `multi-phase-plan`; per-phase model+effort
selection is delegated to the **`carter`** CLI. The only choice to extract
from the user's wording is the routing constraint set:

- No provider named → no constraint (carter routes across every enabled
  provider; this is the default and subsumes the old "mixed" flavour).
- User names an executor ("with claude", "codex plan", "opencode/deepseek
  plan") → `--provider <claude|codex|opencode>`.
- User signals cost-sensitivity ("cheapest", "minimize spend") → `--budget`.

This is the canonical rule; other skills cross-reference it instead of
restating it.

Steps:

1. Parse the invocation. The `prep` token is opt-in; do not treat a missing
   mode token as prep.
2. Apply the decision tree unless the user forced `research` or
   `consolidate`.
3. For `research`, invoke **`plan-research`** with the task description and
   any routing constraints extracted by the canonical rule above.
   `plan-research` loads
   `long-horizon-research`, emits a dossier with a literal
   `## Planner Handoff`, and may downshift to a findings note when the
   target is too small for a planning dossier.
4. For `consolidate`, invoke **`consolidate-plan-sets`** with the plan glob
   or named plan directories and any routing constraints extracted by the
   canonical rule above. This route is only for existing plan sets.
5. For no-prep, do not synthesize a dossier. Tell the user to invoke
   `/plan-and-verify plan <task description>` directly.
6. After `prep` completes, surface the dossier path or consolidated
   `README.md` path and remind the user that the next step is:
   ```bash
   /plan-and-verify plan --from-dossier <path>
   ```
   Do not auto-chain into `plan`; the dossier is a deliberate review
   boundary before phase docs are written.

## Mode 1 — `plan`

Invocation:
- `/plan-and-verify plan <task description>` — no routing constraint; carter
  routes across every enabled provider.
- `/plan-and-verify plan claude <task description>` — provider constraint
  (`--provider claude`); likewise `codex` and `opencode`.
- `/plan-and-verify plan --from-dossier <path> [task description]` —
  dossier-aware planning; pass the dossier path through to
  `multi-phase-plan`'s dossier input variant.
- `/plan-and-verify <task description>` — no mode token; default to this
  `plan` mode for backwards compatibility.
- Natural language ("plan and verify a feature flag sweep [with claude]")
  works the same way; extract routing constraints per the canonical rule.

Steps:

1. Extract routing constraints from the wording per "Default routing for
   prep/plan dispatch" above (`--provider`, `--budget`, or none).
2. Hand the task description to **`multi-phase-plan`** verbatim, along with
   the routing constraints. It routes every phase and sub-layer through the
   `carter` CLI and produces a standalone phase doc set only — it does
   **not** emit `run-*.sh` scripts, `run-all.sh`, `case "$provider"` shims,
   or any dispatch harness; the user runs the phases themselves.
   If the invocation includes `--from-dossier <path>`, pass that through
   instead of re-documenting or re-reading the `plan-handoff` fields here;
   **`multi-phase-plan`** owns the dossier-aware planning parse rules,
   precedence rules, and missing-field recovery.
3. After phase docs land under `docs/src/planning/<plan-name>/`, return
   the routing summary table and parallelism matrix to the user, plus a
   reminder that the user runs each phase themselves (fresh session per
   phase; no dispatch scripts are generated). When routing was
   unconstrained, surface a one-line provider-mix summary so the user can
   see at a glance how many phases landed on each provider.
4. Tell the user that `verify` is available as a follow-up once the
   phases have been executed.

Do not run any verification at this stage — the phases have not been
executed yet.

## Mode 2 — `verify`

Invocation: `/plan-and-verify verify [<plan-name>]` or natural language
("check that the feature flag sweep was completed properly"). If
`<plan-name>` is omitted, auto-detect by listing
`docs/src/planning/*/` and asking the user only if more than one
candidate exists.

Steps:

1. **Locate phase docs.** Resolve `docs/src/planning/<plan-name>/` and
   list its `NN-*.md` files in order. If the directory is missing, stop
   and tell the user there is no plan to verify.

2. **Survey execution evidence.** Quick orientation before running any
   checks:
   ```bash
   git log --oneline -20
   git status --short | head -40
   git diff --stat HEAD | head -40
   ```
   Note which commits and which working-tree changes appear related to
   the plan (filename overlap with the phase docs' "Files likely
   touched" sections is the strongest signal). If there is *no* relevant
   commit or staged change at all, stop and tell the user the plan
   appears un-executed — there is nothing to verify yet.

3. **Extract acceptance criteria.** For each phase doc, read its
   "Acceptance criteria" section and parse the `- [ ]` checklist into a
   structured worklist:
   ```
   Phase 01:
     1. <criterion>          -> command/file to check
     2. <criterion>          -> ...
   Phase 02:
     ...
   ```
   Also note each phase's "Files likely touched" and "Out of scope" so
   you can distinguish "the phase didn't do this" from "the phase
   explicitly punted this".

4. **Run the checks.** For each criterion, pick the cheapest evidence:
   - Manifest claims (`"x11" not in bevy.features = [...]`) → `rg` /
     `Read`.
   - Compile-graph claims (`cargo check --features X` exits 0) → run
     the actual `cargo check`. Use `--quiet` to keep output bounded.
   - Linkage / runtime claims (`ldd` shows `libwayland` and not
     `libX11`) → run the binary check on the existing
     `target/debug/<bin>` if present, otherwise build it.
   - Doc claims (`SUMMARY.md` contains entry) → `Read` /  `rg`.
   - Test-suite claims (`cargo test -p X --no-run` succeeds) → run it.

   Parallelise independent checks within a single tool-call batch when
   possible. Do not re-run expensive checks that are already proven by a
   prior check in the same verification pass.

5. **Distinguish three outcomes per criterion.** Each line in the report
   must be one of:
   - **PASS** — direct evidence (file content, command exit code, ldd
     output) shows the criterion is met.
   - **FAIL** — direct evidence shows the criterion is *not* met. Quote
     the contradicting evidence (file:line, command output snippet).
   - **N/A / explicit punt** — the phase doc's "Out of scope" or
     "Pitfalls" section, or the executor's own change-log doc (e.g.
     `COVERAGE-CHANGES.md`), explicitly defers this to another phase or
     flags it as a pre-existing issue unrelated to the plan. Cite the
     deferral source.

   Never silently skip a criterion. If you can't evaluate it, mark it
   `UNVERIFIED` with the reason.

6. **Look for over-delivery.** Read the diff in the touched areas for
   changes that go beyond the phase's stated plan. Note these — they
   are usually improvements (the executor saw an obvious adjacent fix
   and took it) but occasionally they are scope creep that warrants
   user attention. Quote the unexpected change with a one-sentence
   classification: "strict improvement", "neutral cleanup", or "scope
   creep — flag for user".

7. **Report.** Structure the chat reply:

   ```
   ## Verification results — <plan-name>

   **Phase 01 (<short title>)** — <one-sentence overall verdict>
   - [✓] <criterion 1> — <evidence>
   - [✓] <criterion 2> — <evidence>
   - [✗] <criterion 3> — <contradicting evidence>
   - [—] <criterion 4> — N/A: explicit punt per <source>

   ... (repeat per phase) ...

   **Build matrix verified live:** (only if applicable)
   - `cmd 1` → exit 0 ✓
   - `cmd 2` → exit 0 ✓
   ...

   **Over-delivery noted:** (only if applicable)
   - <file:line>: <description> — strict improvement / scope creep

   **Known caveats:** (only if applicable — pre-existing issues
   surfaced during verification but not introduced by the plan)
   - <issue> — pre-existing, see <source>.

   **Net assessment:** <one sentence — passed cleanly / passed with
   caveats / partial / failed>
   ```

   Don't recap the phase contents. The reader has the phase docs; the
   verification report is the dispatch.

## Doctrine: the coupled paradigm

Coupling exists because the planning family now has three substrate flows
that naturally hand work to each other: research -> plan, consolidate ->
plan, and plan -> verify. `plan-and-verify` gives users one entry point for
that arc while preserving the schema contract: prep producers write a
reviewable `## Planner Handoff`, `multi-phase-plan` consumes that dossier via
its from-dossier path, and verification proves the executed phase docs
against their acceptance criteria.

Paradigm diagram:

```text
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│ user ask │───>│ prep mode    │───>│ dossier with │───>│ plan mode│
│          │    │ ├ research   │    │ plan-handoff │    │ from-    │
│          │    │ └ consolidate│    │ schema       │    │ dossier  │
└──────────┘    └──────────────┘    └──────────────┘    └──────────┘
                                                               │
                                                               v
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ verify mode  │<───│ user executes│<───│ phase doc set│
│ + auto-retire│    │ phases       │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

Use `prep` per the Mode 0 decision tree when the target needs evidence before
phase docs are written or when existing plan directories must be collapsed
first; skip it for a single fix or single-session change where the user already
supplied enough evidence. `plan-research`'s right-size gate is the borderline
fallback, so don't synthesize a dossier just to make a small task look larger.

The hand-off boundaries are deliberate. `prep -> plan` pauses so the user
can review the dossier and resolve open decisions before phase docs exist.
`plan -> execute` pauses so the user can read the phase set and run those
phases in fresh sessions. `execute -> verify` pauses because verification
only has meaning after the phase work has landed in the repository. Do not
collapse these stages into one invocation.

Domain-grounded research has a different entry point. Use
`research-routing` for research-shaped work that is not meant to produce a
multi-phase planning dossier: audits, investigations, host probes,
downstream-impact checks, and other domain specialist probes. Use
`plan-research` only when the research output is supposed to feed
`multi-phase-plan` through the Planner Handoff contract.

Clean verification has an end-of-lifecycle consequence. The auto-retirement
rule and its `clean-shipped` fast path live with `multi-phase-plan` and
`retire-docs-planning`; this orchestrator's doctrine only names the
boundary. On a clean verify, durable knowledge moves into stable docs and
the completed planning surface is removed. On a non-clean verify, the plan
stays visible with the missing evidence reported.

### Worked example: WebGPU backend for a Bevy fork

```bash
/plan-and-verify prep "add WebGPU backend to bevy fork"
```
New, non-trivial work with no named stale plan dir → routes to `plan-research`,
which audits the fork and writes `docs/planning/webgpu-backend-research.md` with
a filled `## Planner Handoff`. The user reviews it and resolves any open
decision (e.g. native-only vs. WASM examples first), then:

```bash
/plan-and-verify plan --from-dossier docs/planning/webgpu-backend-research.md
```
Dispatches to `multi-phase-plan`, which reads the handoff (applying any
routing constraints it declares) and writes the phase set
(`docs/src/planning/webgpu-backend/README.md` + `NN-*.md`). The user runs those
phases in fresh sessions over the following days, then:

```bash
/plan-and-verify verify webgpu-backend
```
`verify` checks repo state + live commands against each phase's acceptance
criteria. On a clean pass (no gaps, no `missed-signal:` surprises) it delegates
to `retire-docs-planning clean-shipped docs/src/planning/webgpu-backend`:
durable knowledge moves to stable docs (`docs/src/webgpu.md`), `SUMMARY.md` is
pruned, and the plan dir is removed with `git rm -r`. End state: stable shipped
docs, no stale planning surface.

## Things to look out for during `verify`

- **Coverage docs.** Multi-phase plans frequently produce a sibling
  doc like `COVERAGE-CHANGES.md` or `AUDIT.md` under the same plan
  directory. Read these first — they often pre-record which checks the
  executor ran, with exit codes. Confirm their claims (don't trust
  blindly: re-run the highest-value checks yourself), but use them to
  prioritise.
- **Pre-existing failures.** A criterion failing for reasons *outside*
  the plan's scope (e.g. an unrelated compile error in a test crate)
  should be reported as a caveat, not as a phase failure. Cross-check
  against the diff: if the failing area wasn't touched, it's
  pre-existing.
- **Cargo feature unification surprises.** When verifying feature-flag
  work, always check the linkage (`ldd`) of a real built binary, not
  just `cargo check`. Cargo's feature unification can silently
  re-enable a feature you thought you'd stripped if any workspace
  member still pins it.
- **Phase-level acceptance vs. plan-level acceptance.** Each phase is
  judged on its own criteria. If Phase 02 says "Phase 03 must precede
  step 5" and Phase 03 was skipped, that's a Phase 02 failure
  (precondition unmet) even though Phase 03 *itself* has no failures.
- **Don't fix what you find.** This skill is a verification pass, not
  an execution pass. If checks fail, report them and stop. The user
  decides whether to spawn a follow-up agent or course-correct.

## Anti-patterns

- **Skipping the live build matrix.** A phase's compile-related
  acceptance criteria are not verified by reading the manifest; they
  require running `cargo check` (or equivalent) and observing exit
  codes. Don't substitute manifest-reading for compilation.
- **Trusting the coverage doc verbatim.** The executor's claimed exit
  codes can be stale (file edited after the check) or selectively
  reported. Re-run the load-bearing ones yourself.
- **Marking the whole plan PASS if 90% of criteria pass.** Per-phase
  verdicts must reflect their own criteria; the net assessment can be
  "passed with caveats" but individual `[✗]` lines must remain visible.
- **Bundling `plan` and `verify` in one invocation.** They are
  separated for a reason — execution happens between them, possibly
  days apart, possibly across many sessions. If the user asks for both
  in a single shot, plan first and tell them to come back for `verify`
  once the phases have been executed.
- **Auto-chaining prep → plan → verify in one invocation.** `prep` is a
  hand-off boundary on purpose; the user reviews the dossier before
  phases get written. `plan` is a hand-off boundary on purpose; the user
  reviews phase docs and executes them before `verify` runs. Do not
  collapse these.

Add new domain variants here as they emerge — each one should pin its
phase shape and its verification matrix so this generic skill stays
thin.

## Reference

- Prep producer: [`plan-research`](../plan-research/SKILL.md) —
  research-then-plan dossier wrapper.
- Prep/consolidation producer:
  [`consolidate-plan-sets`](../consolidate-plan-sets/SKILL.md) — collapse
  existing stale or overlapping plan sets into one current plan set with a
  Planner Handoff.
- Shared handoff contract: [`plan-handoff`](../plan-handoff/SKILL.md) —
  `## Planner Handoff` schema produced by prep and consumed by
  dossier-aware planning.
- Planner: [`multi-phase-plan`](../multi-phase-plan/SKILL.md) — the single
  multi-phase skill (shape spec, sub-layer model, dossier input, reroute);
  the user runs phases themselves (no orchestration scripts generated).
- Verify contract + clean-verify auto-retire rule:
  [`multi-phase-plan`](../multi-phase-plan/SKILL.md) "Mode: `verify`".
- Model + effort routing: the `carter` CLI
  (`https://codeberg.org/caniko/rs-carter`).
- Project convention for plan docs:
  `docs/src/planning/<plan-name>/NN-<slug>.md` (single-layer phases) or
  `docs/src/planning/<plan-name>/NN-<slug>/sub-MM-<slug>.md` (multi-sub-layer
  phases), indexed in `docs/src/SUMMARY.md` under a Planning section.
