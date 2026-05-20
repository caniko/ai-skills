---
name: feature-flag-compile-sweep
description: Domain-specific plan-and-verify workflow for auditing and tightening a Rust workspace's Cargo feature flags so default builds compile only what's needed for the user's chosen runtime (e.g. Wayland-only on Linux desktop, no Steam SDK by default, no dev-only deps in release). Produces a six-phase plan via `multi-phase-plan-codex` covering audit → workspace bevy/winit backend split → per-crate platform features → code-level cfg sweep → Nix shell + runtime verification, then verifies each phase's acceptance criteria with `cargo check` matrix + `ldd` linkage + `cargo tree` checks. Triggers on "feature flag sweep", "optimize compilation", "make default build Wayland-only", "audit feature gates", "shrink the default compile graph", "default-only-what-we-need".
---

# Feature-flag compile sweep

This skill is the domain-specific instantiation of the `plan-and-verify`
workflow for Rust workspace feature-flag hygiene — specifically the
shape we needed to make `cargo build` produce a Wayland-only binary
that doesn't drag in Steam SDK, dev-only tracing deps, or x11 unless the
user opts in.

It is appointed by `plan-and-verify` when the user's task is recognisably
about Cargo features, default compile graph shrinkage, windowing-backend
selection, or "make default builds smaller / more focused".

## When to use

- "Default flags should only compile for <runtime X>" (Wayland, x11,
  android, headless, etc.).
- "Sweep the feature flag setup — make sure everything that should be
  gated is gated."
- "Why is `<some dev-only crate>` in my release binary?"
- "Make Steam SDK opt-in", "make x11 opt-in", "shrink the default
  compile graph".
- Any time the user is uncomfortable with what `cargo tree` /
  `ldd target/release/<bin>` reveals about default builds.

Don't use this for:
- A single-feature bug fix (just edit the manifest).
- Renaming an existing feature (mechanical, no plan needed).
- Adding a single new feature for a new code path (regular dev task).

## Workflow shape

This skill is a **two-mode** wrapper, same contract as `plan-and-verify`:

### Mode 1 — `plan`

Hand the task to **`multi-phase-plan-codex`** (the Codex flavour — this
domain has historically been executed by Codex sessions) with a prompt
that fixes the phase shape to the six phases below. The phases are not negotiable
labels — the `verify` mode reads acceptance criteria back out of these
specific phase docs and the build-matrix it runs assumes their presence.

Plan directory convention: `docs/src/planning/feature-flag-sweep/`
(plural-agnostic — use this exact slug so `verify` can auto-detect).

**The six phases:**

1. **Audit & inventory** (read-only). Enumerate every `[features]`
   table, every `cfg(feature = "...")` site, every
   `cfg(target_os = ...)` gate, and a gap list of code that *should*
   be gated but isn't. Output: `docs/src/planning/feature-flag-sweep/
   AUDIT.md`.
2. **Workspace bevy/winit backend split.** The keystone manifest
   change. Strip windowing backend features from the workspace-level
   `bevy` declaration; move `android-game-activity` into a
   `[target.'cfg(target_os = "android")'.dependencies]` block; expose
   `wayland` and `x11` as opt-in features at the root crate; set
   `default = [..., "<runtime-of-choice>"]`.
3. **Client/binary crate platform features.** Mirror Phase 02 at the
   crate that builds the windowed binary (e.g. `chessbender-client`).
   Removes hardcoded `["x11", "wayland"]` from its bevy block.
4. **Test/visual crate platform features.** Same shape at any test
   harness that builds a Bevy app (e.g. `chessbender-visual-test`).
5. **Code-level cfg coverage sweep.** Work the Phase 01 gap list:
   add/strengthen gates, move always-on-but-conditionally-used deps to
   `optional = true` with `dep:` activators, record decisions in
   `COVERAGE-CHANGES.md`. Common targets: Steam SDK imports,
   `tracing-appender`/`tracing-subscriber`/`chrono` (dev-only),
   `minidumper` (crash-dumps), `ratatui`/`crossterm` (TUI dev tools).
6. **Nix shell + runtime verification.** Split `nix develop` into a
   default (wayland-only) shell and an opt-in `.#x11` shell. Update
   README with the new contract. Run `fix-loop-*` smoke skills on a
   real Wayland session to prove no runtime regression.

Routing per phase (consult `gpt-plan-routing`):
| Phase | Model |
|---|---|
| 01 audit | `5.5 medium` — judgment for *missing* gates |
| 02 workspace | `5.5 high` — feature unification trap, keystone |
| 03 client | `5.5 medium` |
| 04 visual-test | `5.5 low` — mirror of 03 |
| 05 code-level sweep | `5.5 high` — per-site judgment |
| 06 nix + verify | `5.5 medium` |

Parallelism:
- 01 blocks 05 (audit feeds the worklist) and informs 02.
- 02 blocks 03 and 04 (shared manifest contract).
- 03 and 04 can run in parallel after 02.
- 05 can run in parallel with 02/03/04 (no shared files).
- 06 is the final gate.

### Mode 2 — `verify`

Auto-detect plan dir `docs/src/planning/feature-flag-sweep/`. Read each
phase's acceptance criteria, then run **this exact build matrix** plus
the per-phase manifest checks.

