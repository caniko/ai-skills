# Phase 07 — ai-skills hooks + `calibrate` mode

> **Recommended Codex model: GPT 5.5 medium**
>
> Adds three sections to the now-rewritten
> `global/multi-phase-plan/SKILL.md`: end-of-plan hook
> (`skillnet calibration init` + `record`), end-of-verify hook
> (`skillnet calibration verify`), and the `calibrate` mode body
> that delegates to `skillnet calibration walkthrough`. Plus the
> calibration changelog footer. Much simpler than the prior
> draft because skillnet now owns evaluation, the orchestrator,
> and all parsing — the SKILL.md body becomes mostly "shell out
> to skillnet; surface its output."

## Working tree

`~/canix/Projects/ai-skills`.

## Goal

`global/multi-phase-plan/SKILL.md`, post-Phase-06, gains:

1. **End-of-plan hook step** that calls `skillnet calibration
   init <plan-dir>` then, if any meta-heuristic fires,
   `skillnet calibration record <plan-dir>`.
2. **End-of-verify hook step** that appends the verify section
   to `.calibration.json` and calls `skillnet calibration verify
   <plan-dir>`, with `surprises` annotation guidance.
3. **`calibrate` mode body** that delegates to `skillnet
   calibration walkthrough --skill-md <this-file-path>` and
   instructs the user to paste the printed changelog block into
   the footer.
4. **Calibration changelog footer** — empty placeholder ready
   for future entries.

## Why this matters now

This is the integration phase: the CLI is shipped (skillnet
0.4.0 per Phase 05), the skill body documents the contract
(Phase 06), the helpers exist. Without these three sections,
the calibration loop has no entry point — agents finish a plan
and the dataset stays empty.

This phase depends on Phases 02 (`init`), 03 (schema), 04
(`walkthrough`), and 06 (rewritten SKILL.md). Lands after all
four.

## Out of scope

- Flavor wrapper updates — Phase 08.
- ai-skills flake input — Phase 08.
- Retiring the old `calibration-loop` plan — Phase 08.
- Any change to skillnet — done in Phases 01–05.
- Any change to the heuristics catalog itself — Phase 01 is
  the source-of-truth.

## Plan

1. **Read the post-Phase-06 SKILL.md** end to end. Confirm the
   section headings the hooks cross-reference exist with the
   names this phase uses:
   - "Heuristics catalog"
   - "When a plan gets recorded"
   - "Sidecar `.calibration.json`"
   - "Tag conventions"
   - "Verifier `surprises` field"

2. **Add end-of-plan hook** as a new workflow step. Append after
   the existing final step ("Provide a routing summary"):

   > **Record for calibration.** After the plan files are
   > written:
   >
   > 1. Run `skillnet calibration init <plan-dir>`. This
   >    bootstraps `<plan-dir>/.calibration.json` by parsing the
   >    README and phase files, evaluating the heuristics
   >    catalog, and evaluating the meta-heuristics.
   > 2. If `init`'s output indicates at least one meta-heuristic
   >    fired (printed as `meta_heuristics_fired: […]`), run
   >    `skillnet calibration record <plan-dir>` to persist the
   >    plan to the calibration database.
   > 3. Surface the recording in the chat reply: "Recorded for
   >    calibration: <reason1, reason2>". If no meta-heuristic
   >    fired, do not surface anything — the plan deliverable
   >    is unchanged.
   >
   > If `skillnet` is missing (no HM module, no `cargo install`),
   > skip the recording silently and print a one-line install
   > hint at the end of the chat reply:
   > `(skillnet not installed — calibration recording skipped;
   > see ai-skills' HM module to enable.)`. Calibration
   > recording is a best-effort augment, not a blocker.

