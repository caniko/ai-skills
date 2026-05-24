# Phase 08 — ai-skills consumption + flavor propagation + retire old plan

> **Recommended Codex model: GPT 5.5 medium**
>
> Final phase: wire `inputs.skillnet` into ai-skills' flake,
> re-export the HM module, propagate the `calibrate` mode to the
> three flavor wrappers, retire the superseded
> `calibration-loop/` plan, and end-to-end-smoke the loop.
> Mechanical work with one design call (HM module re-export
> shape: pass-through vs explicit). `low` would forget the
> retirement of the old plan and leave docs in conflict; `high`
> is unnecessary.

## Working tree

`~/canix/Projects/ai-skills`.

## Goal

After this phase:

1. `ai-skills/flake.nix` has `inputs.skillnet` pinned to a
   specific revision of `ssh://git@codeberg.org/caniko/skillnet.git`.
2. ai-skills' flake re-exports `hmModules.default` such that a
   downstream user importing it gets `programs.skillnet.enable`
   wired transparently.
3. The three flavor wrappers
   (`global/multi-phase-plan-{codex,claude,mixed}/SKILL.md`)
   each list `plan` / `verify` / `calibrate` as their three
   modes and reference the base skill for content.
4. `docs/planning/calibration-loop/` is deleted (`git rm -r`),
   superseded by `calibration-suite/`. Use the
   `retire-docs-planning` skill.
5. Repo-root `README.md` has a short "Calibration" section
   pointing at skillnet and the calibrate mode.
6. End-to-end smoke run completed: this very plan's sidecar
   recorded into Postgres, visible via `skillnet calibration
   show`.

## Why this matters now

Phases 06 and 07 prepared the base skill; this phase makes the
loop actually operational by:
- Locking the skillnet version ai-skills consumes (otherwise
  later changes can break the contract silently).
- Giving the flavor wrappers the third-mode entry so users
  invoking `multi-phase-plan-codex` (etc.) discover calibrate
  mode.
- Removing the superseded plan so the docs/ tree doesn't have
  two competing plans for the same scope.

## Out of scope

- Any change to skillnet — done in Phases 01–05.
- Any change to the base skill body — done in Phases 06–07.
- Migrating any pre-existing calibration data — none exists.
- Removing other (non-skillnet) Rust tooling from ai-skills —
  the prior `calibration-loop` plan considered this; this phase
  only retires that plan, not the codebase decisions inside it.
  The git status snapshot already shows `D src/...` for the
  skillnet sources; this phase finalizes the related flake
  changes but does not re-do source deletion.

## Plan

1. **Pre-requisite check**:
   - `skillnet --version` reports `0.4.0`.
   - `nix run codeberg.org:caniko/skillnet --help` resolves
     (proves the public flake is reachable).
   - `global/multi-phase-plan/SKILL.md` has the post-Phase-07
     hooks + calibrate mode.
   - `docs/planning/calibration-suite/` is complete (this set).

   If any fails, pause and finish prereqs.

2. **Add the flake input** to `ai-skills/flake.nix`:
   ```nix
   inputs = {
     # … existing …
     skillnet = {
       url = "git+ssh://git@codeberg.org/caniko/skillnet.git?ref=v0.4.0";
       # If ai-skills pins nixpkgs:
       inputs.nixpkgs.follows = "nixpkgs";
     };
   };
   ```
   Document the SSH vs HTTPS alternative in a flake comment for
   CI scenarios.
   ```sh
   nix flake lock --update-input skillnet
   git add flake.nix flake.lock
   ```

3. **Re-export the HM module** (pass-through, Option A from the
   prior `calibration-loop` design):
   ```nix
   outputs = { self, nixpkgs, skillnet, ... }: {
     # … existing outputs …
     hmModules.default = { ... }: {
       imports = [
         skillnet.hmModules.default
         # … any ai-skills-own HM modules …
       ];
     };
   };
   ```
   Comment why: downstream importers of ai-skills' HM module
   get skillnet without an extra import.

