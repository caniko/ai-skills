# Phase 01 — skillnet heuristics catalog as a first-class concept

> **Recommended Codex model: GPT 5.5 high**
>
> Foundation phase: defines the heuristic catalog model (trigger
> definitions, default thresholds, runtime-mutable storage), the
> Postgres schema for runtime overrides, and the catalog API that
> every other helper command consumes. Design content sits in the
> shape of the trigger trait (sync vs async evaluation, what inputs
> they receive, where the threshold mutation lives) and in the
> Postgres migration's upgrade path on a live db. `medium` would
> ship a string-keyed map that erodes type safety; `low` would
> hand-roll evaluation per trigger; both burn future time. No `max`
> is needed — the surface is well-bounded and the existing skillnet
> calibration module gives the contract by example.

## Working tree

`~/canix/Projects/skillnet`.

## Goal

A new `src/calibration/catalog/` module that:

- Defines every trigger from the design (13 user-facing
  heuristics + 8 meta-heuristics) as a Rust value with a name,
  category, default threshold, and an `evaluate(plan: &PlanInputs)
  -> TriggerOutcome` function.
- Exposes a `Catalog` singleton readable by name, by category, and
  iterable.
- Reads runtime threshold overrides from a new
  `heuristic_thresholds` Postgres table (seeded on migrate from
  the code defaults; mutable via `analyze`/`propose`/`decide`).
- Provides `PlanInputs` — the shape that helper commands assemble
  from a plan directory's README + phase files (path, phase
  count, files-per-phase, routing tiers, repo spread, wave
  structure, etc.).
- Provides `TriggerOutcome { input_value: f64, threshold: f64,
  fired: bool, section_added: Option<String> }` — exactly what the
  sidecar's `TriggerRecord` needs (so emission is trivial).

No CLI surface lands in this phase. Phase 02 wires the helpers;
this phase only delivers the catalog API + storage.

## Why this matters now

Every other phase in this suite consumes the catalog. Phase 02's
`eval` walks it; `meta-heuristics` filters it; `heuristics list`
prints it; phase 04's `walkthrough` displays it; phase 06's
SKILL.md cross-references it; phases 07 and 08 invoke commands
that read from it. Getting the shape wrong here cascades into
every later phase.

Until 01 lands, evaluation logic would have to live in agent
prose (the current state of the prior `calibration-loop` plan).
Pushing it into typed Rust code makes the contract verifiable,
makes thresholds tunable without crate releases, and is the
prerequisite for SKILL.md to be a *thin* reference to the
canonical catalog rather than a re-implementation.

## Out of scope