3. **Add end-of-verify hook** to the verify-mode workflow. After
   the existing final verify step:

   > **Record verify outcome.**
   >
   > 1. Read `<plan-dir>/.calibration.json` if it exists.
   > 2. Append a `verify` section to the sidecar with the
   >    outcome, per-phase pass/fail map, and `surprises` text.
   >    The `surprises` field should use the structured
   >    prefixes documented in "Verifier `surprises` field"
   >    when applicable:
   >    - For each section that turned out to be dead weight on
   >      this plan: `dead-weight: <trigger-name>: <one-line
   >      note>`.
   >    - For each failure mode no trigger pre-empted: write
   >      `missed-signal: <closest-trigger-name>: <one-line
   >      note>` *if* a known trigger would have caught it with
   >      a lower threshold; otherwise leave informational
   >      prose (and consider proposing a new heuristic in the
   >      next calibrate-mode session).
   > 3. Run `skillnet calibration verify <plan-dir>`.
   > 4. If the sidecar does not exist (plan wasn't recorded at
   >    plan time) but a verify-time meta-heuristic would fire
   >    (`skillnet calibration meta-heuristics <plan-dir>
   >    --sidecar /dev/null` returns any of `verify-surprise`,
   >    `rerouting-event`): run `skillnet calibration init
   >    <plan-dir> --force` first (which writes a sidecar
   >    derived from the current plan state), then proceed.
   >
   > CLI errors are reported and don't block the verify
   > deliverable.

4. **Add the `calibrate` mode** as a new top-level section,
   sister to "Mode: plan" and "Mode: verify":

   > ## Mode: `calibrate`
   >
   > Triggered when the user says "calibrate", "tune the
   > heuristics", "review calibration data", or invokes the
   > skill with `calibrate` as the first word.
   >
   > Calibrate mode does not write phase files. It walks the
   > user through the calibration dataset and produces a
   > changelog block to paste into this file's footer.
   >
   > ### Workflow
   >
   > 1. Shell out to:
   >    ```sh
   >    skillnet calibration walkthrough \
   >        --skill-md global/multi-phase-plan/SKILL.md \
   >        --interactive
   >    ```
   >    The orchestrator runs `analyze` → interactive prompts
   >    per candidate proposal → records `propose`/`decide` →
   >    emits an `export-changelog` block scoped to changes
   >    since the most recent entry in this file's footer.
   >
   > 2. The user interacts with `walkthrough` directly (it
   >    handles the prompts). The skill agent's job is to
   >    surface what the user pasted next:
   >
   > 3. After `walkthrough` finishes, copy the markdown block
   >    between `──── Changelog block ────` and the closing
   >    `══` markers into the "Calibration changelog" footer
   >    at the bottom of this file. For each accepted proposal,
   >    also update the corresponding heuristic's threshold in
   >    the catalog section above (Phase 06's catalog is
   >    descriptive — the live threshold is the one in
   >    skillnet; this footer is for human audit).
   >
   > 4. Calibrate mode does NOT auto-edit SKILL.md. The user
   >    pastes; the user is the editor; the user can reject a
   >    bad block before it ratchets.
   >
   > ### Non-interactive use
   >
   > Scripted callers can:
   > ```sh
   > skillnet calibration walkthrough \
   >     --non-interactive --decisions decisions.json \
   >     --skill-md global/multi-phase-plan/SKILL.md
   > ```
   > Decisions file format: see `skillnet calibration
   > walkthrough --help` and the schema at
   > <https://codeberg.org/caniko/skillnet/src/branch/main/docs/src/calibration/walkthrough.md>.
   >
   > ### Cadence
   >
   > User-initiated; not scheduled. The min-N guard in
   > `analyze` ensures running too early is a no-op. Suggested
   > rhythm: after every ~10 verified plans, or when a
   > recurring "dead-weight" annotation suggests a trigger is
   > over-firing.

5. **Add the calibration changelog footer**. Last section of
   the file:

   > ## Calibration changelog
   >
   > Threshold changes to the heuristics catalog above are
   > recorded here. Each entry is produced by `skillnet
   > calibration walkthrough` (or `export-changelog`) and
   > pasted by the user during a `calibrate` mode session. The
   > live thresholds are authoritative in skillnet
   > (`heuristic_thresholds` table); this footer is the
   > human-readable audit trail.
   >
   > <!-- Newest first. Format produced by `skillnet calibration
   > export-changelog`. -->

   Leave the body empty under the comment marker.

6. **Update the Modes header** at the top of SKILL.md. The
   "Modes" list (from prior phases) lists `plan` and `verify`.
   Add `calibrate` as the third entry with a one-line summary
   pointing at the new section.

7. **Update the anti-patterns** with two more:
   - **Hand-editing the calibration changelog.** It's the
     audit trail; pastes from `walkthrough` only.
   - **Editing thresholds in skillnet without going through
     `walkthrough`.** The accepted-proposal trail in
     `calibration_proposals` is provenance; bypassing it leaves
     no record of *why* a threshold moved.

