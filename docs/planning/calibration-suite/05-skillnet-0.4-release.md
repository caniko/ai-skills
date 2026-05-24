# Phase 05 — skillnet 0.4.0 release

> **Recommended Codex model: GPT 5.5 medium**
>
> Bump to 0.4.0, refresh CHANGELOG, run the chaperone, publish
> to crates.io, push the tag, update the docs/ mdBook with the
> new pages from Phase 03 and a brief migration note for HM
> module consumers. Mechanical via the existing
> `rust-crate-release-chaperone` skill family. Non-reversible
> publish at the end; `medium` is right because the release
> machinery already exists — the judgment is which gates to
> insist on (cargo-deny, audit, doc-test snapshot) before letting
> the chaperone push the tag.

## Working tree

`~/canix/Projects/skillnet`.

## Goal

`skillnet 0.4.0` published on crates.io, tagged on Codeberg,
docs/ rebuilt with the new calibration pages, HM module updated
if any new options surfaced from phases 01–04, and CHANGELOG
covering every user-visible change since 0.3.0.

## Why this matters now

Phases 01–04 land features in unreleased state. Phase 08
(ai-skills consumption) needs to lock its `inputs.skillnet` to
a published, immutable version. Releasing now also forces a
final pass through the quality gates before ai-skills wires up.

## Out of scope

