# Phase 03 — analyze JSON schema + surprises parser doc

> **Recommended Codex model: GPT 5.5 medium**
>
> Documentation phase with two small code touches: lock the
> `analyze --format json` schema as SemVer-stable, document the
> `surprises` `dead-weight:` / `missed-signal:` parser (already
> implemented), and add a doc test that snapshots the JSON output
> shape. The parser is already at `analyze.rs:511`; this phase
> doesn't re-implement, it formalizes. Moderate complexity because
> getting the JSON schema *right* on first lock matters (changes
> are breaking thereafter).

## Working tree

`~/canix/Projects/skillnet`.

## Goal

- `docs/src/calibration/json-schema.md` (new mdBook page) fully
  documents the `analyze --format json` schema with field-by-field
  types, optionality, and stability commitment.
- `docs/src/calibration/surprises.md` (new mdBook page) documents
  the `surprises` text convention with examples, the
  prefix-parser semantics, and the calibration consequences of
  each kind of annotation.
- `src/calibration/analyze.rs` gains a top-level rustdoc block
  that mirrors the public schema in machine-readable form, plus
  a doc test that asserts a known input produces output matching
  a literal JSON fixture (so accidental schema changes break
  CI).
- The "threshold_source" field promised by Phase 01 is added to
  the analyze JSON output (override vs default).
- The schema page declares the SemVer commitment: from 0.4.0,
  field removals or type changes require a major bump; additive
  fields are minor.

## Why this matters now

The ai-skills `calibrate` mode (Phase 07) parses
`analyze --format json`. Today the schema is implicit in
`analyze.rs`'s output struct — anything could change without
warning. The `walkthrough` orchestrator (Phase 04) also consumes
the same schema. Locking it before 0.4.0 publishes (Phase 05)
prevents accidental breakage downstream.

The `surprises` parser already exists and works; documenting it
keeps the verifier's contract explicit (otherwise users write
free-text surprises that the parser silently ignores, and
calibration learns nothing).

## Out of scope

- Implementing the schema in code (it already exists in
  `analyze.rs`). This phase only documents and pins it.
- Adding new analyze features (skew check enhancements, new
  proposal heuristics, etc.). The schema covers what's there
  today.
- Re-implementing the `surprises` parser (already at
  `analyze.rs:511`). Just document its current behavior.
- mdBook publishing pipeline changes — the existing docs/ build
  picks up new pages automatically.

## Plan

1. **Read the current `analyze.rs`** to inventory the output
   shape:
   ```sh
   rg "Serialize" ~/canix/Projects/skillnet/src/calibration/analyze.rs
   ```
   Identify the top-level output struct(s); confirm field names,
   optionality, nesting.

2. **Add `threshold_source`** to the analyze output (consequence
   of Phase 01's `ThresholdStore`). Each per-trigger row gains:
   ```rust
   threshold_source: ThresholdSource,   // Default | Override { updated_at, updated_by }
   ```
   With `#[serde(tag = "type")]` so the JSON form is:
   ```json
   { "type": "default" }
   { "type": "override", "updated_at": "2026-…", "updated_by": "proposal:42" }
   ```

3. **Write the schema doc** at
   `docs/src/calibration/json-schema.md`. Sections:
   - **Top-level shape**: array of trigger rows + skew warnings
     + proposals.
   - **Per-trigger row**: `name`, `category`, `n_fires`,
     `n_misses`, `fire_rate`, `signal_rate`, `verdict`
     (`"propose-lower" | "propose-raise" | "hold" | "monitor"`),
     `threshold` (current), `threshold_source` (default vs
     override).
   - **Proposals array**: per proposal — `trigger`, `from`,
     `to`, `fire_rate_at_decision`, `signal_rate_at_decision`,
     `supporting_plan_ids`, `filter_tags`.
   - **Skew warnings array**: per warning — `trigger`, `axis`
     (`flavor` | `worktype`), `band`, `band_signal_rate`,
     `global_signal_rate`, `band_fires`.
   - **Top-level meta**: `analyzed_at`, `min_n`, `dataset_size`,
     `filter_tags_applied`.
   - **Stability**: schema_version field at the top (`1` at 0.4.0
     ship); SemVer rules (additive minor, breaking major).
   - **Example**: a full example JSON document.

4. **Write the surprises doc** at
   `docs/src/calibration/surprises.md`:
   - **Why the convention exists**: free-text surprises are
     informational only; structured prefixes feed calibration.
   - **Prefixes**:
     - `dead-weight: <trigger-name>: <note>` — the section
       added by `<trigger-name>` was useless on this plan;
       counts as a false positive.
     - `missed-signal: <trigger-name>: <note>` — `<trigger-name>`
       would have added a useful section if its threshold were
       lower; counts as a false negative.
   - **What the parser does**: parse line-by-line; lines
     starting with one of the two prefixes contribute to
     analyze; everything else is ignored for calibration but
     preserved verbatim in the database for human review.
   - **Multiple annotations per `surprises` field**: separate
     lines, one annotation per line; same trigger may be
     annotated multiple times if multiple aspects were
     dead-weight.
   - **Examples**: three short examples (one false positive, one
     false negative, one mixed with informational prose).
   - **Calibration consequences**: how each prefix moves the
     signal-rate computation (cross-reference the formula in the
     schema doc).

5. **Add a rustdoc schema block to `analyze.rs`** (top of file):
   ````rust
   //! Calibration analysis output schema (SemVer-stable since 0.4.0).
   //!
   //! Top-level: { schema_version, analyzed_at, min_n, dataset_size,
   //!              filter_tags_applied, triggers, proposals,
   //!              skew_warnings }
   //!
   //! Per-trigger: { name, category, n_fires, n_misses,
   //!                fire_rate, signal_rate, verdict, threshold,
   //!                threshold_source }
   //!
   //! See docs/src/calibration/json-schema.md for the canonical
   //! reference and the SemVer commitment.
   ````

6. **Add a doc test (or integration test) snapshot** at
   `tests/analyze_schema.rs`:
   - Seed a tiny synthetic dataset (3 plans, one trigger fired
     twice, one missed once).
   - Run `analyze --format json`.
   - Parse output back into `serde_json::Value`; assert specific
     fields and types using `insta` (already in use in the
     repo? check; otherwise pure assertion).
   - On schema change, the test breaks intentionally; updating
     the snapshot is the same gesture as documenting the bump
     in CHANGELOG.

7. **Wire new pages into `docs/src/SUMMARY.md`**:
   ```
   - [Calibration JSON schema](calibration/json-schema.md)
   - [Verifier surprises convention](calibration/surprises.md)
   ```
   Under a "Calibration" chapter if one exists; else create one.

8. **Run validation**:
   ```sh
   cargo fmt
   cargo clippy --all-targets -- -D warnings
   cargo test
   nix flake check
   # Build docs:
   nix build .#docs    # or mdbook build docs/
   ```

## Acceptance criteria

- [ ] `docs/src/calibration/json-schema.md` exists, documents
      every field of `analyze --format json` output, includes a
      worked example, and declares the SemVer commitment from
      `0.4.0`.
- [ ] `docs/src/calibration/surprises.md` exists, documents both
      prefixes with three examples, and explains the calibration
      consequences.
- [ ] `src/calibration/analyze.rs` has a top-level rustdoc block
      that lists the schema shape and cross-references the
      mdBook page.
- [ ] `analyze` output includes a `threshold_source` field per
      trigger row, JSON-tagged as `default` or `override`.
- [ ] `analyze` output includes a top-level `schema_version: 1`.
- [ ] `tests/analyze_schema.rs` runs `analyze` against a seeded
      dataset and asserts the output's structural shape (field
      presence + types).
