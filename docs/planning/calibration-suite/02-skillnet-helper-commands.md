# Phase 02 — skillnet helper commands

> **Recommended Codex model: GPT 5.5 medium**
>
> Six new `skillnet calibration` subcommands that wrap the catalog
> from Phase 01: `init`, `eval`, `meta-heuristics`, `shape-hash`,
> `heuristics list`, `heuristics show`. The work is clap plumbing
> plus a `PlanInputs` parser that reads a plan directory's README
> and phase files. Moderate complexity: the README parser is the
> only place real ambiguity lives (extracting the dependency graph
> from a markdown table). `low` would hand-wave the parser and
> ship a brittle implementation; `high` is unnecessary once the
> catalog API is in place.

## Working tree

`~/canix/Projects/skillnet`.

## Goal

Six subcommands on `skillnet calibration`, each backed by a
single helper function that takes a `PlanInputs` (loaded by the
shared `init`-style parser) and returns structured JSON:

- `init <plan-dir>` — parse the plan directory and emit
  `.calibration.json` (or print to stdout with `--stdout`).
- `eval <plan-dir>` — evaluate every heuristic against the plan,
  emit the trigger rows as JSON.
- `meta-heuristics <plan-dir>` — emit which meta-heuristics fire,
  as JSON.
- `shape-hash <plan-dir>` — emit the canonical shape hash.
- `heuristics list [--format json|table] [--category C]` — dump
  the catalog with current thresholds and sources (default vs
  override).
- `heuristics show <name>` — detail one heuristic (name, category,
  description, default threshold, current threshold, source,
  section added on fire).

All commands accept the standard skillnet flags
(`--config`, `--database-url`, etc.) and respect the configured
Postgres backend.

## Why this matters now

The skill body (ai-skills, Phase 06 of this suite) currently has
to know how to write `.calibration.json` byte-for-byte; with
`init`, it just shells out and inspects the result. The `eval`
command lets `record` (and `walkthrough`) operate without
duplicating evaluation logic in agent prose. `heuristics list`
gives SKILL.md a canonical "current thresholds" reference instead
of duplicating values that go stale.

This phase is the pivot from "skill writes sidecar bytes" to
"skill points skillnet at a plan dir." Every later phase depends
on these helpers existing.

## Out of scope

- The `walkthrough` orchestrator (04).
- Any change to the catalog itself (01).
- Any change to existing `record`/`verify` behavior. `init`
  produces what `record` already consumes; no API breakage.
- Auto-detection of plan format other than the current convention
  (README.md with a phase table + per-phase
  `NN-<slug>.md` files). Defer non-standard layouts.

## Plan

1. **Rebase against Phase 01.** Read the post-01 catalog API
   (`PlanInputs`, `Heuristic`, `MetaHeuristic`,
   `ThresholdStore`).

2. **Build the plan-dir parser** at
   `src/calibration/plan_parser.rs`:
   ```rust
   pub fn parse(plan_dir: &Path) -> Result<PlanInputs> { ... }
   ```
   - Read `README.md`; extract the **phase table** (markdown
     table with columns Phase | File | Depends on | Touches | Can
     parallel with). Tolerate variations: column order, extra
     columns, missing optional columns.
   - For each row, read the linked phase file (`./NN-slug.md`).
     Extract:
     - Working tree (from `## Working tree` section).
     - Routing tier (from the `> **Recommended Codex model: GPT
       5.5 <tier>**` callout).
     - Files (from `## Files likely touched` — bullet list).
     - Dependencies (from the README table; verify against phase
       file if it cross-references prior phases).
   - Compute derived fields: `repo_spread` (distinct working
     trees), `max_chain_depth` (longest path through the DAG),
     `wave_count` (topological generations), `routing_dist`
     (count per tier).
   - Compute `shape_hash` deterministically (see step 4).
   - Return `PlanInputs`.
   - Use `pulldown-cmark` (or `comrak`) for markdown parsing if
     not already a dep; otherwise hand-roll a tiny table parser
     to avoid the dep.

