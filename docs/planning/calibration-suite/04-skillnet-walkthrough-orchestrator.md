# Phase 04 — `walkthrough` orchestrator

> **Recommended Codex model: GPT 5.5 medium**
>
> A single subcommand — `skillnet calibration walkthrough` —
> that runs the calibrate-mode workflow end-to-end:
> `analyze` → interactive `propose` → `decide` →
> `export-changelog`. Mechanically a small state machine over the
> existing commands, plus a `--non-interactive` mode for scripted
> use. The judgment calls are UX (what to prompt, what defaults
> to offer, when to bail) and how the output composes for the
> ai-skills `calibrate` mode body that wraps this. `low` would
> ship something brittle; `high` is unnecessary for a CLI that
> uses dialoguer-style prompts.

## Working tree

`~/canix/Projects/skillnet`.

## Goal

`skillnet calibration walkthrough` runs the full calibrate flow:

1. Print analysis summary (consumes `analyze --format json`).
2. For each candidate proposal, prompt: accept / skip / refine
   filter tags / quit.
3. On accept, call `propose` (writes a proposal row) then
   immediately `decide accept` with the user's rationale.
4. After all candidates handled, run `export-changelog --since
   <last-changelog-date>` (or full history if none recorded)
   and print the markdown block ready to paste into ai-skills
   SKILL.md.

Modes:
- Interactive (default): TTY prompts.
- `--non-interactive`: read decisions from a JSON file
  (`--decisions decisions.json`), no prompts. Used by automated
  test harnesses and by scripted ai-skills calibrate runs.
- `--dry-run`: walk the flow, print what would be done, but
  don't write proposals or decisions.

## Why this matters now

Without this command, the ai-skills `calibrate` mode (Phase 07)
has to orchestrate the multi-step flow in prose — agent calls
`analyze`, parses JSON, prompts user per proposal, calls
`propose`, then `decide`, then `export-changelog`, then formats
output. That's a fragile prose state machine. Moving it into
skillnet shrinks the SKILL.md mode body to roughly "run
`skillnet calibration walkthrough` and paste the printed
changelog block."

This phase also makes the calibration loop usable *outside*
ai-skills: a user with skillnet installed can run `walkthrough`
directly without invoking any skill.

## Out of scope

- Auto-applying SKILL.md edits. The output is markdown to paste;
  the user (or agent) writes the change.
- New analysis logic (lives in `analyze`, already shipped).
- TUI (cursor positioning, color, redrawing). Plain
  line-oriented prompts only.
- Persisting walkthrough sessions to resume later. If aborted,
  partially-recorded proposals stay in the db as `pending`;
  re-running picks them up.

## Plan

1. **Rebase against Phases 02 + 03.** Read the new `analyze`
   JSON schema (post-03) and the helper command surface
   (post-02).

2. **Add `dialoguer` dep** (or similar) for prompts:
   ```toml
   dialoguer = "0.11"
   ```
   Conservative: it's the standard Rust CLI-prompt crate, small,
   no surprises.

3. **Define the walkthrough state** at
   `src/calibration/walkthrough.rs`:
   ```rust
   pub struct Walkthrough {
       analysis: AnalyzeOutput,           // from analyze --format json
       db: Db,
       since: Option<DateTime<Utc>>,      // for export-changelog
       interactive: bool,
       dry_run: bool,
       decisions: Option<DecisionsFile>,  // when non-interactive
   }
   ```
   And the per-step methods:
   - `run() -> Result<()>` — top-level driver.
   - `present_summary()` — prints proposals + skew warnings.
   - `walk_proposals()` — iterates candidate proposals.
   - `prompt_decision(prop: &CandidateProposal) -> Decision` —
     interactive prompt with options accept / skip / refine /
     quit; non-interactive reads from `decisions`.
   - `apply_decision(prop, decision)` — writes
     `calibration_proposals` row, then writes `decide` row.
   - `emit_changelog()` — calls `export_changelog` with
     `--since`, prints output to stdout with a leading
     instruction line.

4. **Decisions file format** (for non-interactive mode):
   ```json
   [
     { "trigger": "long-serial-chain", "action": "accept",
       "rationale": "5/10 plans with depth 4 hit recovery cost" },
     { "trigger": "trivial-phase-swamp", "action": "skip",
       "rationale": "n=12 — wait for more data" },
     { "trigger": "infrastructure-spof", "action": "accept",
       "filter_tags": [{"key": "flavor", "value": "codex"}],
       "rationale": "codex-only skew justifies per-band threshold" }
   ]
   ```
   Triggers not listed default to `skip`.

5. **`since` resolution** for `export-changelog`:
   - Default: read ai-skills' SKILL.md if `--skill-md <path>` is
     passed, parse the most-recent changelog date from the
     footer, use that. (Phase 07 fills this in via the calibrate
     mode hook.)
   - Fallback: no `--since`, dump the full history.
   - `--since YYYY-MM-DD`: explicit override.

6. **Output format** (final emission):
   ```
   ════════ Calibration walkthrough ════════
   <analysis summary table>

   ──── Proposals ────
   1. trigger=long-serial-chain  4 → 5  fire 45.0%  signal -0.15
      [a]ccept / [s]kip / [r]efine / [q]uit > a
      Rationale: 5/10 plans at depth 4 hit recovery cost
   2. …

   ──── Changelog block (paste into ai-skills SKILL.md "Calibration changelog") ────

   ### 2026-MM-DD — long-serial-chain: 4 → 5
   …
   ════════════════════════════════════════
   ```