8. **Sanity-check the hook commands.** Every `skillnet …`
   invocation in this phase's edits must work against the
   shipped 0.4.0:
   ```sh
   skillnet calibration init --help
   skillnet calibration record --help
   skillnet calibration verify --help
   skillnet calibration meta-heuristics --help
   skillnet calibration walkthrough --help
   skillnet calibration export-changelog --help
   ```
   Each must return without error and show the documented
   flags.

9. **Skim-read** post-edit for consistency with Phase 06's
   tone.

## Acceptance criteria

- [ ] `global/multi-phase-plan/SKILL.md` plan workflow ends
      with a "Record for calibration" step that calls
      `skillnet calibration init` then conditionally
      `skillnet calibration record`.
- [ ] The verify-mode workflow ends with a "Record verify
      outcome" step that writes the `verify` section, calls
      `skillnet calibration verify`, and handles the
      missing-sidecar case via `init --force`.
- [ ] A new `## Mode: calibrate` section exists, delegating to
      `skillnet calibration walkthrough --skill-md
      global/multi-phase-plan/SKILL.md --interactive`, with
      both interactive and non-interactive usage documented.
- [ ] The Modes header lists three modes (`plan`, `verify`,
      `calibrate`).
- [ ] A `## Calibration changelog` section exists at the
      bottom of the file with the placeholder comment and no
      entries.
- [ ] Two new anti-patterns are present.
- [ ] Every `skillnet calibration …` invocation in the edits
      matches a real subcommand in skillnet 0.4.0.
- [ ] The `--skill-md <path>` flag is used so `walkthrough`
      auto-detects `--since`.
- [ ] CLI errors are documented as non-blocking for the
      plan/verify deliverable.
- [ ] No regressions in the per-phase file shape spec or the
      heuristics catalog text from Phase 06.

## Files likely touched

- `global/multi-phase-plan/SKILL.md` (additions only; Phase 06's
  content preserved).

## Pitfalls

- **Conflict with Phase 06.** This phase edits the same file
  Phase 06 rewrote. Pull the post-06 file before starting;
  verify each cross-referenced section heading exists with the
  name expected.
- **`init --force` semantics for verify-time reconstruction.**
  `init --force` overwrites an existing sidecar but preserves
  `plan.id`, user tags, and the verify section if present. For
  verify-time reconstruction when there's no prior sidecar at
  all, `--force` is a no-op (nothing to preserve). Confirm
  Phase 02's `init` implementation handles "no prior sidecar +
  --force" as "just create one".
- **Don't auto-edit SKILL.md from calibrate mode.** The
  user-as-editor invariant keeps bad proposals from ratcheting
  bad thresholds. Document the choice in the mode body.
- **Cadence prescription.** The suggested "every ~10 verified
  plans" is guidance, not a rule. The min-N guard in `analyze`
  is the actual gate; if a user runs calibrate after one plan,
  the orchestrator says "no candidates above min-n" and exits.
- **Hook command exact spelling.** `init`, `record`, `verify`,
  `meta-heuristics`, `walkthrough`, `export-changelog`. Any
  typo breaks the hook silently. Grep the file after editing
  to confirm all commands match Phase 05's published surface.
- **`--skill-md` resolution.** The path passed to
  `walkthrough --skill-md` is relative to the user's CWD at
  invocation time, not to the skill. Document as an absolute
  path or repo-relative-with-cwd-noted; pick one and use it
  consistently.
- **Changelog format drift.** The format the user pastes is
  whatever `export-changelog` emits. If skillnet changes the
  format in a future minor bump, the SKILL.md changelog will
  contain mixed-format entries. Accept this; the entries are
  archival.
- **Surprises annotation placement.** Encourage but don't
  enforce. A verify session can produce useful insights even
  if the agent forgets the prefix syntax — the prose is
  preserved.

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Predecessor phases: `02`, `03`, `04`, `05`, `06`.
- Phase that propagates this to flavor wrappers + finalizes
  ai-skills consumption: `08-ai-skills-consumption.md`.
- skillnet walkthrough command:
  `04-skillnet-walkthrough-orchestrator.md`.
- Live skillnet command surface (post-Phase 05):
  `skillnet calibration --help`.
