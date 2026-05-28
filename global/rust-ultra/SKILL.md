---
name: rust-ultra
description: Master orchestrator that surveys a Rust crate/workspace, scores every housekeeping concern with weighted-grep + file-size heuristics, and drives the full rust-* skill arsenal in correctness→design→polish→dependencies order with convergence and a final verification gate. Use when the user asks to improve/harden/clean up/audit a whole Rust codebase, do a deep Rust pass, run all the rust skills, or "make this crate better".
argument-hint: "[path] [--sensitivity low|medium|high] [--plan-first] [--only <concerns>] [--skip <concerns>]"
---

# Rust Ultra — Whole-Codebase Improvement Orchestrator

Rust Ultra takes a whole crate or workspace from "works" to "polished" in one driven pass. It operates on two work layers:

1. **Deterministic host fixes** — `cargo fmt`, `cargo clippy --fix`, `cargo fix`, `cargo check`. These are mechanical, run by this orchestrator directly (no LLM judgment), and committed step by step.
2. **LLM concern skills** — the 21 sibling `rust-*` skills, each owning one housekeeping concern (dead code, unwrap audit, error architecture, trait design, …). This orchestrator decides which to run, in what order, and how deeply to plan, then invokes each via the Skill tool.

This skill is **full-auto**: it executes. Pass `--plan-first` to gate on human approval after the survey, before any concern edits.

It complements but does **not** replace the release skills (`rust-crate-quality-gates`, `rust-crate-release-prep`, the crates.io publish skills). For publishing, point the user there.

## How invocation works

Each concern below is a separate skill named `rust-<concern>` (e.g. `rust-dead-code`, `rust-error-architecture`). These are **user-level** skills installed under `~/.claude/skills/`. To run one, invoke it with the **Skill** tool — let it do its own work and report back. This orchestrator never reimplements a concern; it only decides **which** concerns run, in what **order**, with how much **planning**, and **loops until convergence**.

**Verify before invoking.** Not every `rust-<concern>` skill is guaranteed to be installed. Before invoking a concern via the Skill tool, confirm the skill is present (e.g. it appears in the available-skills list). If a concern is selected by the survey but its skill is **not installed**, **skip it and log it as deferred** ("skill not installed") rather than fabricating a Skill invocation. Never invent a skill name.

Default arguments: path = current crate/workspace root, `--sensitivity medium`, no `--plan-first`, no `--only`/`--skip`.

## Phase 0 — Deterministic baseline (always, no LLM)

Run the following in order. Commit each step with a conventional, atomic message. If a step fails irrecoverably, STOP and report — do not start concern work on a red tree.

1. `cargo fmt` — commit `style: cargo fmt`.
2. `cargo clippy --fix --allow-dirty --allow-staged --all-targets`, then verify with `cargo clippy --all-targets -- -D warnings`. If warnings remain, hand off to the `fix-clippy-errors` skill (invoke via the Skill tool) and re-verify. Commit `fix: auto-fix clippy lints`.
3. `cargo fmt` again (the clippy fixes may have churned formatting) — commit if it changed anything.
4. `cargo check --all-targets` — **must pass** before any concern work. On failure, try `cargo fix --allow-dirty --allow-staged --all-targets` then re-check; if still broken, fix the compile error yourself before proceeding.

If the crate is a Bevy / headless workspace that needs it, add `--no-default-features` to the commands above.

## Phase 1 — Survey & score

1. **Detect project shape.** Workspace vs single crate; per-crate `lib` / `bin`; presence of `unsafe`, an async runtime (`tokio` / `async-std`), `tracing` / `log`, a `[features]` table, Bevy, and a Nix flake. List **every** source file with its line count.
2. **Score each concern** that has a grep/filesize preflight: `score = Σ(occurrences × weight)` across non-test source. Exclude `target/`, `vendor/`, and test files. For the FileSize preflight (code-reorg): files **>500 lines** score **3** each, files **<30 lines** score **1** each.
3. **Apply `--sensitivity`** to each concern's threshold:
   - `low` ⇒ threshold ×3 (skip more — only strong signals run)
   - `medium` ⇒ threshold ×1 (default)
   - `high` ⇒ clamp threshold to **1** (run on the slightest signal)
   A concern **RUNS** when `score ≥ adjusted threshold`. Concerns whose preflight is **"none"** are opt-in: run them only when `--only` names them, or always when the user asks for release-readiness.