- [ ] `docs/src/SUMMARY.md` links both new pages.
- [ ] `nix build .#docs` (or `mdbook build docs/`) succeeds with
      both pages rendered.
- [ ] `cargo clippy --all-targets -- -D warnings`, `cargo fmt
      --check`, `nix flake check` clean.

## Files likely touched

- `docs/src/calibration/json-schema.md` (new)
- `docs/src/calibration/surprises.md` (new)
- `docs/src/SUMMARY.md` (+ two entries)
- `src/calibration/analyze.rs` (+ rustdoc block, +
  `threshold_source`, + top-level `schema_version`)
- `tests/analyze_schema.rs` (new)

## Pitfalls

- **Documenting a schema you haven't pinned in code.** If
  `analyze.rs`'s output struct uses `#[serde(skip_serializing_if
  = "Option::is_none")]` on optional fields, the JSON shape
  changes based on input. Either document each field as
  conditionally present (with the condition), or remove the skip
  attributes for a stable shape.
- **`schema_version` confusion with sidecar schema_version.** The
  sidecar's `schema_version` is for `.calibration.json`; the
  analyze output's `schema_version` is for the analyze JSON. Use
  different names if collision feels likely (`analyze_schema_version`?).
  Decide once; document in both pages.
- **`threshold_source` enum tag style.** Pick one of
  `#[serde(tag = "type")]`, `#[serde(untagged)]`,
  `#[serde(rename_all = "kebab-case")]`. Tagged with kebab-case
  is the most consumer-friendly; lock it.
- **Doc tests vs integration tests for JSON shape.** Doc tests
  run in rustdoc; integration tests live in `tests/`. The
  snapshot is easier to maintain in `tests/` (no escaping
  hell). Pick that.
- **mdBook chapter structure.** Check
  `docs/src/SUMMARY.md` first — if there's no Calibration
  chapter, create one and place both pages under it. Don't drop
  pages at the top level.
- **Schema changes that look additive but aren't.** Adding a
  field that callers must populate is breaking. Make new fields
  optional (`Option<T>`) for the first release that introduces
  them.
- **Don't paint yourself into a corner with `verdict` enum.**
  The four documented values (`propose-lower`, `propose-raise`,
  `hold`, `monitor`) cover the design. Adding a fifth later
  (e.g., `propose-disable`) is additive *only* if consumers
  treat unknown verdicts as `monitor`. Document the unknown-value
  expectation explicitly.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Catalog from Phase 01: `01-skillnet-heuristics-catalog.md`.
- Existing parser location:
  `skillnet/src/calibration/analyze.rs:511` (`has_structured_surprise`).
- Phase that consumes this schema: `04-skillnet-walkthrough-orchestrator.md`,
  `07-ai-skills-hooks-calibrate-mode.md`.
- mdBook docs root: `skillnet/docs/`.
