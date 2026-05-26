---
name: plan-and-verify
description: End-to-end workflow for prep, plan, and verify around multi-phase planning. Three invocation modes — `prep <task description>` routes to `plan-research` or `consolidate-plan-sets` and emits a dossier hand-off; `plan [codex|claude|mixed] <task description>` produces the standalone phase doc set via the chosen `multi-phase-plan-*` flavour using this skill's canonical default-flavour rule and accepts `--from-dossier <path>`; `verify [<plan-name>]` reads each phase's "Acceptance criteria" checklist and proves (or disproves) each item against the current repo state, flavour-agnostically. Triggers on "plan and verify", "prep then plan", "break into phases then check the work", "verify the phases", "did the agents complete the plan correctly", or any request to audit a phase doc set against the codebase.
---

# Plan-and-verify

A three-mode skill that bookends a multi-agent plan execution and its
evidence-gathering prelude:

0. **`prep`** — decide whether the work needs a dossier before planning.
   Route fresh research-then-plan flows to **`plan-research`**, route
   collapsing existing plan sets to **`consolidate-plan-sets`**, or
   decline prep for small work. `prep` stops at the dossier boundary and
   tells the user how to invoke `plan --from-dossier <path>` next.
1. **`plan`** — delegate to a `multi-phase-plan-*` flavour skill to produce a
   set of standalone phase docs under `docs/src/planning/<plan-name>/`.
   The flavour is picked up from the user's invocation:
   - `plan codex <…>` → **`multi-phase-plan-codex`** (GPT-5.x routing).
   - `plan claude <…>` → **`multi-phase-plan-claude`** (Claude routing +
     parallel sub-layer CLI bundles).
   - `plan mixed <…>` → **`multi-phase-plan-mixed`** (cross-provider
     routing — picks per-phase between Claude and Codex for cost-per-quality
     efficiency; emits a dispatch script that switches `claude` vs
     `codex` invocations per sub-layer).
   - `plan <…>` with no flavour token → apply this skill's canonical
     default-flavour rule.
   - `plan --from-dossier <path> <…>` → same flavour selection, but feed the
     base skill's dossier-aware planning input variant instead of relying only
     on free text.