- Any CLI command (lives in 02).
- The `walkthrough` orchestrator (04).
- JSON schema documentation for `analyze` (03 — depends on this
  phase's `TriggerOutcome` shape).
- Any change to existing `record`/`verify`/`analyze` behavior
  beyond reading overridden thresholds from the new table.
- Web UI / GUI for catalog browsing.
- Per-user catalog customization beyond threshold overrides
  (e.g., disabling a trigger entirely, custom triggers). Defer
  to a follow-up.

## Plan

1. **Add catalog module skeleton** at
   `src/calibration/catalog/mod.rs`:
   ```rust
   pub mod inputs;
   pub mod outcome;
   pub mod heuristics;
   pub mod meta;
   pub mod thresholds;

   pub use inputs::PlanInputs;
   pub use outcome::TriggerOutcome;
   pub use heuristics::{Heuristic, HeuristicCategory, HEURISTICS};
   pub use meta::{MetaHeuristic, META_HEURISTICS};
   pub use thresholds::ThresholdStore;
   ```

2. **Define `PlanInputs`** at
   `src/calibration/catalog/inputs.rs`:
   ```rust
   pub struct PlanInputs {
       pub name: String,
       pub flavor: String,
       pub worktype: Option<String>,
       pub phase_count: u32,
       pub wave_count: u32,
       pub max_chain_depth: u32,
       pub repo_spread: u32,
       pub routing_dist: BTreeMap<String, u32>,
       pub phases: Vec<PhaseInputs>,
       pub waves: Vec<Vec<u32>>,            // wave[i] = ordinals of phases in wave i
   }

   pub struct PhaseInputs {
       pub ordinal: u32,
       pub slug: String,
       pub routing_tier: String,
       pub files: Vec<String>,
       pub working_tree: Option<String>,    // None if same as primary
       pub depends_on: Vec<u32>,
   }
   ```
   This is the canonical reading of a plan directory; the `init`
   helper in Phase 02 populates it from README + phase files.

3. **Define `TriggerOutcome`** at
   `src/calibration/catalog/outcome.rs`:
   ```rust
   pub struct TriggerOutcome {
       pub input_value: f64,
       pub threshold: f64,
       pub fired: bool,
       pub section_added: Option<String>,
   }
   ```
   Matches `sidecar::TriggerRecord` field-for-field; conversion
   is a `From` impl.

4. **Define the `Heuristic` trait + catalog** at
   `src/calibration/catalog/heuristics.rs`:
   ```rust
   pub enum HeuristicCategory { Coordination, Risk, PlanShape, QualityLint }

   pub trait Heuristic: Send + Sync {
       fn name(&self) -> &'static str;
       fn category(&self) -> HeuristicCategory;
       fn default_threshold(&self) -> f64;
       fn description(&self) -> &'static str;          // short, one-line
       fn section_added(&self, fired: bool) -> Option<&'static str>;
       fn evaluate(&self, plan: &PlanInputs, threshold: f64) -> TriggerOutcome;
   }

   pub static HEURISTICS: &[&dyn Heuristic] = &[
       &SharedFileContention,
       &ExternalRepoPhases,
       &ConvergencePoint,
       &OwnershipBoundarySpread,
       &RiskConcentration,
       &RiskLateInPlan,
       &InfrastructureSpof,
       &RevendorPhase,
       &LongSerialChain,
       &MidPlanRerouting,
       &TrivialPhaseSwamp,
       &NoIntegratedVerification,
       &RoutingTierInversion,
       &MechanicalStreak,
       &HiddenPrerequisite,
   ];
   ```
   Implement each trigger as a unit struct with a manual
   `Heuristic` impl. Default thresholds match the values from the
   previously-designed catalog (e.g., `LongSerialChain` default
   4, `MidPlanRerouting` default 10, etc.). One file per trigger
   keeps diffs reviewable; use a sub-module per category if file
   count grows.

5. **Define meta-heuristics** at
   `src/calibration/catalog/meta.rs`:
   ```rust
   pub trait MetaHeuristic: Send + Sync {
       fn name(&self) -> &'static str;
       fn description(&self) -> &'static str;
       fn fires(&self, plan: &PlanInputs, triggers: &[TriggerOutcome]) -> bool;
   }

   pub static META_HEURISTICS: &[&dyn MetaHeuristic] = &[
       &ThresholdProximity,
       &TriggerAbsenceWithRiskShape,
       &NovelShapeSignature,
       &RoutingTierOutlier,
       &VerifySurprise,                  // requires verify section; evaluator handles
       &ReroutingEvent,                  // same
       &HighStakesCombo,
       &UniformRandom,                   // wraps rand crate; rate from constant 0.07
   ];
   ```
   `VerifySurprise` and `ReroutingEvent` need to inspect the
   `VerifyRecord` if present; pass it via an extended
   `MetaHeuristicInputs { plan: &PlanInputs, triggers: &[...],
   verify: Option<&VerifyRecord> }` if needed, to avoid widening
   `PlanInputs` for verify-time data.

6. **Threshold storage** at
   `src/calibration/catalog/thresholds.rs`:
   - Schema migration: `data/multi-phase-plan/schema-pg/00X-heuristic-thresholds.sql`:
     ```sql
     CREATE TABLE heuristic_thresholds (
         name      TEXT PRIMARY KEY,
         threshold DOUBLE PRECISION NOT NULL,
         updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
         updated_by TEXT                       -- proposal id or 'seed'
     );
     ```
     Pick the next free migration number; check `schema-pg/`
     after pulling.
   - `ThresholdStore` API:
     ```rust
     pub struct ThresholdStore { /* internal cache + db handle */ }
     impl ThresholdStore {
         pub fn load(db: &Db) -> Result<Self>;
         pub fn get(&self, name: &str) -> f64;     // db override or default
         pub fn set(&mut self, name: &str, value: f64, source: &str) -> Result<()>;
         pub fn iter(&self) -> impl Iterator<Item = (&str, f64, ThresholdSource)>;
     }
     pub enum ThresholdSource { Default, Override { updated_at, updated_by } }
     ```
   - On migrate: seed any heuristic not yet in the table with its
     default + `updated_by = 'seed'`. Re-running migrate is
     idempotent (does not overwrite overrides).

7. **Wire `decide accept` to update thresholds.** In
   `src/calibration/decide.rs`, when a proposal is accepted, also
   write to `heuristic_thresholds` with `updated_by =
   format!("proposal:{id}")`. Re-running an already-accepted
   proposal is a no-op (idempotent).

8. **Wire `analyze` to read overridden thresholds**. The
   per-trigger threshold field in `analyze`'s output should
   reflect what's currently in `heuristic_thresholds`, not the
   compiled default. Update `src/calibration/analyze.rs` to call
   `ThresholdStore::load(db)?` and read `get(trigger_name)` for
   each row.

9. **Unit tests** at `tests/catalog.rs`:
   - Each heuristic: synthetic `PlanInputs` that crosses
     threshold → `fired = true`; under threshold → `false`.
   - Each meta-heuristic: synthetic plan+triggers → expected
     fire/no-fire.
   - `ThresholdStore`: seeding doesn't overwrite overrides;
     `set` then `get` returns the new value across reload.
   - Default thresholds match the values asserted in
     `tests/catalog_defaults.rs` (a separate snapshot test so
     accidental edits to defaults need to update the snapshot
     deliberately).

10. **Run validation**:
    ```sh
    cargo fmt
    cargo clippy --all-targets -- -D warnings
    cargo test
    nix flake check
    ```

## Acceptance criteria

- [ ] `src/calibration/catalog/` module compiles and re-exports
      `PlanInputs`, `TriggerOutcome`, `Heuristic`, `HEURISTICS`,
      `MetaHeuristic`, `META_HEURISTICS`, `ThresholdStore`.
- [ ] All 13 user-facing heuristics from the suite README
      are implemented with their documented default thresholds.
- [ ] All 8 meta-heuristics are implemented with the documented
      sampling rules (uniform-random rate = 0.07).
- [ ] New migration
      `data/multi-phase-plan/schema-pg/00X-heuristic-thresholds.sql`
      creates the table; `skillnet calibration migrate` seeds
      defaults; re-running migrate doesn't overwrite overrides.
- [ ] `ThresholdStore::get` returns the override when present,
      default otherwise.
- [ ] `decide accept` updates `heuristic_thresholds` with
      `updated_by = "proposal:<id>"`.
- [ ] `analyze` reads thresholds from `ThresholdStore`, not from
      compiled defaults.
- [ ] `tests/catalog.rs` covers each heuristic (fire + no-fire),
      each meta-heuristic, threshold seeding, threshold override
      persistence.
- [ ] `tests/catalog_defaults.rs` snapshot test exists and
      documents the default thresholds at this phase's commit.
- [ ] `cargo clippy --all-targets -- -D warnings`, `cargo fmt
      --check`, `nix flake check` clean.

## Files likely touched

- `src/calibration/catalog/mod.rs` (new)
- `src/calibration/catalog/inputs.rs` (new)
- `src/calibration/catalog/outcome.rs` (new)
- `src/calibration/catalog/heuristics.rs` (new + per-trigger
  sub-files if needed)
- `src/calibration/catalog/meta.rs` (new)
- `src/calibration/catalog/thresholds.rs` (new)
- `src/calibration/mod.rs` (+ `pub mod catalog;` + re-exports)
- `src/calibration/decide.rs` (write to `heuristic_thresholds`
  on accept)
- `src/calibration/analyze.rs` (read from `ThresholdStore`)
- `data/multi-phase-plan/schema-pg/00X-heuristic-thresholds.sql`
  (new; pick next free number)
- `tests/catalog.rs` (new)
- `tests/catalog_defaults.rs` (new; snapshot)

## Pitfalls

- **Threshold-source confusion.** `analyze`'s output must show
  both the default and the active threshold so the user can
  reason about whether overrides have drifted. Add a
  `threshold_source: ThresholdSource` column to the analyze
  output schema (Phase 03 documents it).
- **Migration ordering.** This phase's migration must come *after*
  any existing migrations in `schema-pg/`. Read the directory
  before picking a number; don't claim `002` if it's already
  taken.
- **Meta-heuristic determinism in tests.** `UniformRandom` uses
  `rand`; tests must inject a seeded RNG (or feature-gate the
  call) to be reproducible. Pattern: pass an `Rng` trait through
  `MetaHeuristicInputs`.
- **`decide accept` re-entry.** If a proposal is already accepted
  and the user runs `decide accept` again, don't double-write to
  thresholds. Check the proposal's current `decision` before
  applying.
- **Default-threshold drift.** The snapshot test is the
  forcing function. Without it, an accidental edit to a
  trigger's default changes silent calibration behavior. Treat
  snapshot updates as deliberate decisions.
- **Sync vs async evaluation.** Heuristics are pure functions of
  `PlanInputs` — no IO, no DB, no network. Keep them sync. The
  threshold lookup happens once before the evaluation pass.
- **`PhaseInputs.depends_on` shape.** The depends-on graph is
  what powers chain-depth and convergence detection. Make sure
  Phase 02's `init` populates it correctly from the README's
  phase table (or from explicit "Depends on" annotations in
  phase files).
- **Catalog growth.** 15 trigger files is a lot. Consider a
  declarative macro: `heuristic! { name = "long-serial-chain",
  category = PlanShape, default = 4.0, … }`. Optional; only do
  it if the manual impls feel like boilerplate after writing the
  first 3.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Existing skillnet calibration module:
  `skillnet/src/calibration/`.
- Existing Postgres schema:
  `skillnet/data/multi-phase-plan/schema-pg/`.
- Next phase (helper commands): `02-skillnet-helper-commands.md`.
- Phase that documents the catalog for users: `06-ai-skills-skill-rewrite.md`.