4. **Propagate `calibrate` mode** to the three flavor wrappers.
   For each of
   `global/multi-phase-plan-codex/SKILL.md`,
   `global/multi-phase-plan-claude/SKILL.md`,
   `global/multi-phase-plan-mixed/SKILL.md`:
   - Locate the "## Modes" section. Add a third entry
     (matching the Phase 07 base entry):
     > - **calibrate** — when the user says "calibrate", "tune
     >   the heuristics", or "review calibration data", invoke
     >   the base skill's `calibrate` mode. See the base
     >   `global/multi-phase-plan/SKILL.md` "Mode: calibrate"
     >   for the workflow. The calibrate mode shells out to
     >   `skillnet calibration walkthrough`; users with the
     >   skillnet HM module enabled get this transparently
     >   (`programs.skillnet.enable = true` via ai-skills'
     >   re-exported HM module). The flavor-specific routing
     >   skill (`gpt-plan-routing` for codex,
     >   `claude-plan-routing` for claude, both for mixed) is
     >   *not* consulted for calibrate — calibrate analyzes
     >   past plans, it doesn't route new ones.
   - Locate the "## Plan workflow" section. Append a final
     step mirroring the base hook:
     > **Record for calibration.** Follow the base skill's
     > end-of-plan hook: run `skillnet calibration init
     > <plan-dir>`, and if any meta-heuristic fires, run
     > `skillnet calibration record <plan-dir>`. Surface in
     > the chat reply per the base workflow.
   - Don't duplicate the calibrate body, heuristics catalog,
     or sidecar schema.

5. **Update the repo-root `README.md`** with a Calibration
   section (extend rather than create a new file):
   ```markdown
   ## Calibration

   The `multi-phase-plan` skill records calibration data via
   **skillnet**, a separate published crate at
   <https://codeberg.org/caniko/skillnet> (also on
   crates.io). skillnet's HM module is re-exported from
   ai-skills' flake — adding
   `imports = [ inputs.ai-skills.hmModules.default ];`
   to your HM config and setting `programs.skillnet.enable
   = true` installs the binary and provisions the
   database directory.

   Calibration data lives in Postgres by default (configure
   `programs.skillnet.database.url` or `urlFile`); fallback
   SQLite path is `$XDG_DATA_HOME/skillnet/multi-phase-plan/
   calibration.sqlite`.

   The `calibrate` mode in `multi-phase-plan` walks the user
   through `skillnet calibration walkthrough`, prompting per
   candidate threshold change and emitting a markdown block
   to paste into the calibration changelog footer of
   `global/multi-phase-plan/SKILL.md`.

   See `docs/planning/calibration-suite/` for the plan that
   built this loop.
   ```

6. **Retire the old `calibration-loop/` plan.** Use the
   `retire-docs-planning` skill to:
   - Confirm there's nothing in `calibration-loop/` that
     hasn't been superseded.
   - `git rm -r docs/planning/calibration-loop/`.
   - Add a short note in the new `calibration-suite/README.md`
     to confirm retirement (already present in this suite's
     README).