3. **Implement `init`** at `src/calibration/init.rs`:
   - Parse plan dir → `PlanInputs`.
   - Load catalog + threshold store → evaluate every heuristic →
     collect `TriggerOutcome`s.
   - Evaluate every meta-heuristic → collect names of firing
     ones.
   - Apply auto-tags: `flavor`, `worktype`, `scope`, `risk`,
     `signal:<meta-heuristic>` per the spec already in
     `record.rs`.
   - Compose a `Sidecar` value; serialize to
     `<plan-dir>/.calibration.json` (or stdout with `--stdout`).
   - Refuse to overwrite an existing sidecar unless `--force` is
     passed; if `--force`, preserve the existing `plan.id` and
     any user-added tags + the existing `verify` section.

4. **Define `shape-hash`** at `src/calibration/shape_hash.rs`:
   - Hash inputs (deterministic, canonical):
     ```
     blake3(
       phase_count || wave_count || max_chain_depth || repo_spread
       || sorted(routing_dist as key=value pairs)
       || sorted(phase ordinals || slug || routing_tier)
       || sorted(file paths across all phases)
     )
     ```
     Stable across runs given the same `PlanInputs`.
   - Return as hex string.
   - Pull in `blake3` crate if not already present (small,
     fast).
   - `shape-hash` command parses plan dir, computes hash, prints
     hex.

5. **Implement `eval`** at `src/calibration/eval.rs`:
   - Parse plan dir → `PlanInputs`.
   - Load `ThresholdStore` → for each `Heuristic`, evaluate;
     return JSON array of `{ name, category, input_value,
     threshold, threshold_source, fired, section_added }`.
   - `--format table` for humans; `--format json` (default for
     programmatic use).

6. **Implement `meta-heuristics`** at
   `src/calibration/meta_cmd.rs`:
   - Parse plan dir → `PlanInputs`.
   - Optionally accept `--sidecar <path>` if the user has a
     pre-built sidecar (so meta-heuristics like `VerifySurprise`
     can read the verify section without re-parsing).
   - Run trigger evaluation, then meta-heuristic evaluation.
     Emit JSON: `{ fired: ["threshold-proximity", ...], not_fired:
     [...] }`.

7. **Implement `heuristics list|show`** at
   `src/calibration/heuristics_cmd.rs`:
   - `list`: iterate `HEURISTICS`, look up override per name,
     emit rows `{ name, category, default_threshold,
     current_threshold, threshold_source, description,
     section_added_template }`. Table or JSON.
   - `show <name>`: same fields, one row.
   - `list --category coordination` filters.

8. **CLI surface** in `src/cli/args.rs`. Add `// HELPER COMMANDS`
   placeholder for Phase 04, then:
   ```rust
   Init { plan_dir: Utf8PathBuf, #[arg(long)] stdout: bool, #[arg(long)] force: bool },
   Eval { plan_dir: Utf8PathBuf, #[arg(long, default_value = "json")] format: EvalFormat },
   MetaHeuristics { plan_dir: Utf8PathBuf, #[arg(long)] sidecar: Option<Utf8PathBuf> },
   ShapeHash { plan_dir: Utf8PathBuf },
   Heuristics { #[command(subcommand)] command: HeuristicsCommand },
   ```
   `HeuristicsCommand::{ List { format, category }, Show { name } }`.

9. **Dispatch** in `src/commands/calibration.rs`. Each command
   opens a `Db` for `Heuristics`/`Eval`/`MetaHeuristics` (need
   `ThresholdStore`). `Init` opens a db too (the heuristics need
   thresholds). `ShapeHash` does not — pure function of
   `PlanInputs`.

10. **Integration tests** at `tests/calibration_helpers.rs`:
    - Fixture: a synthetic plan dir with README + 3 phase files.
    - `init` produces a valid sidecar; `record` ingests it.
    - `init --force` preserves `plan.id` and existing tags.
    - `init` (no `--force`) refuses to overwrite.
    - `eval` JSON output matches the triggers that would land in
      `record`'s `triggers` table.
    - `meta-heuristics` JSON output names every meta-heuristic
      that should fire on the fixture.
    - `shape-hash` is stable across two runs on the same fixture
      and changes when phase files change.
    - `heuristics list` returns 13 user-facing heuristics and
      respects `--category`.
    - `heuristics show <known>` returns one row; `show <unknown>`
      exits non-zero with a clear error.
    - All commands honor `SKILLNET_DATABASE_URL` and read
      thresholds via `ThresholdStore`.

11. **Run validation**:
    ```sh
    cargo fmt
    cargo clippy --all-targets -- -D warnings
    cargo test
    nix flake check
    ```

## Acceptance criteria