7. **CLI surface** in `src/cli/args.rs` under the `// WALKTHROUGH
   command here` placeholder Phase 02 left:
   ```rust
   Walkthrough {
       #[arg(long)]
       since: Option<String>,                  // YYYY-MM-DD
       #[arg(long)]
       skill_md: Option<Utf8PathBuf>,          // for since auto-detection
       #[arg(long, conflicts_with = "decisions")]
       interactive: bool,                      // explicit; default true if stdin is TTY
       #[arg(long, conflicts_with = "interactive")]
       non_interactive: bool,
       #[arg(long, requires = "non_interactive")]
       decisions: Option<Utf8PathBuf>,
       #[arg(long)]
       dry_run: bool,
       #[arg(long, value_parser = parse_kv)]
       filter_tag: Vec<(String, String)>,      // forwarded to analyze
       #[arg(long, default_value = "10")]
       min_n: u32,                             // forwarded to analyze
   },
   ```

8. **Dispatch** in `src/commands/calibration.rs` at the
   `// WALKTHROUGH command here` placeholder.

9. **Integration tests** at `tests/calibration_walkthrough.rs`:
   - Seed dataset with one candidate proposal trigger above
     min-N.
   - Run `walkthrough --non-interactive --decisions accept.json`
     where `accept.json` accepts the proposal; assert the
     `calibration_proposals` table has the row with
     `decision=accepted` and the `heuristic_thresholds` table is
     updated.
   - Run with `--decisions skip.json`; assert no proposal row is
     created.
   - Run `--dry-run`; assert no rows written, output mentions
     `[DRY RUN]`.
   - Run with `--since 2099-01-01`; assert export-changelog
     block is empty / nothing since.
   - Run without `--skill-md` and without `--since`; assert full
     history dumped.

10. **Run validation**:
    ```sh
    cargo fmt
    cargo clippy --all-targets -- -D warnings
    cargo test
    nix flake check
    ```

## Acceptance criteria

- [ ] `skillnet calibration walkthrough --help` shows the
      documented flags.
- [ ] Interactive mode reads from stdin and writes prompts to
      stderr; final changelog block to stdout (so it can be
      piped).
- [ ] `--non-interactive --decisions <file>` runs without
      prompts; missing decisions default to skip.
- [ ] `--dry-run` writes nothing to the database; output prefixed
      with `[DRY RUN]`.
- [ ] Accepting a proposal writes a row to
      `calibration_proposals` with `decision=accepted` and
      updates `heuristic_thresholds`.
- [ ] `--skill-md <path>` auto-detects `--since` from the most
      recent changelog footer date.
- [ ] Final stdout block is paste-ready markdown matching the
      `export-changelog` format.
- [ ] `tests/calibration_walkthrough.rs` covers accept, skip,
      dry-run, since-empty, and missing-decisions-default-skip.
- [ ] `cargo clippy --all-targets -- -D warnings`, `cargo fmt
      --check`, `nix flake check` clean.

## Files likely touched

- `src/calibration/walkthrough.rs` (new)
- `src/cli/args.rs` (+ `Walkthrough` variant under placeholder)
- `src/commands/calibration.rs` (+ dispatch arm)
- `src/calibration/mod.rs` (+ `pub mod walkthrough;`)
- `Cargo.toml` (+ `dialoguer`)
- `tests/calibration_walkthrough.rs` (new)

## Pitfalls

- **TTY detection.** Default `interactive` to `atty::is(Stdin)`
  if neither flag is set. Don't prompt when stdin is a pipe;
  fail loudly if the user wants interactive but stdin isn't a
  TTY.
- **Atomic accept.** The `propose` → `decide accept` sequence
  must be one transaction (or the proposal row visible to other
  processes between steps is misleading). Wrap in
  `db.transaction()`.
- **Rationale escaping in changelog.** User rationale flows
  into the markdown block; escape `<`, `>`, `|` so it doesn't
  break the markdown. The `export-changelog` formatter (already
  shipped) likely handles this; verify.
- **Empty walkthrough.** If `analyze` returns no candidate
  proposals, print "no candidates above min-n" and exit 0. Don't
  prompt for nothing.
- **`--since` parse errors.** Accept `YYYY-MM-DD`; reject
  anything else with a clear message. Don't try to be flexible
  with date formats.
- **Skill-md parsing.** Extracting the most recent date from
  the SKILL.md changelog footer is fragile (markdown is loose).
  Use a strict regex matching `^### (\d{4}-\d{2}-\d{2}) —`;
  if no match, fall back to no `--since`. Document the regex in
  the code comment.
- **Shared file with Phase 02.** `src/cli/args.rs` and
  `src/commands/calibration.rs` are also touched by Phase 02.
  Use the `// WALKTHROUGH command here` placeholder Phase 02
  left.
- **Non-interactive decision-file schema.** Lock the JSON shape
  in step 4. If the ai-skills calibrate mode generates this
  file programmatically (Phase 07), the contract matters.
- **Postgres transactions across multiple commands.** The flow
  is `analyze` (read) → `propose` (write) → `decide` (write) →
  `export-changelog` (read). Each is its own transaction in the
  shipped code; `walkthrough` orchestrates rather than merges
  them. That's fine — concurrency isn't a concern (single-user
  workflow).

## Reference

- Suite README: `docs/planning/calibration-suite/README.md`.
- Helpers from Phase 02: `02-skillnet-helper-commands.md`.
- JSON schema from Phase 03: `03-skillnet-analyze-schema-surprises-doc.md`.
- Existing commands wired together: `analyze`, `propose`,
  `proposals`, `decide`, `export-changelog`.
- Phase that wraps this from the skill: `07-ai-skills-hooks-calibrate-mode.md`.
- Release that ships it: `05-skillnet-0.4-release.md`.
- `dialoguer`: <https://docs.rs/dialoguer>.
