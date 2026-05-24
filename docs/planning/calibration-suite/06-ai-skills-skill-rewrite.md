# Phase 06 — ai-skills SKILL.md rewrite

> **Recommended Codex model: GPT 5.5 high**
>
> Substantive content rewrite of the base
> `global/multi-phase-plan/SKILL.md`. Drops the 3–8 phase cap,
> adds per-phase shape rules, documents the heuristics catalog
> (cross-referencing skillnet as source-of-truth for live
> thresholds), documents sidecar schema, tag conventions, the
> `surprises` convention, meta-heuristics. The skill becomes a
> *thin* reference layer over skillnet rather than re-implementing
> the algorithm. Writing-heavy, design-heavy — but considerably
> simpler than the earlier draft because skillnet now owns the
> catalog. `medium` would underspec the contract; `max` is
> overkill for a documentation phase.

## Working tree

`~/canix/Projects/ai-skills`.

## Goal

`global/multi-phase-plan/SKILL.md` is rewritten to:

1. **Drop the 3–8 phase cap.** Replace with per-phase shape
   rules (one outcome / one rollback / one session window).
2. **Document the heuristics catalog** at a *conceptual* level:
   what each category means, what kind of section each
   heuristic adds, how a plan author thinks about them. The
   canonical names + current thresholds live in `skillnet
   calibration heuristics list`; SKILL.md does NOT duplicate
   the threshold values.
3. **Document the meta-heuristics** (sampling rules) the same
   way: conceptual; reference `skillnet calibration meta-heuristics`
   for the live list.
4. **Specify the sidecar `.calibration.json` schema** —
   referencing skillnet's `src/calibration/sidecar.rs` as the
   byte-level source-of-truth, with a minimal example.
5. **Specify the tag conventions** (auto-tags applied by
   skillnet, user-tags rules).
6. **Specify the `surprises` text convention**
   (`dead-weight:` / `missed-signal:` prefixes), cross-
   referencing skillnet's `docs/src/calibration/surprises.md`.

Hooks into `skillnet calibration init|record|verify|walkthrough`
land in Phase 07, not here.

## Why this matters now

skillnet 0.4.0 (Phase 05) ships the canonical catalog + helper
commands. Without this rewrite, ai-skills' SKILL.md still
enforces a 3–8 cap and has no contract documentation; Phase 07's
hooks would land in an unprepared skill body. This phase locks
the contract before 07 adds the wiring.

Runs in parallel with skillnet phases 01–05 (Wave 0+). The
SKILL.md cross-references to skillnet content can be written
against the design, validated against the live skillnet
post-Phase 05.

## Out of scope

- Hook calls (`skillnet calibration init|record|verify`) — Phase 07.
- `calibrate` mode body — Phase 07.
- Calibration changelog footer scaffolding — Phase 07.
- Flavor wrapper updates — Phase 08.
- Any change to the existing per-phase file shape (Working
  tree / Goal / Why / Out of scope / Plan / Acceptance criteria
  / Files likely touched / Pitfalls / Reference). Contract
  preserved.
- Documenting `skillnet`'s broader CLI surface (mirror, sync,
  scope, catalog). Out of scope for `multi-phase-plan`.

## Plan

1. **Read the current `global/multi-phase-plan/SKILL.md`** end
   to end. Preserve:
   - The per-phase file shape spec.
   - The "Required top-level README.md" section.
   - The anti-patterns section.
   - The Workflow section's overall structure (only step 1's
     body changes).
   - The "Sequencing and parallelism guidance" section.

2. **Replace the 3–8 phase cap** in Workflow step 1:

   > **Take inventory.** List every concrete action the work
   > entails. Group related actions into candidate phases. Each
   > phase must satisfy the per-phase shape rules:
   >
   > - **One outcome.** The Goal section names a single
   >   user-observable outcome; you can write "this phase
   >   succeeds when …" in one sentence.
   > - **One rollback boundary.** The phase's changes can be
   >   reverted as a unit without leaving the repo in a
   >   half-state. If a phase crosses two natural revert
   >   boundaries, it's two phases.
   > - **One session window.** A fresh session can plausibly
   >   complete the phase in one sitting at the recommended
   >   tier. A phase that needs to be bumped from `medium` to
   >   `high` to fit is a routing signal, not a "make the phase
   >   bigger" signal.
   >
   > Phase count is whatever falls out. There is no upper cap.
   > Large efforts trigger additional README sections via the
   > heuristics catalog below.

