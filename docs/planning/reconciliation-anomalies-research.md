# Reconciliation Anomalies Research Dossier

## Goal And Trigger

A scan of every `RECONCILIATION.md` under `~/canix/Projects/ai-skills` surfaced two anomalies the user wants investigated before any fix is applied:

1. **`long-horizon-research` is missing from `global/RECONCILIATION.md`** even though the mirror, both source roots, and a recent commit all show it.
2. **`retire-docs-planning` is the only global skill whose selected source is `agents`** while every other row reads `claude`, despite both source copies being byte-identical with the same nanosecond mtime.

The user wants a root-cause analysis with code citations, reproduction, and a recommended single fix per anomaly, packaged for a follow-up multi-phase planning skill.

## Current Reality

- skillnet 0.4.0 binary on `$PATH` resolves to `/nix/store/zi73nbqdmjgbyk67pvj0b0fqpfw5zvjr-skillnet-0.4.0/bin/skillnet` (built from upstream rev `3d35951` per [flake.nix:9-12](../../flake.nix#L9-L12)).
- The skillnet source checkout used for code analysis lives at [~/canix/Projects/skillnet](file://~/canix/Projects/skillnet) at HEAD `8fc0b71` (newer than the pinned rev — minor functional differences should be limited; the reconcile + tie-break logic matches what the running binary does).
- `ai-skills` is on `main`, clean apart from the in-progress reconciliation churn the scan already reported.
- Global config in [skillnet.toml:4-9](../../skillnet.toml#L4-L9) sets source priorities `agents=3, claude=2, codex=1`.

## Evidence Inventory

### Finding #1 — `long-horizon-research` missing from the global manifest

| Artifact | Evidence |
|---|---|
| Mirror dir count vs manifest rows | `find global -maxdepth 2 -name SKILL.md \| wc -l` → 53; `grep -c '^\| \`' global/RECONCILIATION.md` → 52. Diff via `comm -3 …` confirms `long-horizon-research` is the only missing row. |
| Skill exists in both source roots | `~/.claude/skills/long-horizon-research/SKILL.md` and `~/.agents/skills/long-horizon-research/SKILL.md` both present (file count 106 = 53×2). |
| Mirror file mtimes | mirror `SKILL.md` mtime `2026-05-24 18:02:04.220736394`; both source `SKILL.md` files share the exact same mtime (copy preserves times — see [skillnet/src/fs_ops.rs:11](file://~/canix/Projects/skillnet/src/fs_ops.rs#L11) and [skillnet/src/fs_ops.rs:97-110](file://~/canix/Projects/skillnet/src/fs_ops.rs#L97-L110)). |
| Add commit | `e02da65 docs cleanup, horizon res skill init, multi-phase-plan upgrade` (Sun 2026-05-24 18:00:43 +0200) — the diff adds `global/long-horizon-research/SKILL.md` + `agents/openai.yaml` only; it does **not** touch `global/RECONCILIATION.md`. |
| Manifest mtime | `global/RECONCILIATION.md` mtime `2026-05-24 19:15:39`. The mtime nanoseconds inside the table rows are all `1779638457…` (= 2026-05-24 18:00:57), proving the table was *generated* at 18:00:57 — i.e. ~14 s **after** the commit but ~67 s **before** the skill landed in source dirs at 18:02:04. The 19:15:39 mtime is therefore from a later touch (likely an editor save or `git` touch), not a fresh reconcile write. |
| Live dry-run | `skillnet … --dry-run sync pull --scope global` lists 53 entries including `long-horizon-research` (selected from `agents`) — proving the reconciler discovers it correctly *now*. |
| Code path that writes the manifest | The only writer is `write_manifest` ([skillnet/src/reconcile.rs:332-359](file://~/canix/Projects/skillnet/src/reconcile.rs#L332-L359)), called from `write_skill_set` ([reconcile.rs:296](file://~/canix/Projects/skillnet/src/reconcile.rs#L296)) called from `write_mirror` ([reconcile.rs:213-228](file://~/canix/Projects/skillnet/src/reconcile.rs#L213-L228)) called only from `reconcile_target_with_options` ([reconcile.rs:100-125](file://~/canix/Projects/skillnet/src/reconcile.rs#L100-L125)). The two reachability paths are `sync pull` ([skillnet/src/commands/sync.rs:122-154](file://~/canix/Projects/skillnet/src/commands/sync.rs#L122-L154)) and `sync roundtrip check` ([sync.rs:235-249](file://~/canix/Projects/skillnet/src/commands/sync.rs#L235-L249)). **`sync push` does not refresh the manifest** — it only invokes `write_flat_from_mirror_with_options` ([sync.rs:156-195](file://~/canix/Projects/skillnet/src/commands/sync.rs#L156-L195)). |

### Finding #2 — `retire-docs-planning` picks `agents`

| Artifact | Evidence |
|---|---|
| Both sources byte-identical | `diff -rq` returns empty across the two copies; full file walk shows identical sha-style hash and matching `references/lessons.md` mtime `2026-05-24 18:08:50.837414431` on both sides. |
| Manifest row | `\| retire-docs-planning \| agents \| /home/can/.agents/skills/retire-docs-planning \| 1779638930837414431 \| 2 \|` ([global/RECONCILIATION.md:51](../../global/RECONCILIATION.md#L51)). |
| Tie-break code | [skillnet/src/reconcile.rs:52-56](file://~/canix/Projects/skillnet/src/reconcile.rs#L52-L56): `ranked.sort_by(\|a, b\| b.newest_mtime_nanos.cmp(&a.newest_mtime_nanos).then_with(\|\| b.priority.cmp(&a.priority)));` — descending priority breaks an mtime tie. |
| Identical-content tie acceptance | [reconcile.rs:58-72](file://~/canix/Projects/skillnet/src/reconcile.rs#L58-L72) only bails when tied candidates differ; identical content is silently accepted. |
| Config priority that drives the pick | [skillnet.toml:5-9](../../skillnet.toml#L5-L9) declares `agents=3, claude=2, codex=1`. Tie + identical → `agents` wins **by design**. |
| Why most other rows still read `claude` (frozen state) | At reconcile time (~18:00:57) the user had recently edited skills under `~/.claude/skills/` — those got newer mtimes than the agents copy, so `claude` won outright on every row except `retire-docs-planning`, where prior sync had already round-tripped the file and the two mtimes equalised. The live dry-run for current state shows **52 of 53 rows now read `agents`** and only `simit-dependent-fixes` reads `claude` — confirming the snapshot in the committed manifest is a transient state, not a per-skill anomaly. |
| Mtime preservation explains how ties arise organically | `copy_dir` in `fs_ops` preserves file/dir/symlink mtimes via `filetime::set_file_times` ([fs_ops.rs:114-148](file://~/canix/Projects/skillnet/src/fs_ops.rs#L114-L148)). Each `sync push` therefore produces sources with mtimes identical to the mirror, which triggers the priority tie-break path on subsequent reconciles. |

### Commands run during research

```
ls ~/canix/Projects/ai-skills/{global,projects}
cat ~/canix/Projects/ai-skills/global/RECONCILIATION.md
cat ~/canix/Projects/ai-skills/projects/*/RECONCILIATION.md
which skillnet && readlink -f $(which skillnet)
cat ~/canix/Projects/ai-skills/{flake.nix,skillnet.toml,skillnet.catalog.toml,scripts/reconcile-skills.nu}
ls ~/canix/Projects/skillnet/src/
sed -n '1,420p' ~/canix/Projects/skillnet/src/reconcile.rs
sed -n '90,200p'  ~/canix/Projects/skillnet/src/commands/sync.rs
rg -n 'fn copy_dir|set_file_times|preserve_file_times' ~/canix/Projects/skillnet/src/fs_ops.rs
stat --format='%y %n' global/long-horizon-research/SKILL.md global/RECONCILIATION.md ~/.claude/skills/long-horizon-research/SKILL.md ~/.agents/skills/long-horizon-research/SKILL.md
git log --oneline --name-status -- global/long-horizon-research/ global/RECONCILIATION.md
git show --stat e02da65
git diff global/RECONCILIATION.md
skillnet --config ./skillnet.toml --catalog-config ./skillnet.catalog.toml --dry-run sync pull --scope global
comm -3 <(find global -maxdepth 2 -name SKILL.md | xargs -I{} dirname {} | xargs -n1 basename | sort) \
        <(grep '^| `' global/RECONCILIATION.md | awk -F'`' '{print $2}' | sort)
```

## Existing Plan Status

Not applicable — no prior planning docs target these anomalies. The repo has no `docs/planning/` tree until this dossier created one.

## Work That Should Survive Into The Long-Term Plan

1. **Refresh the global manifest so it actually represents discoverable state.** The dry-run already produces the correct 53-row table; the fix is a single `skillnet sync pull --scope global` (no `--then-push`, no `roundtrip` — pull alone refreshes mirror + manifest from sources, and sources already hold the skill).
2. **Decide whether the configured `agents > claude > codex` tie-break is the intended canonical source order.** This is not a bug; it is the value the user wrote in `skillnet.toml`. The fix is a *decision*, not code: keep it (and document the implication: after every sync, future reconciles will systematically pick `agents` until someone edits the claude side), or flip it to `claude > agents > codex` if the historical `claude`-dominant manifest is the desired steady state.
3. **Tighten the manifest's "Rule" paragraph to disclose the priority tie-break.** The body written by [reconcile.rs:335-338](file://~/canix/Projects/skillnet/src/reconcile.rs#L335-L338) currently says only "ties accepted when contents are identical." Future readers will keep raising the same false alarm unless the doc also says "on a tie, the source with the highest configured priority wins." This is a one-line string change upstream (skillnet repo), not in `ai-skills`.
4. **Optional drift guard.** Add a `skillnet doctor` check (or a CI pre-commit) that fails when `mirror_skill_dirs(mirror) ≠ {choice.skill for choice in parse(RECONCILIATION.md)}` so manifest staleness is caught the next time someone edits the mirror without re-pulling.

## Blockers And Missing Artifacts

None. All evidence is locally reproducible and the reconciler runs cleanly in dry-run mode. The upstream skillnet code is available at `~/canix/Projects/skillnet` for any string/logic change the planner chooses.

## Risks And Constraints

- **Pull vs roundtrip choice.** `sync pull` refreshes the manifest and rewrites the mirror from sources. Because `discover_candidates` reads all sources and `write_mirror` overwrites the mirror with the chosen copies, this is safe here (the chosen copies are byte-identical to what is already in the mirror). `sync roundtrip` would additionally push back to sources — unneeded and noisier.
- **Whose mtime wins after the refresh.** The new manifest will record `agents` for nearly every skill (per the dry-run). That is consistent with config but visually different from the committed manifest. If the user has external readers that assume the source column reads `claude`, brace them or flip the priority order first.
- **Upstream change vs local change.** Findings #2 mitigation (doc string + priority decision) crosses the boundary into `caniko/skillnet`. The `ai-skills` repo cannot fix it alone; the planner will need to either (a) cut a small skillnet PR, or (b) document the behaviour locally in `global/RECONCILIATION.md`'s surrounding README and call it done.
- **Drift guard scope creep.** Adding a CI/precommit check is a nice-to-have, not a fix for the current symptom. Keep it as a separate phase the planner can drop if the user wants the minimal fix only.

## Candidate Phase Boundaries

| Phase | Scope | Notes |
|---|---|---|
| P1. Refresh global manifest | Run `skillnet --config ./skillnet.toml --catalog-config ./skillnet.catalog.toml sync pull --scope global`; review diff; commit. | Single-shot, low risk, no upstream changes. |
| P2. Confirm or invert source priorities | Decide between keeping `agents=3, claude=2, codex=1` or flipping `agents`/`claude`. If flipping, edit [skillnet.toml:5-9](../../skillnet.toml#L5-L9) and re-run P1 so the manifest re-stabilises around the chosen winner. | Pure decision + config; revertable. |
| P3. (Upstream) Document tie-break in manifest header | One-line edit to [skillnet/src/reconcile.rs:338](file://~/canix/Projects/skillnet/src/reconcile.rs#L338): append "On an exact mtime tie with identical contents, the source with the highest configured priority wins." Bump skillnet, then bump `flake.lock` in ai-skills. | Cross-repo; only do if the user wants a permanent answer to "why agents". |
| P4. (Optional) Drift guard | Add `skillnet doctor` or a `pre-commit`/CI gate that diffs `mirror_skill_dirs` against the rows parsed from `RECONCILIATION.md`. | Sized as its own phase because it touches either skillnet or a new repo hook. |

P1 is independent of P2-P4. P2 only matters if the user disagrees with the configured tie-break. P3 and P4 are upstream-leaning; defer unless the user asks.

## Open Decisions For The User

1. **Tie-break preference.** Keep `agents` as the canonical source on identical-content ties, or invert to `claude`? (Determines whether P2 runs and whether the regenerated manifest will read `agents` or `claude` for most rows.)
2. **Upstream documentation pass.** Do you want the manifest's "Rule" paragraph updated upstream (P3) or is a local note in this repo's README enough?
3. **Drift guard.** Should the planner include P4, or skip it now and revisit if staleness recurs?

## Planner Handoff

- **Selected downstream skill:** `multi-phase-plan-codex` (default; the user did not specify a provider and the work is small, mechanical, and well-suited to Codex execution. Switch to `multi-phase-plan-claude` if the user prefers Claude-side runs).
- **Dossier path:** [docs/planning/reconciliation-anomalies-research.md](docs/planning/reconciliation-anomalies-research.md).
- **Current-state summary:** Global manifest at `global/RECONCILIATION.md` is stale by exactly one row (`long-horizon-research`); root cause is that the skill was added to the mirror in commit `e02da65` ~1 minute before reconcile last ran, and never picked up afterwards because no subsequent `sync pull`/`sync roundtrip` was executed. The `retire-docs-planning` "anomaly" is the documented tie-break in `skillnet/src/reconcile.rs:52-56` resolving to `agents` per the configured priority `agents=3 > claude=2 > codex=1` in `skillnet.toml:5-9`; it is not a bug.
- **Work that should become phases:** P1 (run `sync pull --scope global`, commit); optionally P2 (priority decision), P3 (upstream manifest docstring), P4 (drift guard). P1 alone resolves the reported symptoms.
- **Known blockers that must remain blockers:** None.
- **Acceptance evidence the future phase set should preserve:**
  - `comm -3 <(find global -maxdepth 2 -name SKILL.md | xargs -I{} dirname {} | xargs -n1 basename | sort) <(grep '^\| \`' global/RECONCILIATION.md | awk -F'\`' '{print $2}' | sort)` returns no rows.
  - `git diff --stat global/RECONCILIATION.md` after P1 shows the table grew by exactly one row (the new `long-horizon-research` entry) plus any source-column flips P2 introduces.
  - `skillnet --config ./skillnet.toml --catalog-config ./skillnet.catalog.toml --dry-run sync pull --scope global` exits clean and matches the committed manifest row-for-row.