**Mandatory live build matrix** (run from workspace root, regardless of
what individual phase docs say):

```bash
# 1. Default features must build (and pick the chosen runtime backend).
cargo check --quiet

# 2. Explicit single-backend builds must each succeed.
cargo check --no-default-features --features "wayland" --quiet
cargo check --no-default-features --features "x11" --quiet

# 3. No-backend build must FAIL with winit's compile_error.
cargo check --no-default-features --quiet     # expected: non-zero exit
                                              # expected: "compile_error" in stderr

# 4. Android cross-target must pick android-game-activity, not wayland/x11.
cargo tree --target aarch64-linux-android -e features -p <root-crate> \
  --depth 2 2>&1 | grep -E 'bevy feature|wayland|x11'

# 5. Default tree must NOT contain Steam SDK transitive deps.
cargo tree -e features --depth 3 2>&1 | \
  grep -iE 'steamworks|aeronet_steam|libp2p-steam'
# expected: empty output

# 6. Linkage of the default release/debug binary.
ldd target/debug/<bin-name> 2>/dev/null | grep -E 'libX11|libwayland'
# expected: libwayland-client.so.* present, libX11.so NOT present
```

For each phase, mark every checklist item PASS / FAIL / N/A. Cite
evidence (file:line, command output snippet). Read `AUDIT.md` and
`COVERAGE-CHANGES.md` first if they exist — they pre-record the
executor's claimed results, which prioritise (but don't replace) your
checks.

**Things that are not failures:**
- `cargo check --no-default-features` (with no backend) failing is
  *required* — the winit `compile_error` is the proof that the backend
  is properly gated.
- `cargo check -p <client-crate> --no-default-features` failing for the
  same reason is also expected.
- Pre-existing test compile errors in crates the plan didn't touch
  (cross-check against `git diff --name-only HEAD` and the phase docs'
  "Files likely touched" sections). Report as **caveats**, not phase
  failures.

**Things that are silent failures to watch for:**
- A workspace member crate still pinning `["x11", "wayland"]` in its
  own `bevy.features = [...]` array — Cargo feature unification will
  silently re-enable x11 in the default tree even though the workspace
  declaration is clean. Verify with:
  ```bash
  rg '"x11"|"wayland"' --type toml -- '!**/target/**'
  ```
  Only the intentional `[features]` re-export entries and the
  `chosen-runtime` default line should appear.
- `libX11.so` appearing in `ldd` output despite a clean `cargo tree` —
  means a non-bevy dep pulled it in (e.g. an xcb-based crate). Trace
  with `cargo tree -i libX11-sys` or equivalent.
- `bevy-steamworks` / `chessbender-steam` showing up in default
  `cargo tree` despite being marked `optional = true` — means a
  feature still has them in its activator list without `dep:` prefix.

## Report shape

Same as `plan-and-verify` Mode 2, but include the explicit build-matrix
section every time:

```
## Verification — feature-flag compile sweep

**Phase 01 (Audit)** — verdict
- [✓] AUDIT.md exists with 5 sections — evidence
- [✓] ... (per criterion)

... (per phase) ...

**Build matrix verified live:**
- `cargo check` (default) → exit 0 ✓
- `cargo check --no-default-features --features wayland` → exit 0 ✓
- `cargo check --no-default-features --features x11` → exit 0 ✓
- `cargo check --no-default-features` → winit `compile_error!` ✓
- `ldd target/debug/<bin>` → libwayland-client present, libX11 absent ✓
- `cargo tree --target aarch64-linux-android` → android-game-activity
  present, no wayland/x11 ✓
- `cargo tree` (default) → no steamworks/aeronet_steam/libp2p-steam ✓

**Over-delivery noted:** (if any — common pattern: executor also made
Steam deps optional+gated even when only platform-backend split was in
scope)

**Known caveats:** (pre-existing issues unrelated to the sweep)

**Net assessment:** <one sentence>
```

## Anti-patterns

- **Skipping the linkage check.** `cargo check` exit 0 proves
  compilation; it does not prove the default binary doesn't drag in
  libX11. Always `ldd` the actual binary.
- **Trusting `cargo tree` output without specifying target.** Without
  `--target`, you only see the host's resolution. Android verification
  *requires* `--target aarch64-linux-android` (or whichever Android
  triple the project uses).
- **Adding the windowing backend to a leaf crate's `[features]`
  table.** Don't. The leaf crate inherits from the consumer that
  selected the backend; adding `wayland`/`x11` features to crates that
  don't own the bevy app surface fragments the contract and creates
  the unification trap again.
- **Verifying with `target/release/<bin>` if it doesn't exist.** Build
  it first (`cargo build --release`) or fall back to `target/debug/`.
  Don't skip the check.

## Reference

- Parent skill: `plan-and-verify` (general two-mode wrapper).
- Planning skill: `multi-phase-plan-codex` (uses `multi-phase-plan` shape spec).
- Routing skill: `gpt-plan-routing`.
- Cargo feature unification:
  https://doc.rust-lang.org/cargo/reference/features.html#feature-unification
- Real-world example of this skill's output:
  `docs/src/planning/feature-flag-sweep/` in the chessbender/regicide
  workspace (six phases, AUDIT.md, COVERAGE-CHANGES.md, all six
  acceptance-criteria sets verified via the matrix above).