7. **Seed the calibration changelog footer** in
   `global/multi-phase-plan/SKILL.md` with a genesis entry:
   ```markdown
   ### YYYY-MM-DD — Calibration loop activated

   - skillnet 0.4.0 consumed via HM module re-export.
   - Initial heuristic thresholds: see `skillnet calibration
     heuristics list --format json` for live values.
   - Database backend: Postgres
     (`postgres:///can?host=/run/postgresql` per this user's
     HM config; SQLite fallback documented).
   - No threshold changes in this entry — genesis row only.
   ```

8. **End-to-end smoke run**:
   ```sh
   # From ai-skills/:
   nix flake check
   home-manager switch                           # if HM config changed

   # Record this very plan into Postgres:
   skillnet calibration init docs/planning/calibration-suite
   # Inspect the resulting sidecar:
   cat docs/planning/calibration-suite/.calibration.json | jq .
   # If a meta-heuristic fired:
   skillnet calibration record docs/planning/calibration-suite
   # Confirm the row landed:
   skillnet calibration show <plan_id-from-sidecar>
   skillnet calibration query --tag flavor=codex --limit 5

   # Try a calibrate-mode dry run:
   skillnet calibration walkthrough --dry-run \
     --skill-md global/multi-phase-plan/SKILL.md
   ```
   Expect `walkthrough --dry-run` to say "no candidates above
   min-n" (the dataset has one row).

9. **Validate** `nix flake check` and commit.

## Acceptance criteria

- [ ] `ai-skills/flake.nix` has `inputs.skillnet` pointing at
      Codeberg, ref-pinned to `v0.4.0` (or current released
      tag).
- [ ] `ai-skills/flake.lock` has the locked skillnet revision.
- [ ] `ai-skills/flake.nix` re-exports `hmModules.default` that
      imports `skillnet.hmModules.default`.
- [ ] Each of `global/multi-phase-plan-{codex,claude,mixed}/SKILL.md`
      lists three modes including `calibrate`, with the
      flavor-specific note that calibrate doesn't consult
      routing skills.
- [ ] Each flavor wrapper documents the end-of-plan hook step.
- [ ] No flavor wrapper duplicates the calibrate body,
      heuristics catalog, or sidecar schema.
- [ ] Repo-root `README.md` has the Calibration section.
- [ ] `docs/planning/calibration-loop/` is git-rm'd.
- [ ] `global/multi-phase-plan/SKILL.md` calibration changelog
      footer has the genesis entry.
- [ ] Smoke run successful: `skillnet calibration init` on this
      plan dir creates a sidecar; if a meta-heuristic fires,
      `record` persists; `show` returns the row.
- [ ] `nix flake check` clean.

## Files likely touched

- `ai-skills/flake.nix` (+ `inputs.skillnet`, `hmModules.default`)
- `ai-skills/flake.lock` (auto-updated)
- `global/multi-phase-plan-codex/SKILL.md` (modes + workflow
  note)
- `global/multi-phase-plan-claude/SKILL.md` (same)
- `global/multi-phase-plan-mixed/SKILL.md` (same)
- `global/multi-phase-plan/SKILL.md` (only the genesis
  changelog entry; Phase 06+07 content preserved)
- `README.md` (+ Calibration section)
- `docs/planning/calibration-loop/` (deleted via `git rm -r`)
- `docs/planning/calibration-suite/.calibration.json` (created
  by smoke step 8; commit it for archival or `.gitignore` it —
  see Pitfalls)

## Pitfalls

- **Committing the smoke-run sidecar.** The `.calibration.json`
  produced by step 8 is real data. Either commit it (provides
  a real fixture for future tests) or `.gitignore` `*.calibration.json`
  in `docs/planning/`. Pick once and document. Default:
  `.gitignore` — calibration data lives in Postgres, the
  sidecar is a transient handoff.
- **`flake.nix` SSH input in CI.** CI may not have SSH access
  to Codeberg. Document `git+https://codeberg.org/caniko/skillnet.git`
  as an alternative in a flake comment; the user can choose
  per environment.
- **`inputs.nixpkgs.follows` conflicts.** If skillnet pins a
  specific nixpkgs and ai-skills pins a different one,
  `follows` collapses them. Without `follows`, two trees come
  in (bloated lockfile). Use `follows`.
- **Flavor-wrapper drift.** Three near-copy files. Edit all
  three identically (modulo routing-skill name). Grep after to
  confirm all three list `calibrate`.
- **HM module composition Option A's caveat.** Pass-through
  means downstream users who want ai-skills WITHOUT skillnet
  can't easily opt out. Document this as a known trade-off; if
  it becomes a problem, switch to a separate `hmModules.skillnet`
  re-export later.
- **`retire-docs-planning` may surface knowledge worth
  preserving.** Before `git rm`, run the skill — it audits the
  old plan and migrates contributor-worthy knowledge into
  contributor docs. Don't bypass that step.
- **Genesis changelog entry date.** Use the actual date of
  this phase's completion; don't backdate or leave a
  placeholder. The footer's chronology is part of the audit
  trail.
- **Smoke run requires Postgres reachable.** This user has
  Postgres at `postgres:///can?host=/run/postgresql`. If the
  socket isn't available, the smoke run fails at `record`;
  diagnose before declaring the phase done.
- **`init` may not trigger a meta-heuristic on this plan.**
  This is fine — `record` is conditional. If nothing fires,
  manually inspect the sidecar and confirm the meta-heuristic
  evaluator agreed there's no signal (then move on without
  recording).

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Phases this phase consummates: `01`–`07`.
- Retired plan: `docs/planning/calibration-loop/`.
- skillnet HM module: `nix/hm-module.nix` in the skillnet
  repo (Phase 08 of the retired plan documented it; live in
  skillnet 0.4.0).
- `retire-docs-planning` skill: see `global/retire-docs-planning/`.
- ai-skills repo: `~/canix/Projects/ai-skills`.
- skillnet repo: `ssh://git@codeberg.org/caniko/skillnet.git`,
  local at `~/canix/Projects/skillnet`.