4. **Gate by project shape:**
   - `rust-api-guidelines` and `rust-doc-public-api` are most valuable for **lib** crates.
   - `rust-msrv` and `rust-feature-flags` are for **release-readiness**.
   - `rust-unsafe-soundness` runs **only if `unsafe` exists** (skip at 0 unsafe).
   - `rust-observability` runs only if `tracing` / `log` is present or the user requests it.
   - If a single crate is **large**, suggest running the `workspace-check` skill first (it decides whether the crate should become a Cargo workspace before deeper reorg).
5. **Honor `--only` / `--skip`.** Then produce a **scored, ordered run-list** (score vs adjusted threshold per concern, marked run/skip). If `--plan-first`, **print the run-list and STOP for approval** before any concern edits.

## Phase 2 — Staged execution

Run the relevant concerns in this fixed stage order: **Correctness → Design → Polish → Dependencies**. The routing table below is already in this order. **Within a stage, run highest-scoring first.**

For each concern:

- **Plan if `plan_worthy`.** First produce a brief plan. For the heaviest concerns — `rust-code-reorg`, `rust-type-safety`, `rust-trait-design` — think at **Opus / max-effort** depth. `rust-code-reorg` may split into **up to 4 parallel units** when **≥8 files** are affected (the "monumental" threshold). Then execute.
- **Respect `overlap_mode` when scoping:**
  - `Tiling` ⇒ also look at adjacent modules / compartments.
  - `Connectome` ⇒ consider the dependency graph and cross-module ripple.
  - `ScopeLocal` ⇒ no cross-boundary context needed.
  - `ToolDriven` ⇒ a cargo tool (e.g. `cargo-udeps`, `cargo-msrv`) drives it.
- **Invoke** the `rust-<concern>` skill via the Skill tool (after confirming it is installed — see "How invocation works") and let it do the work.
- **VERIFY before moving on:** `cargo fmt && cargo clippy --all-targets -- -D warnings && cargo check --all-targets && cargo test`. **Commit atomically per concern.** If verification fails, run the deterministic recovery (`cargo fix` → `cargo fmt`); if still broken, fix it before continuing. **Never leave the tree red.**

## Phase 3 — Convergence

After a full stage pass, **re-score** (repeat Phase 1 step 2). Then:

- Re-run any concern whose **Quantitative** metric is still **> 0**.
- Re-run any concern whose **Indicative / Qualitative** judgment reports remaining work.

**Stop when:** all Quantitative scores reach **0** AND no qualitative concern reports remaining work — OR after **max 3 iterations**. If you stop at the iteration cap, **log what was deferred and why** — never silently cap.

## Phase 4 — Final gate & report

Run the full verification spec:

- `cargo fmt --check`
- `cargo clippy --all-targets -- -D warnings`
- `cargo check --all-targets`
- `cargo test`
- `cargo audit` and `cargo deny check` — if available.

Then **report**:

- Which concerns **ran** (with final scores).
- Which were **skipped** — score vs threshold for each, plus any deferred for "skill not installed".
- **Commits** made.
- **Residual issues** and anything deferred.
- **Recommended follow-ups** (e.g. release skills for publishing).

## Concern routing table

