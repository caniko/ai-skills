---
name: plan-and-verify
description: End-to-end workflow that pairs a `multi-phase-plan-*` flavour skill with an acceptance-criteria verification pass once the phases have been executed by other agents. Two invocation modes — `plan [codex|claude|mixed] <task description>` produces the standalone phase doc set via the chosen flavour (defaults to codex); `verify [<plan-name>]` reads each phase's "Acceptance criteria" checklist and proves (or disproves) each item against the current repo state, flavour-agnostically. Triggers on "plan and verify", "break into phases then check the work", "verify the phases", "did the agents complete the plan correctly", or any request to audit a phase doc set against the codebase.
---

# Plan-and-verify

A two-mode skill that bookends a multi-agent plan execution:

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
   - `plan <…>` with no flavour token → default to **`multi-phase-plan-codex`**
     for backwards compatibility (most existing plan sets are codex-flavoured).
     If the user signals cost-sensitivity ("cheapest", "most efficient",
     "minimize spend"), suggest `mixed` and ask whether to switch.
2. **`verify`** — once the phases have been executed (typically by other
   Codex/Claude sessions), audit the resulting repo state against each
   phase's "Acceptance criteria" checklist and report pass/fail per item.
   Verification is flavour-agnostic — both flavours produce the same
   shape spec (per `multi-phase-plan`), and the only flavour-specific
   surface (Claude's `run-NN-*.sh` bundles, sub-layer directories) is
   transparent to the acceptance-criteria reader.

The two modes share no state across invocations — the phase docs are the
contract.

## When to use

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

## Mode 1 — `plan`

Invocation:
- `/plan-and-verify plan <task description>` — defaults to the **codex** flavour.
- `/plan-and-verify plan codex <task description>` — explicit codex flavour.
- `/plan-and-verify plan claude <task description>` — claude flavour, with
  parallel sub-layer CLI bundles.
- Natural language ("plan and verify a feature flag sweep [with claude]")
  works the same way; pick the flavour from the user's wording, defaulting
  to codex when ambiguous.

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

Add new domain variants here as they emerge — each one should pin its
phase shape and its verification matrix so this generic skill stays
thin.

## Reference

- Generic shape spec: `multi-phase-plan` (loaded by both flavours).
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