3. **Add the heuristics catalog section** (new top-level after
   "Sequencing and parallelism guidance"). Keep it conceptual;
   do *not* duplicate threshold values.

   > ## Heuristics catalog
   >
   > The plan's README and individual phase files gain extra
   > sections when specific *triggers* fire. Triggers and their
   > current thresholds live canonically in skillnet
   > (`skillnet calibration heuristics list`). This section
   > documents what each category means and what kind of
   > section each trigger contributes.
   >
   > Run `skillnet calibration eval <plan-dir>` after writing
   > a plan to see which triggers fire and what they add.
   >
   > ### Coordination
   >
   > Triggers in this category surface coordination cost
   > between phases that share resources or cross repos.
   >
   > - `shared-file-contention` — multiple phases touch the
   >   same file. Adds a "Shared-file lockstep" section to the
   >   README and cross-links each affected phase's Plan.
   > - `external-repo-phases` — any phase has a non-primary
   >   `Working tree`. Adds an "External repo coordination"
   >   section.
   > - `convergence-point` — a phase has many direct
   >   predecessors. The convergent phase gets a "Merge-readiness
   >   checklist".
   > - `ownership-boundary-spread` — phases span multiple
   >   maintainer domains. Adds a "PR sequencing &
   >   cross-owner coordination" section.
   >
   > ### Risk
   >
   > - `risk-concentration` — many `max` phases. README gets a
   >   "Risk-tier callout".
   > - `risk-late-in-plan` — a `max` phase in the final waves.
   >   README gets a "Late-risk warning".
   > - `infrastructure-spof` — a phase touches CI / flake.nix /
   >   lockfiles and downstream phases depend on it. The phase
   >   is flagged "infra-SPOF"; downstream Pitfalls inherit a
   >   smoke-invalid note.
   > - `revendor-phase` — phase title or files indicate vendor
   >   bump. Routing tier suggestion bumps up; the phase gets a
   >   "Compat surface" section.
   >
   > ### Plan shape
   >
   > - `long-serial-chain` — deep dependency chain. README gets
   >   a "Serial-chain recovery" section.
   > - `mid-plan-rerouting` — many phases. README mandates an
   >   "after wave N, re-run routing" checkpoint.
   > - `trivial-phase-swamp` — many low-tier phases relative to
   >   high. README gains a "Cleanup batch" appendix.
   > - `no-integrated-verification` — no closing verification
   >   phase. Warn; prompt adding one.
   >
   > ### Quality lint (warn, don't add section)
   >
   > - `routing-tier-inversion` — leaf phase routes ≥ its
   >   orchestrator. Require an inline justification.
   > - `mechanical-streak` — many `low` in a row. Suggest
   >   bundling.
   > - `hidden-prerequisite` — phase assumes state nothing
   >   earlier produces. Block; require explicit dep edge.
   >
   > Current thresholds, including any per-tag-band overrides,
   > are available via `skillnet calibration heuristics list
   > --format json`. They evolve via the calibration loop — see
   > the calibration changelog at the bottom of this file.