2. **`verify`** — once the phases have been executed (typically by other
   Codex/Claude sessions), audit the resulting repo state against each
   phase's "Acceptance criteria" checklist and report pass/fail per item.
   Verification is flavour-agnostic — all flavours produce the same
   shape spec (per `multi-phase-plan`), and the only flavour-specific
   surface (Claude's `run-NN-*.sh` bundles, sub-layer directories) is
   transparent to the acceptance-criteria reader.

The modes share no hidden state across invocations. `prep` produces a
reviewable dossier with a `## Planner Handoff` contract; `plan` produces the
phase docs; `verify` consumes the phase docs after execution.

When no recognized mode token appears as the first word of the invocation,
default to **`plan`** mode for backwards compatibility. In other words,
`/plan-and-verify <task description>` means
`/plan-and-verify plan <task description>`, not `prep`.

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
- Natural language ("prep this and then plan it") works the same way; pick
  the sub-flavour from wording.

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

### Default flavour for prep/plan dispatch

The default downstream planner flavour = `multi-phase-plan-codex`. Switch to
`multi-phase-plan-claude` when the user names Claude or invokes via
`/multi-phase-plan-claude`; switch to `multi-phase-plan-mixed` when the user
signals cost-sensitivity ("cheapest", "minimize spend") or names the mixed
flavour explicitly. This is the canonical rule; other skills cross-reference
it instead of restating it.

Steps:

1. Parse the invocation. The `prep` token is opt-in; do not treat a missing
   mode token as prep.
2. Apply the decision tree unless the user forced `research` or
   `consolidate`.
3. For `research`, invoke **`plan-research`** with the task description and
   the downstream flavour selected by the canonical rule above.
   `plan-research` loads
   `long-horizon-research`, emits a dossier with a literal
   `## Planner Handoff`, and may downshift to a findings note when the
   target is too small for a planning dossier.
4. For `consolidate`, invoke **`consolidate-plan-sets`** with the plan glob
   or named plan directories and the downstream flavour selected by the
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
- `/plan-and-verify plan <task description>` — use this skill's canonical
  default-flavour rule.
- `/plan-and-verify plan codex <task description>` — explicit codex flavour.
- `/plan-and-verify plan claude <task description>` — claude flavour, with
  parallel sub-layer CLI bundles.
- `/plan-and-verify plan --from-dossier <path> [task description]` —
  dossier-aware planning; pass the dossier path through to the selected
  flavour's base `multi-phase-plan` input variant.
- `/plan-and-verify <task description>` — no mode token; default to this
  `plan` mode for backwards compatibility.
- Natural language ("plan and verify a feature flag sweep [with claude]")
  works the same way; pick the flavour from the user's wording, applying
  the canonical default-flavour rule when ambiguous.

Steps:

1. Pick the flavour skill:
   - `multi-phase-plan-codex` — Codex / GPT-5.x execution, routes via
     `gpt-plan-routing`. Dispatch scripts emit `codex exec` calls.
   - `multi-phase-plan-claude` — Claude execution, routes via
     `claude-plan-routing`. Dispatch scripts emit `claude --print` calls.
   - `multi-phase-plan-mixed` — Cross-provider execution; routes per
     phase/sub-layer through both routing skills and picks the
     `(provider, model, effort)` triple with the best cost-per-quality.
     Dispatch scripts contain a `case "$provider"` shim that selects
     `claude` vs `codex` per sub-layer.
2. Hand the task description to the chosen flavour skill verbatim. All
   three flavours load the **`multi-phase-plan`** generic shape spec and
   **`multi-phase-dispatch`** (parallel sub-layer model + run-script
   template) internally, then layer their flavour-specific routing
   callout block and CLI invocation contract on top.
   If the invocation includes `--from-dossier <path>`, pass that through
   instead of re-documenting or re-reading the `plan-handoff` fields here;
   the base **`multi-phase-plan`** skill owns the dossier-aware planning
   parse rules, precedence rules, and missing-field recovery. The codex,
   claude, and mixed flavour wrappers all honor that dossier input and
   cross-reference the base skill for field reads.
3. After phase docs land under `docs/src/planning/<plan-name>/`, return
   the flavour's routing table + parallelism matrix + dispatch
   instructions (which `run-NN-*.sh` scripts to invoke, in what order)
   to the user. The mixed flavour additionally surfaces a one-line
   provider-mix summary so the user can see at a glance how many phases
   landed on each provider.
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
reviewable `## Planner Handoff`, planner flavours consume that dossier via
their shared from-dossier path, and verification proves the executed phase
docs against their acceptance criteria.

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

Use `prep` when the planning target needs evidence before phase docs are
written, or when existing plan directories must be collapsed before a
current plan can be produced. The short decision tree is:

1. Existing plan dirs are in scope -> dispatch to `consolidate-plan-sets`.
2. New, non-trivial, multi-day or multi-subsystem work -> dispatch to
   `plan-research`.
3. Small, single-session work -> skip prep and invoke `plan` directly,
   unless the user insisted on prep; in that case `plan-research` may
   downshift to a findings note through its own right-size gate.

Skip prep for a single fix, a single-session change, or work where the user
already provided enough current evidence for direct planning. The
right-size gate in `plan-research` is the fallback for borderline cases, so
the orchestrator should not synthesize a dossier to make a small task look
larger than it is.

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

A user wants to add a WebGPU backend to a local Bevy fork, but the current
renderer state and prior experiments are unclear:

```bash
/plan-and-verify prep "add WebGPU backend to bevy fork"
```

`prep` sees new, non-trivial work and no named stale plan directory, so it
routes to `plan-research`. The research pass inspects the fork, audits any
prior WebGPU experiments, checks renderer/backend constraints, and writes a
dossier such as `docs/planning/webgpu-backend-research.md` with a filled
`## Planner Handoff`. The user reviews that dossier and resolves one open
decision it surfaced, for example whether the first phase should target
native-only WebGPU or include WASM examples immediately.

The user then asks the planner to consume the dossier explicitly:

```bash
/plan-and-verify plan --from-dossier docs/planning/webgpu-backend-research.md
```

The request dispatches to `multi-phase-plan-codex`, matching the dossier's
recommended flavour, and passes the dossier path through to the shared
from-dossier input. The planner reads the handoff according to
`multi-phase-plan`, then writes a concrete phase set such as
`docs/src/planning/webgpu-backend/README.md`,
`docs/src/planning/webgpu-backend/01-renderer-inventory.md`,
`docs/src/planning/webgpu-backend/02-backend-abstraction.md`, and
`docs/src/planning/webgpu-backend/03-webgpu-smoke-tests.md`.

Over the next several days, the user runs those phase files in fresh Codex
sessions. After the changes land, the user asks for the audit pass:

```bash
/plan-and-verify verify webgpu-backend
```

`verify` reads the acceptance criteria from
`docs/src/planning/webgpu-backend/`, checks the repository state and live
commands the criteria require, and reports the result. If every criterion
passes and there are no unresolved gaps or `missed-signal:` surprises, the
clean-verify path delegates retirement to `retire-docs-planning
clean-shipped docs/src/planning/webgpu-backend`. Durable backend knowledge
moves into stable docs such as `docs/src/webgpu.md`, `docs/src/SUMMARY.md`
is pruned, and the completed plan directory is removed with
`git rm -r docs/src/planning/webgpu-backend`. The end state is stable
documentation for the shipped WebGPU backend and no stale planning surface
left behind.

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
- Generic shape spec: `multi-phase-plan` (loaded by all flavours).
- Sibling skill: `multi-phase-plan-codex` — Codex / GPT-5.x flavour.
- Sibling skill: `multi-phase-plan-claude` — Claude flavour (Opus 4.7 /
  Sonnet 4.6 / Haiku 4.5).
- Sibling skill: `multi-phase-plan-mixed` — cross-provider flavour
  (cheapest-viable routing across Claude + Codex per phase/sub-layer).
- Shared dispatch: `multi-phase-dispatch` — parallel sub-layer model +
  `run-NN-<slug>.sh` template + `run-all.sh` orchestrator.
- Routing skills: `gpt-plan-routing` (Codex), `claude-plan-routing` (Claude).
- Project convention for plan docs:
  `docs/src/planning/<plan-name>/NN-<slug>.md` (single-layer phases) or
  `docs/src/planning/<plan-name>/NN-<slug>/sub-MM-<slug>.md` (Claude
  flavour, multi-sub-layer phases), indexed in `docs/src/SUMMARY.md`
  under a Planning section.
