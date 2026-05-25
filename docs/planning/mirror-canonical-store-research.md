# Mirror-As-Canonical-Store Research Dossier

## Goal And Trigger

After the prior reconciliation-anomalies investigation, the user picked **Option 4**: invert the model so the `ai-skills` mirror at `~/canix/Projects/ai-skills/{global,projects/<name>}` is the *single canonical store*, and `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`, and per-project `.agents/skills` / `.claude/skills` / `.codex/skills` / `skills/` / `.codex-plugin/skills` / `.claude-plugin/skills` become *generated read-only views*. The intent is to dissolve `reconcile`, `choose_latest`, priority tie-breaks, and mtime-driven selection — there is only one writable copy of any skill.

This dossier feeds a follow-up multi-phase planner. The work spans Rust (skillnet CLI/lib), Nix/Home Manager (skillnet hmModule + canix consumer), config schema, and downstream tools (skill-creator, Claude Code, Codex CLI). It is a multi-repo refactor with a non-trivial cut-over.

## Current Reality

- skillnet binary on `$PATH` is `/nix/store/zi73nbqdmjgbyk67pvj0b0fqpfw5zvjr-skillnet-0.4.0/bin/skillnet`, built from rev `3d35951` per the now-deleted `ai-skills/flake.nix` (still in `HEAD`; see *Mid-flight state* below).
- Source-of-truth code lives at [~/canix/Projects/skillnet](file://~/canix/Projects/skillnet) on local HEAD `8fc0b71` (a few commits ahead of the running binary; differences should not affect this refactor's design surface).
- `ai-skills` working tree is **mid-cleanup**: `git status` shows `flake.nix`, `flake.lock`, `.envrc`, `scripts/reconcile-skills.nu`, and every `projects/<name>/INDEX.md` already deleted (uncommitted). The user is partway down the Option 4 road already.
- Both `~/.agents/skills` and `~/.claude/skills` contain 53 real directories each (no symlinks today); `~/.codex/skills` is empty (the `.codex` dir holds only Codex CLI state).
- `/home` (`/dev/nvme0n1p2`) and `~/canix/Projects` (`/dev/nvme0n1p4`) are **separate btrfs partitions on the same physical disk**, so cross-mount absolute-path symlinks work.
- HM consumption: [canix/home/hosts/runner/can.nix:32-160](file://~/canix/Projects/canix/home/hosts/runner/can.nix#L32-L160) imports `inputs.skillnet.hmModules.default` and declares the full `programs.skillnet.settings.{global,project_source_rules,projects}` block today.

### Mid-flight state worth noting before planning

`git status` already deletes:

- `flake.nix`, `flake.lock`, `.envrc` — `ai-skills` is being de-Nixed at the repo level (canix-side HM module now owns the install).
- `scripts/reconcile-skills.nu` — the user-facing reconcile loop is being retired.
- All `projects/<name>/INDEX.md` files — the per-project landing pages produced by skillctl are gone.

These deletions are consistent with Option 4: a canonical mirror has no need for a per-repo flake (canix already provides the package), no reconcile script (there is no reconcile), and no per-project landing pages (the directory itself is the index). The planner should incorporate them rather than re-introduce them.

## Evidence Inventory

### Skillnet CLI surface area (today)

[skillnet/src/cli/args.rs:46-95](file://~/canix/Projects/skillnet/src/cli/args.rs#L46-L95) declares the top-level commands. Grouped by Option 4 fate:

| Command | Today's role | Fate under Option 4 |
|---|---|---|
| `status` ([args.rs:48](file://~/canix/Projects/skillnet/src/cli/args.rs#L48), [commands/status.rs](file://~/canix/Projects/skillnet/src/commands/status.rs)) | Scope divergence + catalog health. | **Keep, simplify.** Divergence becomes "view drift" instead of "source-vs-mirror." |
| `doctor` ([args.rs:60](file://~/canix/Projects/skillnet/src/cli/args.rs#L60), [commands/doctor.rs](file://~/canix/Projects/skillnet/src/commands/doctor.rs)) | Checks `sync_paths` invariants — sources include agents but no sync_path etc. | **Rewrite.** New invariants: every configured view target points at the right mirror skill set; no orphan view symlinks; mirror has no skill without a SKILL.md. |
| `sync pull` ([args.rs:425-454](file://~/canix/Projects/skillnet/src/cli/args.rs#L425-L454), [commands/sync.rs:93-154](file://~/canix/Projects/skillnet/src/commands/sync.rs#L93-L154)) | Reconcile + write mirror from live sources. | **Delete.** No reconcile under canonical mirror. |
| `sync roundtrip` ([args.rs:456-473](file://~/canix/Projects/skillnet/src/cli/args.rs#L456-L473)) | Pull then push. | **Delete.** Vestigial without pull. |
| `sync push` ([args.rs:474-488](file://~/canix/Projects/skillnet/src/cli/args.rs#L474-L488), [sync.rs:156-195](file://~/canix/Projects/skillnet/src/commands/sync.rs#L156-L195)) | Write mirror → sync_paths. | **Repurpose / rename → `view sync`.** Same write direction, but targets become generated view paths and the operation is idempotent regeneration of symlinks (or copy tree), not a write-back. |
| `sync status` ([args.rs:489-500](file://~/canix/Projects/skillnet/src/cli/args.rs#L489-L500)) | Live-vs-mirror divergence summary. | **Repurpose → `view status`.** "Are the views in sync with the mirror?" |
| `sync diff` ([args.rs:501-509](file://~/canix/Projects/skillnet/src/cli/args.rs#L501-L509)) | File-level mirror/live diff. | **Repurpose → `view diff`.** Detects drift caused by external writes (rm, edit) into views. |
| `skill list/show/delete/rename/move` ([args.rs:512-548](file://~/canix/Projects/skillnet/src/cli/args.rs#L512-L548), [commands/skill.rs](file://~/canix/Projects/skillnet/src/commands/skill.rs)) | CRUD on mirrored skills. | **Keep, extend.** Already mirror-first today (`commands/skill.rs:68-127` operates on the mirror). Add `skill new` (currently missing — there is no command to create a new skill in the mirror; skill-creator plugin or hand-editing fills the gap). Each write should also call `view sync` for affected scopes. |
| `scope list/sources` ([args.rs:550-561](file://~/canix/Projects/skillnet/src/cli/args.rs#L550-L561)) | Print mirror scopes + configured sources. | **Keep `list`. Repurpose `sources` → `views`.** Sources are gone; views remain. |
| `project list/add/remove` ([args.rs:563-590](file://~/canix/Projects/skillnet/src/cli/args.rs#L563-L590)) | Manage `projects[]` config. | **Keep.** Projects still exist; only their *source* concept changes. |
| `catalog *` ([args.rs:86-89](file://~/canix/Projects/skillnet/src/cli/args.rs#L86-L89)) | Generate / validate skill catalog metadata. | **Keep unchanged.** Catalog reads the mirror; no dependence on sync. |
| `calibration *` ([args.rs:91-92](file://~/canix/Projects/skillnet/src/cli/args.rs#L91-L92)) | Multi-phase-plan calibration. | **Keep unchanged.** `rg -n source\|sync_path src/calibration/` shows the only "source" tokens are calibration *threshold sources*, not file sources. |
| `hook ingest/install/uninstall/status` ([args.rs:290-330](file://~/canix/Projects/skillnet/src/cli/args.rs#L290-L330)) | Claude Code hook lifecycle. | **Keep unchanged.** Hooks target `~/.claude/settings.json`, orthogonal to the source-roots question. |
| `completions` | Shell completions. | **Keep.** |

### Library surface area (today)

[skillnet/src/reconcile.rs](file://~/canix/Projects/skillnet/src/reconcile.rs):

- `discover_candidates`, `discover_regular`, `discover_system`, `choose_latest`, `candidate_from_path`, `Candidate`, `Choice` — **all deletable**. They exist only because today there are multiple writable sources.
- `reconcile_target_with_options`, `write_mirror`, `write_manifest` — **delete** (`write_mirror` and the manifest writer are reconcile-internal).
- `mirror_skill_dirs` — **keep**. It is the only function that enumerates the mirror; multiple callers ([commands/status.rs:81](file://~/canix/Projects/skillnet/src/commands/status.rs#L81), [commands/mirror.rs:10](file://~/canix/Projects/skillnet/src/commands/mirror.rs#L10), [commands/sync.rs:744](file://~/canix/Projects/skillnet/src/commands/sync.rs#L744)). Move to `mirror.rs` after the reconcile module is deleted.
- `write_flat_from_mirror_with_options` — **keep, rename** (e.g., `materialize_view` or `write_view`). This *is* the Option 4 view-materialization primitive.
- `write_skill_set` — **keep**, with the `manifest: Option<…>` parameter removed.
- `overwrite_action` ([reconcile.rs:308-330](file://~/canix/Projects/skillnet/src/reconcile.rs#L308-L330)) — **delete** along with `WriteOptions.allow_older` semantics. With one canonical writer there are no "older or equal-mtime" conflicts; view materialization is replace-or-skip-identical.
- `WriteOptions.allow_delete` — **keep** as a guard on view sync, repurposed to mean "remove view entries that no longer correspond to a mirror skill."

[skillnet/src/model.rs](file://~/canix/Projects/skillnet/src/model.rs):

- `Source`, `Candidate`, `Choice` — **delete**.
- `Target` — **keep, slim down**. `mirror_path` stays; `sources` is deleted; `sync_paths` is renamed to `view_paths`; `stale_codex_skill_paths` is deleted (no more legacy cleanup path needed; views just don't include a codex destination).

[skillnet/src/config.rs](file://~/canix/Projects/skillnet/src/config.rs):

- `GlobalConfig.{sources, sync_paths, stale_codex_skill_paths}` — replace with `GlobalConfig.views: Vec<ViewConfig>`.
- `ProjectSourceRule` / `ProjectConfig.extra_sources` — replace with `ProjectViewRule` and per-project `extra_views`.
- `expand_paths` helper stays.

[skillnet/src/commands/doctor.rs:71-114](file://~/canix/Projects/skillnet/src/commands/doctor.rs#L71-L114) — assertions about `sync_paths` shape are inverted into assertions about `view_paths` shape.

### Downstream consumers of `~/.agents/skills` and `~/.claude/skills`

- **Claude Code** reads `~/.claude/skills/<name>/SKILL.md` at session start (the available-skills list in the system reminder is built from a directory walk). Symlinks resolve transparently — `is_dir()` follows links by default. New skills require a new session, which matches today's behaviour.
- **Codex CLI** does not look at `~/.codex/skills` per `cat ~/.codex/config.toml` (only project trust levels) and the empty `~/.codex/skills` directory. The `stale_codex_skill_paths` config entry is already vestigial.
- **Agents framework** (`~/.agents/`) — `ls -la ~/.agents/` shows only the `skills/` subtree exists. No `settings.json`, no hook config. Whoever owns the `.agents` convention reads it as a sibling to `.claude/skills`; symlinks should work identically.
- **skill-creator plugin** at `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md` — guides the user through creating a skill but **does not auto-write** to `~/.claude/skills`. The user (or Claude session) decides where to save. Under Option 4 the destination becomes the mirror.

### Claude Code symlink resolution

`fs::read_dir` returns symlink entries; `metadata()` follows links by default, while `symlink_metadata()` does not. For an LLM agent the SKILL.md content is what matters and that travels through the link. There is no evidence Claude Code rejects symlinked skill directories (it does not appear to canonicalise paths before reading; if it did, the user would already see broken behaviour from any HM-generated tree).

### Filesystem topology

```
/dev/nvme0n1p2  /home              btrfs   (1.0T,  64% used)
/dev/nvme0n1p4  /mnt/data/...    btrfs   (5.4T,  78% used)
```

Cross-partition symlinks with absolute paths are routine. Bind mounts cross filesystems fine. No physical constraint blocks Option 4.

### Commands run during research

```
df -h ~/ ~/canix/Projects/ai-skills
stat -f -c '%T %n' ~/.claude ~/canix/Projects/ai-skills
ls -la ~/.claude/skills/ ~/.agents/skills/ ~/.codex/skills/ ~/.agents/
ls -la ~/canix/Projects/ai-skills/
git -C ~/canix/Projects/ai-skills status
git -C ~/canix/Projects/ai-skills show HEAD:flake.nix HEAD:.envrc HEAD:scripts/reconcile-skills.nu
cat ~/canix/Projects/ai-skills/skillnet.toml
cat ~/canix/Projects/canix/home/hosts/runner/can.nix  # sed lines 20-200
rg -n 'sync_paths|stale_codex|hmModule|programs.skillnet' inside skillnet + canix
sed -n '1,300p' ~/canix/Projects/skillnet/nix/hm-module.nix
sed -n '44-590p' ~/canix/Projects/skillnet/src/cli/args.rs
sed -n '1-580p' ~/canix/Projects/skillnet/src/reconcile.rs
sed -n '1-230p' ~/canix/Projects/skillnet/src/config.rs
sed -n '1-80p'  ~/canix/Projects/skillnet/src/model.rs
sed -n '1-220p' ~/canix/Projects/skillnet/src/commands/skill.rs
sed -n '90-200p' ~/canix/Projects/skillnet/src/commands/sync.rs
rg -n 'symlink|read_link|is_symlink' ~/canix/Projects/skillnet/src/
rg -n 'source|sync_path' ~/canix/Projects/skillnet/src/{calibration,catalog}/
cat ~/.claude/settings.json | head
cat ~/.codex/config.toml | grep skill
ls ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/
```

## Existing Plan Status

The only prior dossier in scope is [docs/planning/reconciliation-anomalies-research.md](reconciliation-anomalies-research.md), which is the precursor to this one. Its findings stand:

| Item | Status |
|---|---|
| Finding #1 (manifest stale, `long-horizon-research` missing) | **superseded by Option 4** — no manifest exists in the canonical model. |
| Finding #2 (`retire-docs-planning` picks `agents` per priority tie-break) | **superseded by Option 4** — no tie-break logic exists in the canonical model. |
| Recommendation P1 (run `skillnet sync pull`) | **obsolete** — the cut-over migration replaces it. |
| Recommendation P2 (priority decision) | **obsolete** — priorities go away. |
| Recommendation P3 (upstream manifest docstring) | **obsolete** — manifest goes away. |
| Recommendation P4 (drift guard) | **carry forward as Option 4 `skillnet doctor` invariants** for view drift. |

## Work That Should Survive Into The Long-Term Plan

### A. Skillnet upstream changes (`~/canix/Projects/skillnet`)

1. **Config schema migration.** Replace `GlobalConfig.{sources, sync_paths, stale_codex_skill_paths}` with `GlobalConfig.views: Vec<ViewConfig { label, path, mode }>`. Replace `ProjectSourceRule` with `ProjectViewRule`. Loader rejects legacy fields with a clear migration message (point users to `skillnet config migrate-views`).
2. **Library trim.** Delete `Source`, `Candidate`, `Choice`, `discover_*`, `choose_latest`, `reconcile_target_with_options`, `write_manifest`, `write_mirror`, `overwrite_action`. Move `mirror_skill_dirs` and `write_flat_from_mirror_with_options` into a new `mirror.rs` / `view.rs` module under their new names.
3. **CLI repurpose.** Drop `sync pull` and `sync roundtrip` entirely (or keep stubs that error out with a one-shot migration hint). Replace `sync push` with `view sync` (alias retained for one minor release). Replace `sync status/diff` with `view status/diff`. Add `skill new <scope> <name> [--template <template>]` so creating a skill no longer requires hand-creating `<mirror>/<scope>/<name>/SKILL.md`.
4. **`skill <mutating>` auto-syncs views.** Every `skill new/delete/rename/move` ends with an automatic `view sync` for the affected scope, unless `--no-view-sync` is passed.
5. **Doctor inversion.** New invariants:
   - Every configured view path exists and is either the expected symlink/file or absent.
   - No view path contains files not present in the mirror.
   - No mirror skill lacks a corresponding entry in every applicable view (allowing per-mode exclusions, e.g. project-only skills excluded from global view).
6. **Cache cleanup.** `.skillnet/cache.toml` is currently keyed by "last pulled at / live source max mtime / mirror content hash" (see [commands/sync.rs:138-146](file://~/canix/Projects/skillnet/src/commands/sync.rs#L138-L146)). With no pull, only the mirror content hash is meaningful; consider removing the file entirely or repurposing it to "last-view-synced-at."

### B. Home Manager module (`skillnet/nix/hm-module.nix`)

7. **Options surface.** Replace the implicit "use settings.global.sync_paths to decide where to copy" model with explicit `programs.skillnet.views = [ { name = "claude-global"; from = "<mirrorRoot>/global"; to = "~/.claude/skills"; readOnly = true; } ...]` declarations.
8. **Activation script.** New `home.activation.skillnet-views` block that, on every `home-manager switch`, regenerates view paths from the mirror per the chosen mechanism. Initial recommended default: per-skill symlinks (see decision matrix below). Keep the existing assertions ([hm-module.nix:180-213](file://~/canix/Projects/skillnet/nix/hm-module.nix#L180-L213)) for path validation.
9. **Backwards compatibility.** Either bump the module major version (and let canix update in lockstep) or keep a `programs.skillnet.legacy.sourceRoots = false` toggle for one release. Given there is only one downstream consumer ([canix/home/hosts/runner/can.nix](file://~/canix/Projects/canix/home/hosts/runner/can.nix)), the major bump is cleaner.

### C. canix consumer change

10. **Rewrite `programs.skillnet.settings`** in [canix/home/hosts/runner/can.nix:32-160](file://~/canix/Projects/canix/home/hosts/runner/can.nix#L32-L160) to the new `views` schema. Same projects, same destinations, no `sources`, no `sync_paths`, no `stale_codex_skill_paths`.
11. **Drop the per-project pulled config.** The legacy `project_source_rules` becomes a fixed pair of `views` (one for `.claude/skills`, one for `.agents/skills`) per project. Vendor sources for `regicide` (`vendor/fragpipe/skills`, `vendor/thespis/.agents/skills`) become **read-only mirror entries** — see *Open Decisions* on whether vendor skills become canonical-mirror entries or are dropped.

### D. ai-skills repo housekeeping

12. **Already in progress.** Accept the in-flight deletions of `flake.nix`, `flake.lock`, `.envrc`, `scripts/reconcile-skills.nu`, `projects/<name>/INDEX.md`. Add the new `docs/planning/` to tracked content and commit.
13. **Update `README.md`.** Document that the mirror is the single canonical store, and that `~/.claude/skills` / `~/.agents/skills` are HM-managed views.
14. **Retire `RECONCILIATION.md` files.** Replace with a single `MIRROR.md` (or fold into `README.md`) that explains the canonical-store model. Per-project `RECONCILIATION.md` files can be removed wholesale.
15. **`skillnet.toml` / `skillnet.catalog.toml`** — confirm whether `ai-skills` keeps an in-repo `skillnet.toml` at all. Today it duplicates what the HM module writes to `$XDG_CONFIG_HOME/skillnet/skillnet.toml`. Under Option 4 the in-repo file should either be removed (HM is authoritative) or kept as a portable fallback for non-NixOS users; pick one.

### E. Per-project canonical-vs-federated decision

16. The project list in `skillnet.toml` mixes projects that "own" their skills (e.g. `canix`, `SynDB`) with vendor-flavoured ones (`regicide`'s `vendor/fragpipe`, `vendor/thespis`). Today every project's skills live under `ai-skills/projects/<name>/`. Option 4's clean design is to keep this — `ai-skills` is the single canonical store, projects get views in their own `.claude/skills` directories pointing back at the mirror. This is the recommended default (option A below). Option B (move canonical store *into* each project repo) is a follow-up redesign, not part of this initiative.

## Blockers And Missing Artifacts

None. All evidence is locally reproducible:

- skillnet source: `~/canix/Projects/skillnet` (recursive read)
- ai-skills source: `~/canix/Projects/ai-skills` (recursive read)
- canix HM consumer: `~/canix/Projects/canix/home/hosts/runner/can.nix`
- Live state: `~/.{agents,claude,codex}/`, filesystem mounts

The one open input is the choice of **view materialization mechanism** (see *Open Decisions* below). The dossier offers a recommendation; the user must confirm before the planner emits phases.

## Risks And Constraints

### Risks

- **Project-repo views point out of the repo.** If a project lives in a git repo and `<project>/.claude/skills/<name>` is a symlink to `/data/.../ai-skills/projects/<name>/<skill>`, anyone cloning the project on another machine without `ai-skills` at the same path gets dangling symlinks. Mitigate by adding the view path to `.gitignore` (it is host-machine state) and documenting that skills must be regenerated via `skillnet view sync` on each machine. The HM module already enforces this on the user's primary box; CI machines either get a stub view or accept the dangling-link state.
- **Tools that `rm -rf ~/.claude/skills/<name>`.** Under per-skill symlinks, `rm -rf` removes the symlink only and leaves the mirror entry intact — the user re-runs `view sync` to restore. Under bind mounts the operation errors. Under HM copy the entry comes back on next `home-manager switch`. Document expected behaviour.
- **`~/.claude/skills` deletion or replacement by an agent.** Same class as above. Add a `skillnet doctor` invariant that flags drift, and surface it in the user's shell prompt or motd if they want.
- **Codex CLI conventions changing.** `~/.codex/skills` is currently empty; if Codex starts reading it, Option 4 needs a third view destination. The schema admits this (`views[]` is a list), so additive.
- **HM activation timing.** Activation runs after `writeBoundary`. If the user edits the mirror, the views are *already* live (symlinks need no regeneration to reflect a mirror file edit). Only mirror *directory-set* changes (new skill, deleted skill, renamed skill) need a re-sync, and those are exactly the operations done through `skillnet skill *` which can auto-trigger sync. So the dev loop is "edit SKILL.md in the mirror, save, done" — no `home-manager switch` per edit.
- **Bootstrap on a fresh machine.** Cloning `ai-skills` is now load-bearing for any agent that wants skills. Acceptable trade given canix already manages everything declaratively, but document in the canix README.
- **Symlinks vs `path` checks.** Some agent frameworks call `realpath` on a skill dir to derive its canonical name. If realpath returns `/data/.../ai-skills/global/<skill>`, but the framework expected `~/.claude/skills/<skill>`, names could mismatch. Mitigate by testing each agent (Claude Code, Codex CLI, agents-framework) end-to-end before declaring done.
- **Calibration DB references.** The calibration code stores threshold sources keyed by skill name. Renaming a skill in the mirror still works because the DB key is the skill *name*, not its path. No migration required.

### Constraints

- **Skillnet is an upstream Codeberg repo.** Changes require a release; canix follows it via a flake input bump. Plan accordingly (PR → release → canix lockfile bump → `home-manager switch`).
- **Single physical user.** No multi-user concerns; the canonical mirror lives in one user's home tree (well, `/data/...`, owned by the same user). Easier than a multi-tenant design would be.
- **Existing reconciliation state is already a no-op.** The pending dry-run from the prior dossier showed mirror==sources for content; the cut-over preserves user-visible state automatically. The migration is mostly schema/config, not data.

## Candidate Phase Boundaries

Provisional. Final ordering belongs to the multi-phase planner.

1. **P1 — Decision lock.** User picks the view materialization mechanism (symlinks / bind mounts / HM copy) and the per-project ownership model (federated under `ai-skills` vs. embedded in project repos). Output: a one-pager appended to this dossier.
2. **P2 — Skillnet config schema migration.** Add `ViewConfig` / `ProjectViewRule`, keep old `SourceConfig` / `ProjectSourceRule` accepted but warn-on-use. Add a `skillnet config migrate-views` command that rewrites the user's TOML.
3. **P3 — Skillnet view-sync command.** Add `skillnet view sync/status/diff` operating on the new `views[]`. Wire `skill new/delete/rename/move` to invoke `view sync` automatically. Old `sync push/status/diff` become thin aliases that delegate.
4. **P4 — Skillnet reconcile deletion.** Remove `reconcile.rs`'s discovery/choose/manifest code; move surviving functions to `mirror.rs`/`view.rs`. Remove `sync pull`/`sync roundtrip` commands entirely. Bump skillnet major. *Depends on: P2, P3.*
5. **P5 — Skillnet HM module rewrite.** Replace the source-roots options with `programs.skillnet.views` and an activation script that materialises them. *Depends on: P3.*
6. **P6 — canix consumer rewrite.** Switch [canix/home/hosts/runner/can.nix](file://~/canix/Projects/canix/home/hosts/runner/can.nix) to the new schema, bump the skillnet flake input, `home-manager switch`, verify Claude Code + Codex CLI + agents all read skills from the views. *Depends on: P4, P5.*
7. **P7 — ai-skills repo housekeeping.** Finalise the in-flight deletions, add `docs/`, retire `RECONCILIATION.md` files, update `README.md`. *Depends on: P6 (so the docs describe the live state).* Parallelisable with P6 in principle but cleaner if it lands afterwards.
8. **P8 — Doctor invariants and migration guide.** Implement the new `skillnet doctor` checks; write an upgrade guide for any external users (if any beyond canix). *Depends on: P4.*

Parallelism hints: P2/P3 are sequenceable (P3 needs P2's types); P5 can be drafted in parallel with P3 because the HM module only consumes the eventual command surface; P6 is the integration point that unblocks P7.

## Open Decisions For The User

1. **View materialization mechanism.** Decision matrix:

   | Mechanism | Read-only? | Edit-loop cost | Risk | Notes |
   |---|---|---|---|---|
   | **Per-skill symlinks** | No (filesystem-wise) but socially enforced | Zero — mirror edits reflect live | Easy to delete a symlink and confuse `skillnet doctor`; recoverable | **Recommended default.** Activation copies the directory structure; each skill dir becomes `ln -s /data/.../ai-skills/global/<name> ~/.claude/skills/<name>` |
   | Top-level symlink (`~/.claude/skills` → mirror dir) | No | Zero | Foreign tools may `realpath` and surprise; renaming the mirror dir breaks everything | Cleaner conceptually but harder to manage per-scope (claude vs. agents views need separate trees) |
   | Bind mount with `ro` | Yes (kernel-enforced) | Zero in steady state; requires fstab/systemd-mount unit | Adds a NixOS dependency to enable user-namespace mounts; `rm` errors instead of silently restoring | Strong invariant, more infra |
   | HM-managed copy (`home.file."./.claude/skills/<name>".source = mirror/global/<name>`) | Yes (Nix-store-backed) | Bad — every mirror edit needs `home-manager switch` to re-link the file into the activated profile | Wrong dev loop | **Reject** for active-author skills; could fit a "release channel" model where mirror snapshots are tagged then materialised |
   | FUSE / mergerfs | Yes (FUSE-enforced) | Zero | Adds a userspace mount daemon; brittle | **Reject as overkill** |

   *Default recommendation: per-skill symlinks*. Rationale: zero edit-loop cost matches the user's actual workflow (edit, save, ask agent), and the read-only intent is socially enforced via `skillnet doctor` + a one-line warning in `~/.claude/skills/README` that's part of every view. If the user wants kernel-enforced read-only later, the bind-mount path is additive.

2. **Per-project canonical location.** Pick A or B:
   - **A. Federated (recommended).** Canonical store stays under `ai-skills/projects/<name>/`. Project repos get view symlinks in `.claude/skills`, `.gitignored`. Ai-skills owns skill governance.
   - **B. Embedded.** Move canonical store into each project's repo at `<project>/.skills/<name>/`. ai-skills becomes an index/aggregator with symlinks pointing into project repos. Skills travel with the project.

   Recommendation: A for now (smaller blast radius; matches existing layout; the user already keeps `ai-skills/projects/<name>/`). Revisit later if you want skills to ship with project releases.

3. **Codex `.system/*` namespace.** Today `discover_system` ([reconcile.rs:376-394](file://~/canix/Projects/skillnet/src/reconcile.rs#L376-L394)) flattens `~/.codex/skills/.system/<skill>` into normal globals. Under canonical-mirror, the user authors skills in the mirror flat. Confirm there is no Codex-side feature that *requires* the `.system/` subtree (we found no evidence). Open the question with the planner so the migration explicitly removes the codex view path or, if needed, keeps a `.system/` flag in `ViewConfig`.

4. **Vendor skills (regicide).** `vendor-fragpipe`, `vendor-thespis` today are source roots inside the regicide repo. Under Option 4 they need a home: either (a) imported into `ai-skills/projects/regicide/` as plain mirror entries (loses vendor provenance), (b) kept as a separate view mode that reads the vendor path and copies into the canonical mirror on demand (a sync direction we explicitly want to abolish), or (c) excluded from the canonical mirror entirely and treated as project-local helpers Claude Code happens to find. Pick before P6.

5. **Backwards-compat window for skillnet.** Either ship one transitional release that accepts both schemas (slower migration, easier rollback) or do the breaking change in one bump (faster, requires canix lockfile bump in lockstep). Single-consumer makes the breaking change cheap.

## Planner Handoff

- **Selected downstream skill:** `multi-phase-plan-mixed` — most phases (Rust refactor, Nix module rewrite, CLI surface changes) are mechanical and Codex-friendly; the two design decisions (view mechanism, per-project ownership) are judgement-heavy and Claude-friendly. Mixed routing minimises cost-per-quality. If the user later overrides to `multi-phase-plan-codex`, the phases still execute correctly; if to `multi-phase-plan-claude`, fine.
- **Dossier path:** [docs/planning/mirror-canonical-store-research.md](mirror-canonical-store-research.md). (Companion: [docs/planning/reconciliation-anomalies-research.md](reconciliation-anomalies-research.md), superseded but useful for backstory.)
- **Current-state summary:** Skillnet today implements a multi-source-roots model with mtime-based selection (`discover_candidates` + `choose_latest` in `src/reconcile.rs:26-84`). The user has decided this is the wrong invariant and wants the `ai-skills` mirror to be the single canonical store, with `~/.{agents,claude,codex}/skills` and per-project `.{agents,claude,codex}/skills` becoming generated read-only views. The repo is mid-cleanup: `flake.nix`, `scripts/reconcile-skills.nu`, and per-project `INDEX.md` files are already deleted in the working tree. The HM module that the canix consumer uses is upstream in `skillnet` at `nix/hm-module.nix`; only one consumer (canix/home/hosts/runner/can.nix) exists today.
- **Work that should become phases:** P1 decision lock → P2 schema migration → P3 view-sync command → P4 reconcile deletion → P5 HM module rewrite → P6 canix consumer rewrite → P7 ai-skills repo housekeeping → P8 doctor invariants + migration guide. Provisional dependencies in *Candidate Phase Boundaries*.
- **Known blockers that must remain blockers instead of being planned around:**
  - User must answer Open Decisions #1 (view mechanism) and #2 (per-project ownership) before phases P2 onward can be specified concretely. The other open decisions can be resolved inline by phases.
  - Skillnet must release before canix can bump; lockstep release timing belongs in the plan.
- **Acceptance evidence the future phase set should preserve:**
  - `skillnet sync pull --scope global` returns "command not found" (P4 acceptance).
  - `skillnet view status --scope global` reports zero drift on a clean tree (P3 acceptance).
  - `rg reconcile skillnet/src/` returns no live code references (P4 acceptance).
  - `find ~/.claude/skills -maxdepth 1 -type l | wc -l` equals the count of mirror skills under `global/` (P6 acceptance, assuming the symlink mechanism is chosen).
  - Claude Code, in a fresh session, lists every mirror skill in its available-skills index (P6 acceptance — manual smoke test).
  - The canix `home-manager switch` succeeds on `runner` with the new HM schema (P6 acceptance).
  - `skillnet doctor` flags zero invariant violations with the new doctor implementation (P8 acceptance).

---

# Addendum: Option B (Embedded Per-Project Canonical) Locked

## Goal And Trigger (revised)

The user locked the two open decisions from the prior pass:

1. **View mechanism: per-skill symlinks** (matches the dossier's recommendation).
2. **Per-project canonical: Option B — Embedded.** Project skills live in `<project>/.skills/<name>/` inside each project's own repo; `ai-skills/projects/<name>/` becomes a federation aggregator that points back into those repos. `ai-skills/global/<name>/` remains canonical for global skills (unchanged).

Option B has materially different ramifications than the dossier's recommended Option A. This addendum supersedes only the *per-project* aspects of the prior dossier; the global-store sections (skillnet library trim, HM module for `~/.{agents,claude}/skills`, reconcile deletion) carry forward unchanged.

## Current Reality (Option B specific)

The per-project state is **already most of the way to Option B**, just under a different convention. Inventory of all 12 configured projects:

| Project | Path | Branch | Dirty lines | Skills | `.skills/` exists? | `.agents/skills/` tracked | `.claude/skills/` tracked | Notes |
|---|---|---|---:|---:|---|---|---|---|
| SynDB | `~/canix/Projects/SynDB` | rapid | 17 | 15 | no | yes (17 files) | no | Pattern A — agents-canonical |
| ai-yolo-nix | `~/canix/Projects/ai-yolo-nix` | feat/yh-dev-subcommand | 5 | 21 | no | yes (48 files) | no | Pattern A |
| canix | `~/canix/Projects/canix` | runner-postgres | 4 | 9 | no | yes (14 files) | yes (14 files, identical trees) | Pattern B — duplicated |
| codex | `~/canix/Projects/codex` | main | 16 | 10 | no | no | no (`.claude/` is `.gitignored` line 34) | Pattern C — local-only |
| CourseOfLife | `~/canix/Projects/CourseOfLife` | trunk | 13 | 1 | no | no | no | Pattern C |
| fragpipe-mcp | `~/canix/Projects/fragpipe-mcp` | main | 3 | 4 | no | no | no | Has tracked `skills/` (4 files) — uses `root-skills` convention |
| goose | `~/canix/Projects/upstream/goose` | nushell-support | 8 | 4 | no | yes (5 files, real tree) | yes (4 files, **all git symlinks** mode `120000` → `../../.agents/skills/<name>`) | Pattern D — already Option B in miniature, just with `.agents/skills/` as canonical |
| nix-crossbow | `~/canix/Projects/nix-crossbow` | main | 2 | 1 | no | yes (2 files) | no | Pattern A |
| plinth | `~/canix/Projects/solo/plinth` | poc | 1 | 1 | no | yes (1 file) | no | Pattern A |
| regicide | `~/canix/Projects/solo/game-dev/regicide` | bevy-replicated-migration | 135 | 36 | no | yes (38 files) | yes (38 files, **identical SHAs**) | Pattern B — duplicated. Heavy dirty tree. |
| rs-modde | `~/canix/Projects/rs-modde` | trunk | 70 | 7 | no | yes (7 files) | no | Pattern A |
| rs_bouldy | `~/canix/Projects/rs_bouldy` | trunk | 1 | 1 | no | yes (1 file) | no | Pattern A |

Implications:

- **No project already has `.skills/`** — picking it as the canonical directory name introduces zero naming conflicts.
- **8 of 12 projects already commit a canonical copy** to their repo today (Patterns A, B, D). Their migration is mostly a `git mv` plus a symlink rewrite.
- **3 projects keep skills local-only** (codex, CourseOfLife, fragpipe-mcp via `.agents`/`.claude`). For these the migration is a *first-time commit* of canonical content into the project repo — user decision needed per project on whether to commit.
- **Every project has a dirty working tree** (1 to 135 changed lines). The migration cannot assume a clean checkout. The plan must either (a) ask the user to commit/stash per-repo before each project migration runs, or (b) batch the dirty-tree work into a single per-project commit with the migration content.
- **Two projects are forks the user controls** (`goose` → `github:caniko/goose`; `codex` → `github:caniko/codex`); committing `.skills/` content to them is fine. No project on the list is read-only.

### Regicide vendor sources (open decision #4 carried over)

- `vendor/fragpipe` is a **git submodule** of `codeberg:caniko/fragpipe` (branch `main`). Its skills already live in the submodule's `skills/` directory and are governed by *that* project's repo. Regicide's `skillnet.toml` `extra_sources` entry [skillnet.toml:80-83](../../skillnet.toml#L80-L83) is just registering this submodule as a project-scope source.
- `vendor/thespis` is a **git submodule** of `codeberg:caniko/rs-thespis` (branch `main`). Its skills live in its own `.agents/skills/`.
- **Neither vendor dir is tracked by regicide directly** (only the submodule pointer is). The skills inside them belong to those upstream repos.

Under Option B this **resolves itself automatically**: each submodule project (`caniko/fragpipe`, `caniko/rs-thespis`) becomes a project in its own right with its own `.skills/`, and regicide just consumes them via the submodule mechanism. No special "vendor source" concept needs to survive in the skillnet schema. The `extra_sources` field for regicide can be dropped entirely. The user may want to also register `fragpipe` and `rs-thespis` as top-level entries in `skillnet.toml` if they want global visibility.

### ai-skills `projects/` tree today

`git ls-files projects/` shows every project's skills committed to ai-skills (e.g. `projects/SynDB/etl/SKILL.md`, `projects/regicide/add-hero/SKILL.md`). Under Option B this content is **deleted from ai-skills** and replaced by symlinks. That is a large git deletion: roughly the sum of all per-project SKILL.md + references files (hundreds of files). The mirror's `projects/<name>/` becomes either:

- An aggregator dir containing per-project top-level symlinks: `projects/regicide` → `/data/.../regicide/.skills/`, with one entry per project.
- Or deleted entirely; replaced by a single `PROJECTS.md` index file plus `skillnet project list` output.

### Other tooling

- `scripts/reconcile-skills.nu` is in the working-tree deletion set (HEAD has it; working tree has removed it). Confirms reconcile workflow is going away regardless.
- `skill-installer` skill ([~/.claude/skills/skill-installer/SKILL.md](file:///home/can/.claude/skills/skill-installer/SKILL.md)) installs skills into `$CODEX_HOME/skills` from `github:openai/skills`. **Does not interact with the mirror at all**; irrelevant to Option B.
- canix does not scan `ai-skills/projects/` outside of the skillnet HM block; `rg` hits in `submodules/podman/` are coincidental matches of the word "projects".
- skillnet catalog discovery ([skillnet/src/catalog/discover.rs:12-36](file://~/canix/Projects/skillnet/src/catalog/discover.rs#L12-L36)) reads `mirror_root/projects/<name>/<skill>/SKILL.md`. `is_dir()` follows symlinks by default, and `strip_prefix` works on string paths (not realpath), so **catalog continues to work transparently** if `ai-skills/projects/<name>/` is a top-level symlink farm: it scans the symlinked dir, computes `rel` as `projects/<name>/<skill>`, and rule matchers in [skillnet.catalog.toml](../../skillnet.catalog.toml) keep matching. No catalog changes required.

## Evidence Inventory (additions)

| Artifact | Evidence |
|---|---|
| Project tracking patterns | Per-project `git ls-files .agents/skills` and `git ls-files .claude/skills`; see table above. |
| Submodule provenance | [regicide/.gitmodules](file://~/canix/Projects/solo/game-dev/regicide/.gitmodules) — `vendor/fragpipe` and `vendor/thespis` are external submodules. |
| Goose pre-existing pattern | `git -C upstream/goose ls-tree HEAD .claude/skills/` returns `120000 blob …` entries — i.e. tracked symlinks, not trees. This is the exact pattern Option B will universalise. |
| canix HM consumer schema | [canix/home/hosts/runner/can.nix:32-160](file://~/canix/Projects/canix/home/hosts/runner/can.nix#L32-L160) — full project list + `project_source_rules` block needs rewrite. |
| catalog discovery safe with symlinks | [skillnet/src/catalog/discover.rs:88-100](file://~/canix/Projects/skillnet/src/catalog/discover.rs#L88-L100) `is_dir()` and `SKILL.md is_file()` follow symlinks. |
| ai-skills tracks projects/ today | `git ls-files projects/` returns hundreds of entries — Option B deletes all of them and adds back symlinks. |

### Commands run (additions)

```
for p in <12 project paths>; do
  git -C "$p" rev-parse --abbrev-ref HEAD
  git -C "$p" status --porcelain | wc -l
  git -C "$p" remote get-url origin
  find "$p/.agents/skills" "$p/.claude/skills" "$p/.skills" "$p/skills" -maxdepth 2 -name SKILL.md | wc -l
  git -C "$p" ls-files .agents/skills | wc -l
  git -C "$p" ls-files .claude/skills | wc -l
done
git -C ~/canix/Projects/upstream/goose ls-tree HEAD .claude/skills/
git -C ~/canix/Projects/canix     ls-tree HEAD .claude/skills/ .agents/skills/
git -C ~/canix/Projects/solo/game-dev/regicide ls-tree HEAD .claude/skills/ .agents/skills/
cat ~/canix/Projects/solo/game-dev/regicide/.gitmodules
ls ~/canix/Projects/solo/game-dev/regicide/vendor/{fragpipe,thespis}/.git
git -C ~/canix/Projects/codex check-ignore -v .claude/skills
git -C ~/canix/Projects/ai-skills ls-files projects/
sed -n '1,120p' ~/canix/Projects/skillnet/src/catalog/discover.rs
```

## Updated Work That Should Survive Into The Long-Term Plan

The prior dossier's **global**-store work (sections A.1–A.6, B.7–B.9, C.10 partial, D.12–D.14) carries forward unchanged. New or rewritten items:

### A′. Skillnet upstream changes — Option B additions

- **A.2′ (replaces A.2).** Trim `reconcile.rs` as before, but the surviving primitive `write_flat_from_mirror_with_options` is no longer the per-project view-sync primitive — under Option B, per-project views are **committed-in-repo relative symlinks**, not HM-activation outputs. Rename it to something like `materialize_global_view` and use it *only* for global views into `~/.{agents,claude}/skills`.
- **A.7 (new).** Schema gains `canonical_rel` (per-project, default `.skills`) and `aggregator_rel` (per-project, default `<ai-skills>/projects/<name>` as a top-level symlink). The `Target` struct splits cleanly: global targets keep `mirror_path`; project targets gain `canonical_path: Utf8PathBuf` (= `<project_root>/.skills`) and `aggregator_path: Option<Utf8PathBuf>`.
- **A.8 (new).** `skillnet skill new <project>/<name>` writes to `<project_root>/.skills/<name>/SKILL.md`, then materialises:
  1. `<project_root>/.claude/skills/<name>` → `../../.skills/<name>` (relative committed symlink).
  2. `<project_root>/.agents/skills/<name>` → `../../.skills/<name>` (relative committed symlink).
  3. `<ai-skills>/projects/<name>` → `<project_root>/.skills` (top-level absolute symlink, only created once per project — already exists thereafter).
  Atomicity: write canonical first, then symlinks, then aggregator. If a symlink op fails, the canonical persists and `skillnet doctor` flags the missing view; user can rerun `skill view sync <project>` to repair.
- **A.9 (new).** `skillnet skill move <from> <to>` and `rename` must update relative symlinks correctly (they point at the new name). `delete` removes the canonical dir AND all symlink view entries in the project + aggregator.
- **A.10 (new).** New `skillnet project sync <name>` command that idempotently regenerates the three categories of symlinks for one project (in-repo `.claude` + `.agents`, aggregator). Bulk variant `skillnet project sync --all`.

### B′. Home Manager module — Option B additions

- **B.11 (new).** HM activation **only manages global views** (`~/.claude/skills`, `~/.agents/skills` per-skill symlinks → `<ai-skills>/global/<name>`). Per-project views are committed symlinks living in each project repo; HM does not touch them. This shrinks the HM module's surface vs. the prior dossier's design.
- **B.12 (new).** New `programs.skillnet.aggregator` option that, on activation, ensures `<ai-skills>/projects/<name>` symlinks exist for every configured project where the project repo is present on disk, and warns for missing projects. This is the bootstrap touch point — see G below.

### C′. canix consumer — Option B additions

- **C.13 (new).** [canix/home/hosts/runner/can.nix:75-160](file://~/canix/Projects/canix/home/hosts/runner/can.nix#L75-L160) drops `project_source_rules` entirely; replaces with a `programs.skillnet.projects = [{ name; path; canonical_rel = ".skills"; }]` list. Each entry has only `name`, `path`, optional `canonical_rel`, and the (now-emptied) `extra_sources`/`extra_views` fields.

### D′. Per-project migration

For each of the 12 projects, the migration is one or two commits authored locally and pushed by the user. The work breaks down by pattern:

**Pattern A — agents-canonical (6 projects: SynDB, ai-yolo-nix, nix-crossbow, plinth, rs-modde, rs_bouldy):**

```
git -C <project> mv .agents/skills .skills
# replace .agents/skills with symlink farm
mkdir <project>/.agents/skills
for s in <project>/.skills/*/; do
  ln -srfT "$s" "<project>/.agents/skills/$(basename $s)"
done
git -C <project> add .skills .agents/skills
git -C <project> commit -m "Embed canonical skills under .skills/ (Option B migration)"
```

**Pattern B — duplicated (canix, regicide):**

```
git -C <project> rm -r .claude/skills        # discard duplicate (.agents/skills retained as the canonical seed)
git -C <project> mv .agents/skills .skills   # rename canonical
# generate both view symlinks
mkdir <project>/.claude/skills <project>/.agents/skills
for s in <project>/.skills/*/; do
  ln -srfT "$s" "<project>/.claude/skills/$(basename $s)"
  ln -srfT "$s" "<project>/.agents/skills/$(basename $s)"
done
git -C <project> add .skills .claude/skills .agents/skills
git -C <project> commit -m "Embed canonical skills under .skills/ (Option B migration)"
```

**Pattern C — local-only (codex, CourseOfLife, fragpipe-mcp):**

- **codex** (10 skills): user must decide whether to commit `.skills/` to the codex fork. Since it's the user's fork, recommend yes. `.gitignore` line 34 (`.claude/`) is fine because `.claude/skills/<name>` is symlinks that will themselves be `.gitignored` anyway. Don't add `.claude/skills/` to git.
- **CourseOfLife** (1 skill): same decision. Recommend yes.
- **fragpipe-mcp** (4 skills): canonical today is `<repo>/skills/` (tracked). Either `git mv skills .skills` to align with the standard, or keep `skills/` and configure `canonical_rel = "skills"` for this project (one-off override). Recommend the rename for consistency, since fragpipe-mcp's `root-skills` convention only existed to satisfy the priority-3 source rule; under Option B all sources collapse.

**Pattern D — goose (already has agents-canonical + claude-symlinks):**

- Already at the target state minus the directory name. `git mv .agents/skills .skills` then re-point the existing `.claude/skills/*` symlinks from `../../.agents/skills/<n>` → `../../.skills/<n>`. Then commit.
- Note: goose's `.claude/skills/edge-case-finder` is a single symlink blob (5 vs 4 tracked-file count is explained — `.agents/skills/edge-case-finder/` is 2 files (`SKILL.md` + `references/`), `.claude/skills/edge-case-finder` is 1 symlink).

**Dirty-tree handling:** every project has uncommitted changes today. The migration commit must be **separate from existing in-flight work** — recommend creating a `skillnet-embed-canonical` branch in each project, performing the migration there, and letting the user merge/PR when ready. This isolates the migration from per-project active work (e.g. regicide's 135-line dirty tree on `bevy-replicated-migration`).

**Per-project commit budget:** 12 commits, one per project, +1 ai-skills cleanup commit, +1 canix HM rewrite commit, +N skillnet releases (probably 1-2 across the schema/CLI/HM phases). Total ≤ ~16 commits.

### E′. ai-skills aggregator decision

Pick one of three shapes for `<ai-skills>/projects/`:

| Shape | Behaviour | Trade-offs |
|---|---|---|
| **Single top-level symlink per project (recommended)** | `<ai-skills>/projects/<name>` is one symlink to `<project_root>/.skills`. Each project's content appears under the aggregator transparently. | Per-skill granularity disappears at the aggregator level; one symlink per project keeps the aggregator tiny. Catalog discovery works (see *Current Reality*). |
| Per-skill symlinks | `<ai-skills>/projects/<name>/<skill>` symlinks per-skill. | More moving parts, more to break, no clear benefit since catalog already crosses one symlink level fine. |
| Delete `<ai-skills>/projects/` entirely | No aggregator. Catalog discovery scans live project repos directly via a new config field. | Big change to catalog discovery; loses the visual "ai-skills owns the index" affordance. |

**Recommendation: single top-level symlink per project.** Atomic per-project creation, minimal aggregator state, catalog and `skill list` keep working. Aggregator entries are `.gitignored` in `ai-skills` (machine-local state — same constraint as the per-project `.claude/skills` view symlinks).

### F′. ai-skills repo state after Option B

- `<ai-skills>/global/` — unchanged, canonical for global skills.
- `<ai-skills>/projects/` — **gitignored** directory of top-level per-project symlinks, regenerated by `skillnet project sync --all` or HM activation. No `.gitkeep`; only present on hosts with the project repos cloned.
- `<ai-skills>/RECONCILIATION.md`, `<ai-skills>/projects/<name>/RECONCILIATION.md`, `<ai-skills>/projects/<name>/INDEX.md` — all deleted. The in-flight working tree already removes the `INDEX.md` files; this finishes the job for `RECONCILIATION.md`.
- `skillnet.toml` — keeps the `[[projects]]` list with `name`, `path`, optional `canonical_rel`. Drops `project_source_rules` entirely. Drops `[global].sources`, `[global].sync_paths`, `[global].stale_codex_skill_paths`.

### G′. Fresh-host bootstrap order

A clean host needs to materialise both global views (HM-managed) and project aggregator symlinks (skillnet-managed). The order matters:

1. User clones `ai-skills` to `/data/.../ai-skills`.
2. User clones every project listed in `programs.skillnet.projects` to its configured path. (Can be automated by a `skillnet project clone --all` helper if desired — out of scope for Option B itself, follow-up phase.)
3. `home-manager switch`:
   - Activation step generates global views: `~/.claude/skills/<name>` → `<ai-skills>/global/<name>`. Idempotent.
   - Activation step generates aggregator symlinks: `<ai-skills>/projects/<name>` → `<project>/.skills`. **Tolerates missing project repos with a warning** (do not fail the activation).
4. In each project repo, `<project>/.claude/skills` and `<project>/.agents/skills` are already populated with committed relative symlinks — nothing to do.

Trade-off accepted: if the user only clones `ai-skills` without the per-project repos, the per-project skills are simply unavailable until the project is cloned. The aggregator silently lacks those entries until then. This matches the spirit of "skills travel with the code."

## Updated Risks And Constraints

New/changed under Option B:

- **Per-project commits are user-visible.** Twelve project repos gain a `.skills/` directory and view symlinks. For shared/team repos (regicide on gitlab.com/clg-gaming, canix on gitlab.com/caniko, codex on github.com/caniko) this is a normal feature commit; for forks tracking upstream (goose, codex) it potentially diverges from upstream further. The user already maintains both forks, so acceptable, but the planner should expect 12 distinct PRs/commits + 12 push events.
- **Cross-project skill sharing is harder, not impossible.** Under Option A you could lift a skill into ai-skills/global/ to share it; under Option B that path still works — promote to global if multiple projects want the same skill. Document the rule in the new `README.md`.
- **Submodule-owned skills (regicide vendor) need their parent projects added.** `caniko/fragpipe` and `caniko/rs-thespis` should be registered as top-level projects in `skillnet.toml` (or accepted as not-globally-visible if the user only wants them via the regicide submodule). Open decision; recommendation: add them as projects.
- **Pattern C projects need a "should this be committed?" call.** codex, CourseOfLife, fragpipe-mcp do not currently commit any canonical skills. The migration changes that. Per-project user confirmation belongs in the plan.
- **`.gitignore` updates per project.** Each migrated project needs `.gitignore` entries:
  - Pattern A: no `.gitignore` change needed (the view dirs are symlinks; they're committed).
  - Pattern B/D: same.
  - codex: keep existing `.claude/` ignore; do NOT add `.skills/` to ignore (we want it tracked).
- **Aggregator symlinks under `<ai-skills>/projects/` are machine-local.** Add `projects/` to `<ai-skills>/.gitignore` and remove the committed `projects/<name>/...` content (large `git rm -r`). The in-flight `git status` already deletes `projects/<name>/INDEX.md` files — finish the job with `git rm -r projects/<name>/`.
- **`skillnet doctor` has more invariants under Option B**, not fewer:
  - Per project: canonical `.skills/<name>` exists ⇔ `.claude/skills/<name>` is a symlink to `../../.skills/<name>` ⇔ `.agents/skills/<name>` is a symlink to `../../.skills/<name>`.
  - Per project: aggregator entry `<ai-skills>/projects/<name>` → `<project_root>/.skills` (or absent + warned).
  - No skill exists in `.claude/skills/` or `.agents/skills/` without a corresponding `.skills/` canonical.
  - This is a more interesting check than Option A's "view matches mirror"; surfaces real drift.
- **Carry-over from prior dossier:** all the global-view risks (foreign tools `realpath`-ing, `rm -rf` on a view symlink, fresh-host bootstrap, calibration DB key stability) still apply.

## Updated Candidate Phase Boundaries

P1 (decision lock) is **done**. The remaining phases under Option B:

1. **P2 — Skillnet config schema migration.** Add `[[projects]].canonical_rel` (default `.skills`), drop `project_source_rules` / `[global].sources` / `sync_paths` / `stale_codex_skill_paths`. Loader rejects legacy fields with a clear migration error message. Add the new `Target` shape with `canonical_path` + optional `aggregator_path`.
2. **P3 — Skillnet view-sync and project-sync commands.** `view sync` for global views; `project sync` for per-project aggregator + in-repo symlinks (idempotent regeneration). `skill new/delete/rename/move` auto-runs the relevant `*sync` for affected scopes.
3. **P4 — Skillnet reconcile deletion.** Remove `discover_candidates`, `choose_latest`, `Source`/`Candidate`/`Choice` types; delete `sync pull` and `sync roundtrip` commands. Bump skillnet major. *Depends on: P2, P3.*
4. **P5 — Skillnet HM module rewrite.** New `programs.skillnet.{views,projects,aggregator}` options. Activation generates *only* global views and aggregator symlinks (tolerating missing project repos). *Depends on: P3.*
5. **P6 — Per-project migration (12 sub-phases).** For each project, one branch `skillnet-embed-canonical`, perform the per-pattern migration above, commit, push. **Each project is independent and can run in parallel** once the migration script (or skillnet helper) is built. Recommend the planner emit P6 as a multi-sub-layer phase (see `multi-phase-dispatch`) — twelve sub-phases routable in parallel. Sub-phase routing is uniform per pattern, so cost is dominated by the largest project (regicide, 36 skills, 135 dirty lines).
6. **P7 — ai-skills repo housekeeping.** `git rm -r projects/<name>/*` content; add `projects/` to `.gitignore`; finalise in-flight deletions (`flake.nix`, `flake.lock`, `.envrc`, deleted INDEX/RECONCILIATION files); update `README.md`; commit. *Depends on: P5 (HM activation generates the aggregator symlinks that replace the committed content) and P6 (canonical content now lives in project repos).*
7. **P8 — canix consumer rewrite.** Rewrite [canix/home/hosts/runner/can.nix:32-160](file://~/canix/Projects/canix/home/hosts/runner/can.nix#L32-L160) to the new schema; bump `skillnet` flake input; `home-manager switch`; smoke-test Claude Code + Codex + agents. *Depends on: P5.*
8. **P9 — Doctor invariants + migration guide.** Implement the Option-B-specific doctor checks (per-project canonical/view/aggregator triangle, drift detection). Write a migration guide for external users (if any beyond canix) and a `skillnet project clone --all` helper for the fresh-host story. *Depends on: P4.*
9. **(Optional) P10 — Register submodule projects.** Add `caniko/fragpipe` and `caniko/rs-thespis` to the `skillnet.toml` projects list so their skills appear in the catalog independently of regicide's submodule consumption. Drops regicide's `extra_sources` block. Tiny, independent of the rest.

Parallelism:
- P2 ↔ P5 can be drafted in parallel after P3's signatures are stable.
- P6's sub-phases are fully parallel.
- P7 + P8 sequence after P5/P6 and can run concurrently with each other.
- P9 trails everything; it's the verification layer.

## Updated Open Decisions For The User

1. ~~View materialization mechanism~~ — **locked: per-skill symlinks**.
2. ~~Per-project canonical~~ — **locked: Option B embedded under `<project>/.skills/`**.
3. **Aggregator shape**: confirm "single top-level symlink per project, gitignored under `<ai-skills>/projects/`". Recommendation given; user can override to per-skill or no-aggregator if desired.
4. **Pattern C projects' commit decision**: for codex, CourseOfLife, fragpipe-mcp — commit `.skills/` to those repos as part of the migration, yes/no? Recommendation: yes for all three.
5. **Submodule-owned projects**: register `caniko/fragpipe` and `caniko/rs-thespis` as top-level projects, yes/no? Recommendation: yes (P10).
6. **`canonical_rel` default**: confirm `.skills` (recommendation); alternatives `skills`, `.agent-skills`, etc. fragpipe-mcp's existing `skills/` directory is the only project that wants something different — either rename it or use a one-off `canonical_rel = "skills"` override.
7. **Migration commit authoring**: do you want skillnet itself to perform the per-project commits (running `git -C <project> add/commit` programmatically), or only generate the working-tree changes and leave the commit to the user? Recommendation: skillnet writes the files and leaves staging/commit to the user (safer; respects dirty-tree state).
8. **Schema-breaking-change window**: same as prior dossier — single skillnet release with the breaking change, single canix lockfile bump. Recommendation unchanged: do it in one bump given single consumer.

## Updated Planner Handoff

- **Selected downstream skill:** `multi-phase-plan-mixed` (unchanged). The new sub-layer structure of P6 (twelve per-project migrations in parallel) is a strong fit for the multi-sub-layer pattern in `multi-phase-dispatch`; the cross-provider planner can route each project's sub-phase independently. The complexity of P2/P3/P4 is Codex-friendly; the Option B design framing (P5, P9) and migration policy decisions (open #4, #5, #6, #7) are Claude-friendly.
- **Dossier path:** [docs/planning/mirror-canonical-store-research.md](mirror-canonical-store-research.md) (this file — addendum supersedes the prior per-project sections only).
- **Current-state summary (Option B):** Eight of twelve projects already commit canonical skill content (under `.agents/skills/` predominantly), making Option B's migration mostly a `git mv .agents/skills .skills` plus symlink rewrite per project. Two projects (canix, regicide) need de-duplication first. Three projects (codex, CourseOfLife, fragpipe-mcp) need a first-time commit of canonical content into their fork. One pattern (goose) already implements Option B in miniature with `.agents/skills` as canonical and committed `.claude/skills/*` symlinks. Regicide's vendor sources resolve naturally because they are submodules with their own canonical stores. ai-skills's `projects/` content gets deleted from git and replaced by HM-managed symlink aggregator entries. The skillnet upstream changes are roughly the same surface as the prior dossier, plus a `Target.canonical_path` split for project scopes. The HM module shrinks because per-project views are committed in-repo and don't need activation-time generation.
- **Work that should become phases:** P2 schema → P3 view/project sync commands → P4 reconcile deletion → P5 HM rewrite → P6 per-project migration (12 parallel sub-phases) → P7 ai-skills cleanup → P8 canix rewrite → P9 doctor + bootstrap helper → optional P10 register submodule projects. Provisional dependencies above.
- **Known blockers that must remain blockers:**
  - User must answer Open Decisions #3 (aggregator shape), #4 (Pattern C commit), #5 (submodule registration), #6 (canonical_rel name), #7 (commit authoring policy). Recommendations are given but they materially affect P6/P7/P10 work products.
  - Skillnet must release before canix can bump (P8 strictly after P4).
  - P6 sub-phases each block on the parent project's working tree being committable (i.e. the user has stashed/committed the existing dirty changes on the project's active branch first); a sub-phase runs on a fresh `skillnet-embed-canonical` branch off the project's current HEAD.
- **Acceptance evidence the future phase set should preserve:**
  - Each project's working tree after P6 has: a tracked `.skills/<name>/SKILL.md` for every skill, a tracked `.claude/skills/<name>` symlink → `../../.skills/<name>` for every skill, a tracked `.agents/skills/<name>` symlink → `../../.skills/<name>` for every skill (where the project committed agents views before — Pattern A,B,D; Pattern C may omit `.claude/skills/` if `.gitignored`).
  - `find <project>/.claude/skills -maxdepth 1 -type l | wc -l` equals `ls <project>/.skills | wc -l` for every project after P6.
  - `<ai-skills>/projects/<name>` resolves via `readlink` to `<project>/.skills` for every project after P7+P8+activation.
  - `git -C <ai-skills> ls-files projects/` returns zero entries after P7 (everything is gitignored).
  - `skillnet skill list --scope <project>` finds all skills via the aggregator symlink after P8 activation.
  - `skillnet doctor` is silent under the new invariants after P9.
  - `skillnet sync pull` / `sync roundtrip` return "command not found" after P4.
  - Claude Code in a fresh session lists every project skill via the in-repo `.claude/skills` views (manual smoke test per project).
