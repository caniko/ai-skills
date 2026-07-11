# Workspace Structural Analysis

Read only after both threshold gates pass. Gather file paths and line counts for
each result.

## Module and target map

List top-level modules, their file count/LOC/submodules, and flag modules over
2,000 LOC (large) or 5,000 LOC (oversized). For each binary, identify imported
modules, shared versus disjoint code, and likely crate boundaries.

## Coupling and features

For major modules over 500 LOC, trace `use crate::` imports, circular
dependencies, and tightly/loosely coupled clusters. Inspect `[features]` and
`#[cfg(feature = "…") ]` placement; self-contained feature clusters may become
crates, scattered gates usually should not.

## Compile-time evidence

Record total LOC, proc-macro dependencies, `build.rs`, expensive generic
instantiations, and macro-heavy modules. Treat LOC as a proxy, not proof.

## Verdict

- `RECOMMENDED`: clear low-coupling boundaries, disjoint binaries, or
  self-contained features with meaningful compile-time benefit.
- `CONSIDER`: some boundaries exist but coupling or effort is material.
- `NOT RECOMMENDED`: tightly coupled modules, marginal thresholds, one binary
  with no boundaries, or effort greater than maintenance benefit.

Report metrics, verdict/rationale, module map, dependency graph, circular
dependencies, feature assessment, and (for the first two verdicts) proposed
crates plus ordered migration steps and effort/risk. This skill remains
read-only; print the report rather than editing the project.