- Any new features. This phase only releases what 01–04 shipped.
- Changes to the HM module beyond what the new commands require
  (likely none — the helpers don't add config surface).
- ai-skills-side changes. Phase 08 picks up the published
  version.

## Plan

1. **Verify upstream state.** Ensure 01, 02, 03, 04 are all
   merged to `main`. Run the full local quality gate:
   ```sh
   cargo fmt --check
   cargo clippy --all-targets -- -D warnings
   cargo test
   cargo doc --no-deps -- -D warnings
   nix flake check
   nix build .#docs
   ```
   Anything red, fix before proceeding.

2. **Audit the HM module** (`nix/hm-module.nix`) for any new
   options the new commands require:
   - Probably none. `init`/`eval`/`meta-heuristics`/`shape-hash`/
     `heuristics`/`walkthrough` all read from the existing
     `database` config. The `heuristic_thresholds` table is
     managed by `migrate`.
   - If any new env var was added in Phase 01–04, expose it via
     a new option here.

3. **Bump version** in `Cargo.toml`:
   ```toml
   [package]
   version = "0.4.0"
   ```
   Update `Cargo.lock`:
   ```sh
   cargo update -p skillnet
   ```

4. **Write CHANGELOG entry**:
   ```markdown
   ## 0.4.0 — YYYY-MM-DD

   Adds the first-class heuristics catalog, helper commands,
   walkthrough orchestrator, and SemVer-stable analyze JSON
   schema. ai-skills' `multi-phase-plan` skill consumes this
   release as the calibration backend.

   ### Added

   - Heuristics catalog as a first-class concept
     (`src/calibration/catalog/`). 13 user-facing heuristics, 8
     meta-heuristics. Default thresholds shipped in code;
     runtime overrides in the new `heuristic_thresholds`
     Postgres table.
   - `skillnet calibration init <plan-dir>` — bootstrap
     `.calibration.json` from a plan directory.
   - `skillnet calibration eval <plan-dir>` — evaluate heuristics
     and emit trigger rows.
   - `skillnet calibration meta-heuristics <plan-dir>` — emit
     firing meta-heuristics.
   - `skillnet calibration shape-hash <plan-dir>` — deterministic
     plan shape hash.
   - `skillnet calibration heuristics list|show` — inspect the
     catalog.
   - `skillnet calibration walkthrough` — orchestrated
     calibrate flow (`analyze → propose → decide →
     export-changelog`); `--non-interactive`,
     `--decisions <file>`, `--dry-run`, `--skill-md <path>`.
   - mdBook pages: calibration JSON schema, verifier surprises
     convention.

   ### Changed

   - `analyze --format json` schema is now SemVer-stable.
     Top-level gains `schema_version: 1`. Per-trigger rows gain
     `threshold_source` (default vs override with provenance).
   - `decide accept` now writes to `heuristic_thresholds`,
     closing the calibration loop.

   ### Schema migrations

   - `data/multi-phase-plan/schema-pg/00X-heuristic-thresholds.sql`.
     Seeded with code defaults; idempotent on re-migrate.
   ```

5. **Refresh docs/**:
   - The new pages from Phase 03 are already wired into
     `docs/src/SUMMARY.md`. Verify.
   - Add a top-level changelog entry to docs if there's a docs
     changelog. Otherwise, the rustdoc landing page should link
     to the new calibration pages.
   - Build: `nix build .#docs` (or `mdbook build docs/`).
     Inspect output.

6. **Run the release chaperone** (`rust-crate-release-chaperone`
   skill). It walks every gate and only allows tagging once
   green:
   - `cargo fmt --check`
   - `cargo clippy --all-targets -- -D warnings`
   - `cargo test`
   - `cargo doc --no-deps -- -D warnings`
   - `cargo package` (and verify the tarball includes the new
     migration SQL and the new schema doc — update `Cargo.toml`'s
     `include` list if needed)
   - `cargo audit`
   - `cargo deny check`
   - `nix flake check`
   - `nix build .#docs`

7. **Tag and push**:
   ```sh
   git tag v0.4.0 -m "skillnet 0.4.0 — heuristics catalog, helpers, walkthrough"
   git push origin main
   git push origin v0.4.0
   ```
   The Codeberg release workflow (`.forgejo/workflows/release.yml`)
   triggers on `v*` and runs `cargo publish`.

8. **Verify the publish**:
   - Watch CI: `berg pr|run status` (or web UI).
   - After publish: `cargo install skillnet@0.4.0` on a clean
     machine succeeds.
   - `crates.io/crates/skillnet/0.4.0` resolves.
   - `docs.rs/skillnet/0.4.0` renders (may take a few minutes).

9. **Validate end-to-end** in a fresh `home-manager switch` on
   the user's machine:
   ```sh
   # Update flake inputs in the user's HM config:
   nix flake update skillnet
   home-manager switch
   skillnet --version          # 0.4.0
   skillnet calibration migrate
   skillnet calibration heuristics list
   skillnet calibration walkthrough --dry-run
   ```

## Acceptance criteria

- [ ] `Cargo.toml` version is `0.4.0`.
- [ ] `CHANGELOG.md` has a `0.4.0` entry covering Added,
      Changed, Schema migrations.
- [ ] All quality gates pass locally and in Codeberg CI:
      fmt/clippy/test/doc/package/audit/deny/nix-check/docs.
- [ ] `v0.4.0` tag exists on Codeberg; release workflow
      published the crate.
- [ ] `crates.io/crates/skillnet/0.4.0` is live.
- [ ] `docs.rs/skillnet/0.4.0` renders with the new calibration
      pages (or the mdBook is published wherever it's hosted).
- [ ] `cargo install skillnet@0.4.0` works on a clean machine.
- [ ] `home-manager switch` against the published version
      installs 0.4.0; `skillnet calibration heuristics list`
      and `walkthrough --dry-run` succeed.

## Files likely touched

- `Cargo.toml` (version + maybe `include` for new SQL/docs)
- `Cargo.lock` (auto-updated)
- `CHANGELOG.md` (+ 0.4.0 entry)
- `nix/hm-module.nix` (only if new env vars were added in 01–04)
- `docs/src/SUMMARY.md` (verified, possibly tweaked)

## Pitfalls

- **`include` list omits new SQL or doc files.** Run `cargo
  package` and inspect the tarball before tagging. The new
  `00X-heuristic-thresholds.sql` and the new
  `docs/src/calibration/*.md` pages must be present.
- **Tag before merge.** Don't tag a branch; tag `main` after
  the merge. Tagging the wrong commit publishes the wrong code.
- **Forgot to update CHANGELOG.** The release workflow doesn't
  check this; you can publish without it. Add a CI gate later if
  this bites; for now, just don't forget.
- **`cargo audit` advisories on transitives.** Triage carefully;
  document any allow-listed advisory in `deny.toml` with a
  rationale.
- **`docs.rs` builds in a sandbox** — if any new code uses a
  feature gated behind `[package.metadata.docs.rs]`, the rustdoc
  on docs.rs will fail. Test locally with `RUSTDOCFLAGS="--cfg
  docsrs" cargo doc --no-deps`.
- **The chaperone is not negotiable.** Resist the urge to
  bypass a failing gate "just this once" — the crates.io publish
  is permanent.
- **HM module changes are breaking if option names shift.** If
  Phase 01–04 added an env var like `SKILLNET_THRESHOLDS_SEED`,
  the HM module needs an option that exports it; document the
  option in the module's rustdoc.
- **Don't bump to 1.0.0.** Even with a SemVer-stable analyze
  schema, the rest of the CLI surface is still pre-1.0. Stay at
  `0.x` until the whole crate stabilizes; revisit after the
  calibration loop has produced real data.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Predecessor phases: `01`, `02`, `03`, `04`.
- Phase that consumes the published version:
  `08-ai-skills-consumption.md`.
- Release skills:
  - `rust-crate-release-chaperone`
  - `rust-crate-release-prep`
  - `rust-crate-publish-workflow`
  - `rust-crate-quality-gates`
  - `rust-crate-forgejo-release-ci`
  - `berg-codeberg-ci`
- Existing release workflow: `.forgejo/workflows/release.yml`.
- crates.io: <https://crates.io/crates/skillnet>.
