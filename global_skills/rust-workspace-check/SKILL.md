---
name: rust-workspace-check
description: Check whether a single-crate Rust project should be converted to a Cargo workspace. Applies file-count and LOC thresholds before performing analysis.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# rust-workspace-check — Cargo Workspace Readiness Assessment

Lineage: this is a narrowly scoped Rust research specialist built on the generic research pattern; use broader research routing when the project exceeds this skill's file-count and LOC gate.

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

## Phase 3 onward

After both thresholds pass, read [analysis.md](references/analysis.md) for the
structural analysis, verdict, and report contract. Do not create or modify
project files; print the read-only report.

## References

- Generic research base: [evidence-first-research](../evidence-first-research/SKILL.md) — rust-workspace-check is a narrowly scoped research specialist. For broader Rust-project investigation, use the base.
- Sibling research router: [research-routing](.skillnet/deps/research-routing/SKILL.md).

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