4. **Add the meta-heuristics section** — "When a plan gets
   recorded". Conceptual; reference `skillnet calibration
   meta-heuristics --help` for the live set:

   > ## When a plan gets recorded
   >
   > A plan is written to the calibration dataset only when at
   > least one *meta-heuristic* fires. The goal is to minimize
   > selection bias: the dataset concentrates on plans where
   > learning is possible (boundary cases, novel shapes,
   > verifier surprises).
   >
   > Categories of meta-heuristic (see `skillnet calibration
   > meta-heuristics --help` for the live list):
   >
   > - **Threshold proximity.** A trigger's input value sits
   >   near its threshold — the boundary is where tuning
   >   matters most.
   > - **Trigger absence with risk shape.** No triggers fired,
   >   but the plan "looks risky" by other measures. Catches
   >   false negatives.
   > - **Novel shape signature.** The plan's overall shape
   >   hasn't appeared before — sparse-region sampling.
   > - **Routing tier outlier.** A phase routes unusually high
   >   or low for its complexity class.
   > - **Verify surprise** *(verify-time only).* The verifier
   >   reported a failure no trigger pre-empted.
   > - **Re-routing event** *(verify-time only).* A phase
   >   executed at a different tier than recommended.
   > - **High-stakes combo.** A `max` phase combined with
   >   external-repo work.
   > - **Uniform random.** A small per-plan probability
   >   (default 7%) regardless of other triggers — the
   >   anti-bias floor.
   >
   > Each meta-heuristic that fires is recorded in the
   > sidecar's `meta_heuristics_fired` array so calibration
   > can later check whether each meta-heuristic itself produces
   > signal.

5. **Add the sidecar schema spec** — "Sidecar
   `.calibration.json`":

   > ## Sidecar `.calibration.json`
   >
   > Every recorded plan carries a sidecar at
   > `<plan-dir>/.calibration.json`. skillnet's
   > `init`/`record`/`verify` commands read and write it; the
   > skill body never composes the JSON by hand.
   >
   > Source-of-truth: `skillnet/src/calibration/sidecar.rs`
   > (`schema_version = 1`).
   >
   > Top-level shape:
   >
   > ```json
   > {
   >   "schema_version": 1,
   >   "plan": { "id": "<uuid>", "name": "<slug>", "flavor": "codex|claude|mixed",
   >             "worktype": "refactor|migration|cleanup|feature|infra|docs|other",
   >             "created_at": <unix-ts>, "phase_count": N, "wave_count": N,
   >             "max_chain_depth": N, "repo_spread": N,
   >             "routing_dist": { "low": N, "medium": N, "high": N, "max": N },
   >             "shape_hash": "<blake3-hex>" },
   >   "triggers": [ { "name": "...", "input_value": F, "threshold": F,
   >                   "fired": bool, "section_added": "..." | null } ],
   >   "phases": [ { "ordinal": N, "slug": "...", "routing_tier": "...",
   >                 "files": [ "..." ] } ],
   >   "meta_heuristics_fired": [ "..." ],
   >   "tags": { "key": "value" },
   >   "verify": null | { "verified_at": <unix-ts>, "elapsed_seconds": N|null,
   >                      "outcome": "shipped|partial|abandoned",
   >                      "phase_outcomes": { "<ordinal>": "pass|fail|skipped|abandoned" },
   >                      "emergency_changes": <json>|null,
   >                      "surprises": "..." | null }
   > }
   > ```
   >
   > Run `skillnet calibration init <plan-dir>` to bootstrap;
   > `skillnet calibration show <plan-id>` to inspect a
   > recorded one.

6. **Add the tag conventions section**:

   > ## Tag conventions
   >
   > skillnet applies **auto-tags** at `record` time from the
   > sidecar's plan metadata:
   >
   > - `flavor:<codex|claude|mixed>`
   > - `worktype:<refactor|migration|cleanup|feature|infra|docs|other>` (if set)
   > - `scope:<single-crate|single-repo|multi-repo|cross-org>` (from `repo_spread`)
   > - `risk:<low|mixed|high>` (from `routing_dist`)
   > - `signal:<meta-heuristic-name>` (one per firing meta-heuristic)
   > - `outcome:<shipped|partial|abandoned>` (updated by `verify`)
   >
   > **User tags** are free-form; key must match
   > `^[a-z][a-z0-9_-]*$`. Add via
   > `skillnet calibration tag <plan-id> <key>=<value>`.
   >
   > **Per-band analysis**: `skillnet calibration analyze
   > --filter-tag <key>=<value>` slices the dataset; the
   > calibrate mode uses this to surface flavor- or
   > worktype-specific skew.

7. **Add the `surprises` text convention section**:

   > ## Verifier `surprises` field
   >
   > The verifier's free-text `surprises` field accepts
   > structured prefixes that feed calibration; lines without
   > a recognized prefix are preserved verbatim but ignored by
   > the analyzer.
   >
   > Recognized prefixes:
   >
   > - `dead-weight: <trigger-name>: <note>` — the section
   >   added by `<trigger-name>` was useless on this plan
   >   (false positive).
   > - `missed-signal: <trigger-name>: <note>` — `<trigger-name>`
   >   would have added a useful section if its threshold were
   >   lower (false negative).
   >
   > Full convention: `skillnet docs` → "Verifier surprises
   > convention".

8. **Update the anti-patterns section**:
   - **Treating heuristic thresholds as immutable.** Use
     `dead-weight:` / `missed-signal:` prefixes when verifier
     surprises occur — the calibration loop is the way they
     get tuned.
   - **Skipping the verifier `surprises` field.** Without
     annotations the loop runs on shape data alone and
     converges slower.
   - **Re-implementing what skillnet provides.** The skill body
     no longer evaluates heuristics in prose; call
     `skillnet calibration eval` (or rely on `init` which
     calls eval internally).

9. **Cross-reference verification** — every reference to
   skillnet in this rewrite must resolve to a real command,
   page, or file:
   ```sh
   skillnet calibration heuristics list
   skillnet calibration meta-heuristics --help
   skillnet calibration eval --help
   skillnet calibration init --help
   skillnet calibration tag --help
   # Verify docs pages exist:
   ls ~/canix/Projects/skillnet/docs/src/calibration/
   ```

10. **Skim-read** post-edit for tone and consistency with the
    rest of `global/`. Confirm the file no longer contains
    `3–8` or `3-8`.

## Acceptance criteria

- [ ] `global/multi-phase-plan/SKILL.md` no longer mentions the
      3–8 phase cap.
- [ ] Per-phase shape rules appear in Workflow step 1.
- [ ] The heuristics catalog section enumerates 13 triggers in
      four categories with their conceptual purpose; no
      threshold values are duplicated in the prose.
- [ ] The meta-heuristics section enumerates 8 sampling rules
      conceptually; the random-rate value is named (`default
      7%`) but tied to "see `skillnet` for live value".
- [ ] The sidecar schema spec documents the JSON shape and
      cross-references `skillnet/src/calibration/sidecar.rs`.
- [ ] The tag conventions section enumerates auto-tags and
      user-tag rules.
- [ ] The `surprises` convention section documents both
      prefixes.
- [ ] Three new anti-patterns are present.
- [ ] Every `skillnet calibration …` command referenced exists
      (verify with `--help`).
- [ ] The per-phase file shape spec is unchanged.
- [ ] `grep -n "3–8\|3-8" global/multi-phase-plan/SKILL.md`
      returns no matches.

## Files likely touched

- `global/multi-phase-plan/SKILL.md` (substantive rewrite; the
  per-phase file shape, README requirements, and anti-patterns
  list are preserved with additions).

## Pitfalls

- **Duplicating threshold values.** The whole point of pushing
  the catalog into skillnet is that thresholds tune themselves.
  If SKILL.md says "long-serial-chain fires at depth 4", that
  number rots the first time a calibrate-mode run accepts a
  change. Reference `skillnet calibration heuristics list`
  instead; don't hardcode.
- **Drift between SKILL.md descriptions and skillnet's
  catalog.** When phase 01 lands new heuristic names, update
  this SKILL.md to match. Until then, you're writing against
  the design; verify post-Phase 01 the names you used here are
  the ones skillnet actually exposes.
- **Sidecar field-name drift.** The example JSON must match
  `sidecar.rs` field-for-field. Open the file side-by-side
  while writing.
- **Confusion between sidecar `schema_version` and analyze
  output `schema_version`.** Same name, different scopes.
  Mention both contexts explicitly so readers don't conflate.
- **Sister skill bleed.** `multi-phase-dispatch` defines the
  sub-layer machinery. Don't accidentally rewrite anything
  there; only `multi-phase-plan` changes.
- **Anti-pattern bloat.** The anti-patterns list is doing real
  work; don't pad it with low-value entries.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- skillnet catalog: `01-skillnet-heuristics-catalog.md`.
- skillnet helpers: `02-skillnet-helper-commands.md`.
- skillnet schema/surprises doc:
  `03-skillnet-analyze-schema-surprises-doc.md`.
- Phase that wires hooks + calibrate mode:
  `07-ai-skills-hooks-calibrate-mode.md`.
- Existing SKILL.md being rewritten:
  `global/multi-phase-plan/SKILL.md`.
- Sister skill (untouched): `global/multi-phase-dispatch/`.