| # | Skill | Stage | Preflight (score ≥ threshold ⇒ run) | overlap_mode | plan_worthy | eval |
|---|---|---|---|---|---|---|
| 1 | rust-dead-code | Correctness | grep `#[allow(dead_code)]`×3,`// unused`×2,`// TODO: remove`×2,`#[deprecated`×2 ≥ **4** | Tiling | no | Quantitative (0 ⇒ done) |
| 2 | rust-unwrap-audit | Correctness | grep `.unwrap()`×1,`.expect(`×1,`unwrap_or(`×1 ≥ **10** | ScopeLocal | no | Quantitative |
| 3 | rust-panic-audit | Correctness | grep `as usize/u32/u64/i64/u8/i32`×1 ≥ **6** (indexing hard to grep — scan manually) | ScopeLocal | no | Qualitative |
| 4 | rust-fail-fast | Correctness | grep `.unwrap()`×1,`panic!(`×3,`unimplemented!(`×3,`unreachable!(`×2,`todo!(`×2 ≥ **8** | ScopeLocal | no | Quantitative |
| 5 | rust-unsafe-soundness | Correctness | grep `unsafe `×3,`transmute`×5,`from_raw`×4,`MaybeUninit`×3,`::ptr::`×3,`get_unchecked`×3 ≥ **5** (skip if 0 unsafe) | ScopeLocal | yes | Indicative |
| 6 | rust-concurrency | Correctness | grep `.await`×1,`Mutex`×2,`RwLock`×2,`tokio::spawn`×2,`block_on`×3,`Arc<`×1 ≥ **8** | Connectome | yes | Qualitative |
| 7 | rust-security | Correctness | grep `unsafe `×3,`transmute`×5,`Command::new`×2,`from_raw`×4,`as *const`×3,`as *mut`×3,`std::ptr::`×3,`libc::`×2 ≥ **6** | ScopeLocal | yes | Indicative |
| 8 | rust-code-reorg | Design | FileSize: files >500 lines ×3, files <30 lines ×1 ≥ **3** | Connectome | yes (Opus plan @ max, multi-agent ≤4, monumental ≥8 files) | Quantitative |
| 9 | rust-type-safety | Design | none (qualitative — run on request / when primitive-obsessed) | Connectome | yes | Qualitative |
| 10 | rust-trait-design | Design | grep `dyn `×1,`Box<dyn`×2,`&dyn `×1 ≥ **8** | Tiling | yes | Indicative |
| 11 | rust-error-architecture | Design | grep `Box<dyn Error`×3,`Box<dyn std::error::Error`×3,`, String>`×2,`Err(format!`×2,`thiserror`×1 ≥ **5** | Connectome | yes | Qualitative |
| 12 | rust-performance | Design | grep `.clone()`×1,`.to_vec()`×2,`.to_string()`×1,`.collect()`×1,`&Vec<`×2,`&String`×2,`format!(`×1 ≥ **12** | ScopeLocal | no | Qualitative |
| 13 | rust-error-messages | Polish | grep `.context("`×1,`bail!("`×1,`eyre!("`×1,`anyhow!("`×1,`.map_err(`×1 ≥ **5** | ScopeLocal | no | Qualitative |
| 14 | rust-doc-public-api | Polish | grep `pub fn `×1,`pub struct `×1,`pub enum `×1,`pub trait `×2,`pub type `×1 ≥ **10** | ScopeLocal | no | Qualitative |
| 15 | rust-api-guidelines | Polish | (lib crates) grep `pub struct `×1,`pub enum `×1,`pub trait `×2,`pub fn get_`×2,`pub fn `×1 ≥ **6** | ScopeLocal | no | Qualitative |
| 16 | rust-test-gaps | Polish | grep `pub fn `×1,`pub async fn `×1 ≥ **5** | ScopeLocal | yes | Qualitative |
| 17 | rust-observability | Polish | grep `println!`×2,`eprintln!`×2,`dbg!`×3,`tracing::`×1,`log::`×1 ≥ **5** | ScopeLocal | no | Qualitative |
| 18 | rust-deps-unused | Dependencies | none (run on request; cargo-udeps signal) | ToolDriven | no | Qualitative |
| 19 | rust-feature-flags | Dependencies | grep `[features]`×3,`#[cfg(feature`×1,`optional = true`×2,`default = [`×2 ≥ **3** (skip if no [features]) | ToolDriven | no | Indicative |
| 20 | rust-msrv | Dependencies | none (run on release-readiness) | ToolDriven | no | Qualitative |
| 21 | rust-deps-adopt | Dependencies | none (run on request) | ScopeLocal | yes | Qualitative |

**eval semantics:**
- **Quantitative** — the preflight score is the metric; converged when it reaches 0.
- **Indicative** — the score indicates relevance, but the concern skill makes the final judgment on remaining work.
- **Qualitative** — convergence is the concern skill's own judgment; there is no numeric zero to chase.

## Notes

- This orchestrator only **EXECUTES** (full-auto). Pass `--plan-first` to gate on approval after Phase 1.
- It **complements**, does not replace, the release skills (`rust-crate-quality-gates`, `rust-crate-release-prep`, the crates.io publish skills) — point the user there for publishing.
- Keep commits **conventional and atomic**. Never revert another agent's or the user's work.
- If a selected concern's `rust-<concern>` skill is not installed, **skip and log it** — do not fabricate a Skill invocation.