- [ ] All six subcommands appear under `skillnet calibration --help`
      (and `heuristics --help`).
- [ ] `init <plan-dir>` produces a `.calibration.json` that
      `skillnet calibration record` ingests without error.
- [ ] `init --force` preserves `plan.id` and user tags.
- [ ] `eval` JSON matches what `record` writes to `triggers`.
- [ ] `meta-heuristics` JSON names the firing meta-heuristics.
- [ ] `shape-hash` is deterministic and content-sensitive.
- [ ] `heuristics list` enumerates 13 heuristics with
      default/current thresholds and source.
- [ ] `heuristics show <name>` returns one heuristic's full
      detail; unknown name errors clearly.
- [ ] All helpers respect the configured Postgres backend via
      `SKILLNET_DATABASE_URL`.
- [ ] `tests/calibration_helpers.rs` covers each command (fixture
      → assertion) including the round-trip
      `init` → `record` flow.
- [ ] `cargo clippy --all-targets -- -D warnings`, `cargo fmt
      --check`, `nix flake check` clean.

## Files likely touched

- `src/calibration/plan_parser.rs` (new)
- `src/calibration/init.rs` (new)
- `src/calibration/eval.rs` (new)
- `src/calibration/meta_cmd.rs` (new)
- `src/calibration/shape_hash.rs` (new)
- `src/calibration/heuristics_cmd.rs` (new)
- `src/calibration/mod.rs` (+ `pub mod …` re-exports)
- `src/cli/args.rs` (+ five new variants + `HeuristicsCommand`)
- `src/commands/calibration.rs` (+ five dispatch arms)
- `Cargo.toml` (+ `blake3`, maybe `pulldown-cmark` / `comrak`)
- `tests/calibration_helpers.rs` (new)

## Pitfalls

- **Markdown table parsing is fiddly.** Real README tables in this
  org use a fixed layout (Phase | File | Repo | Depends on |
  Touches | Can parallel with). Lean on that layout; don't try
  to be too clever. If a plan dir doesn't match, `init` should
  error clearly ("unrecognized README format — expected phase
  table with Phase/File/Depends on/Touches columns").
- **`init` overwriting state.** Without `--force`, never
  overwrite. With `--force`, *preserve* `plan.id` (look up the
  prior sidecar first) and user tags (read prior sidecar's
  `tags` and merge). The `verify` section is also preserved on
  `--force` — refusing to overwrite verify-time data
  accidentally.
- **`shape-hash` stability across plan-dir relocations.** The
  hash must not depend on absolute paths; normalize file paths
  to repo-relative before hashing. Test by parsing the same plan
  from two different absolute roots and asserting the same
  hash.
- **`eval` and `record` divergence.** `eval` and `init` both
  compute trigger outcomes; they must agree. Refactor so both
  call the same `evaluate_triggers(plan: &PlanInputs, store:
  &ThresholdStore) -> Vec<(String, TriggerOutcome)>` helper.
- **Shared file with Phase 04.** `src/cli/args.rs` and
  `src/commands/calibration.rs` are also touched by Phase 04
  (walkthrough). Leave a `// WALKTHROUGH command here`
  placeholder for 04.
- **`pulldown-cmark` vs hand-roll.** Adding a markdown parser
  pulls in a non-trivial dep. If the only parsing needed is the
  phase table and a handful of section headers, a hand-rolled
  parser (≤100 lines) is preferable. Decide on first contact;
  don't bikeshed.
- **`init` vs `record` auto-tag duplication.** `record.rs`
  already applies auto-tags; if `init` also applies them, the
  pipeline applies them twice (harmless because the PK is
  composite, but wasteful). Decide: `init` writes them once;
  `record` only re-applies if missing. Document the choice in
  both files.
- **Backend abstraction is the user's promise.** Both `db.rs`
  (sqlite) and `db_postgres.rs` exist; the helpers must not
  reach into either directly. Use the existing `Db` enum or
  trait that already abstracts them.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Catalog this phase consumes: `01-skillnet-heuristics-catalog.md`.
- Phase that depends on these helpers: `04-skillnet-walkthrough-orchestrator.md`,
  `07-ai-skills-hooks-calibrate-mode.md`.
- Sister doc-phase: `03-skillnet-analyze-schema-surprises-doc.md`.
- Existing sidecar: `skillnet/src/calibration/sidecar.rs`.
- Existing record: `skillnet/src/calibration/record.rs`.
