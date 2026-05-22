---
name: workspace-check
description: Check whether a single-crate Rust project should be converted to a Cargo workspace. Applies file-count and LOC thresholds before performing analysis.
argument-hint: [project-dir]
---

# workspace-check — Cargo Workspace Readiness Assessment

You are analyzing a Rust project to determine whether it has grown large enough to benefit from being split into a Cargo workspace with multiple crates. This is a gated routine: if the project is below size thresholds, exit early.

## Phase 1: Locate the Project

Resolve inputs from `ARGUMENTS_JSON` first, then fall back to `argv` / `raw_args`.

If `ARGUMENTS_JSON.project_dir` is present, treat it as the path to the project root (the directory containing `Cargo.toml`).
Otherwise, if `argv[0]` / `raw_args` is non-empty, use that as the project root.

Otherwise, use the current working directory.

Read `Cargo.toml`. If it already contains `[workspace]`, report "This project is already a Cargo workspace" and stop. If `Cargo.toml` does not exist, report an error and stop.

---

## Phase 2: Threshold Gate

Collect these metrics from the `src/` directory:

1. **File count**: count all `.rs` files under `src/` recursively
2. **Lines of code**: count total lines across all `.rs` files under `src/` (use `wc -l` or equivalent; blank lines and comments count)
3. **Binary targets**: count `[[bin]]` entries in `Cargo.toml` plus the implicit binary if `src/main.rs` exists
4. **Largest file**: identify the single largest `.rs` file by line count

### Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| .rs file count | >= 20 | Below this, a single crate is manageable |
| Total LOC | >= 10,000 | Below this, compile times are unlikely to be a concern |

**Both thresholds must be met** to proceed. If either is below its threshold, output:

```
WORKSPACE CHECK: no action needed
  Files:    <N> .rs files (threshold: 20)
  LOC:      <N> lines (threshold: 10,000)
  Verdict:  Project is below workspace conversion thresholds.
```

Stop here. Do not proceed to Phase 3.

If both thresholds are met, print the metrics and continue.

---

## Phase 3: Structural Analysis

Perform these analyses on the codebase. For each, gather concrete evidence with file paths and line counts.

### 3.1 Module Size Inventory

List all top-level modules (files directly in `src/` and directories in `src/` with `mod.rs` or named modules). For each, report:
- File count (1 for single files, N for directories)
- Total LOC
- Whether it has submodules

Flag modules exceeding 2,000 LOC as "large" and modules exceeding 5,000 LOC as "oversized".

### 3.2 Binary Target Analysis

For each binary target (`[[bin]]` in Cargo.toml, or `src/main.rs`):
- Identify which modules it imports/uses
- Estimate what fraction of `src/lib.rs` (or the crate root) it actually needs
- Determine if binary targets share code or are largely independent

Binary targets that use disjoint subsets of the codebase are strong candidates for separate crates.

### 3.3 Dependency Direction Analysis

For each major module (>500 LOC), trace its `use crate::` imports to build a dependency graph:
- List which other modules it depends on
- Check for circular dependencies (A uses B and B uses A)
- Identify clusters of modules that are tightly coupled (many mutual imports) vs. loosely coupled (few or no shared imports)

Circular dependencies between would-be crates are blockers for splitting.

### 3.4 Feature Flag Analysis

Check `Cargo.toml` for `[features]`. For each feature:
- Identify which source files are gated behind `#[cfg(feature = "...")]`
- Determine if the feature-gated code is self-contained (could be its own crate)
- Note if features gate entire modules vs. scattered conditionals

### 3.5 Compile Time Assessment

Estimate compile time impact:
- Total LOC is a rough proxy (>20K LOC single-crate projects benefit significantly from splitting)
- Count proc-macro dependencies (these force serial compilation and benefit from isolation)
- Check if `build.rs` exists (build scripts block downstream compilation)
- Note if there are expensive generic instantiations or heavy macro usage

---

## Phase 4: Workspace Recommendation

Based on the analysis, produce one of three verdicts:

### Verdict: RECOMMENDED
Use when:
- There are clear, low-coupling boundaries between module clusters
- Multiple binary targets use disjoint code subsets
- LOC exceeds 20K and compile times would meaningfully improve
- Feature-gated code is self-contained enough to be a separate crate

### Verdict: CONSIDER
Use when:
- Some natural boundaries exist but circular dependencies need resolution first
- The project would benefit but the effort is high relative to the gain
- Only one dimension (e.g., large LOC but tightly coupled) supports splitting

### Verdict: NOT RECOMMENDED
Use when:
- Modules are tightly coupled with many circular dependencies
- The project is above thresholds but only marginally
- There is only one binary target and no natural crate boundaries
- The refactoring effort would exceed the compile-time and maintenance benefits

---

## Phase 5: Output Report

Print a structured markdown report:

```markdown
# Workspace Check Report

## Current Metrics
- **Files**: <N> .rs files
- **Lines of code**: <N>
- **Binary targets**: <N> (<list names>)
- **Largest module**: <name> (<N> LOC)

## Verdict: <RECOMMENDED | CONSIDER | NOT RECOMMENDED>

<1-3 sentence summary of the rationale>

## Module Size Map
| Module | Files | LOC | Classification |
|--------|-------|-----|----------------|
| ...    | ...   | ... | normal/large/oversized |

## Dependency Graph
<ASCII or bullet-list representation of module dependencies>
<Note any circular dependencies>

## Suggested Crate Split
<Only if verdict is RECOMMENDED or CONSIDER>

| Proposed Crate | Source Modules | Rationale |
|----------------|---------------|-----------|
| <name>-core    | src/types.rs, src/engine/ | Core types and logic, no I/O |
| <name>-cli     | src/main.rs, src/tui/ | CLI binary and TUI |
| ...            | ...           | ... |

### Migration Steps
1. <Ordered steps to perform the split>
2. ...

### Estimated Effort
- **Size**: small | medium | large | xlarge
- **Risk**: low | medium | high
- **Compile time improvement**: negligible | moderate | significant

## Circular Dependencies to Resolve
<List any circular deps that must be broken before splitting>

## Feature Flags
<Summary of feature analysis and whether any features should become crates>
```

Do NOT create or modify any project files. This skill is read-only analysis. The report is printed to stdout only.
