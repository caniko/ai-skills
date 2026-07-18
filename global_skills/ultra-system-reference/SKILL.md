---
name: ultra-system-reference
description: Shared non-invokable contract for ultra orchestrators covering profile routing, evidence ledgers, bounded delegation, convergence, and honest completion states.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Ultra System Reference

This is a shared reference, not a standalone user workflow. An ultra
orchestrator must load it before discovery and supply a domain foundation,
profile registry, profile procedures, stage order, and final technical gates.
When changing this system, preserve the invariants in
[failure-analysis.md](references/failure-analysis.md).

## Registry contract

Keep routing profile-granular. Every `[[profile]]` entry must declare a stable
ID, owning skill, stage, procedure path, evaluation mode, screening mode,
shape gate, threshold, and any deterministic detectors.

- Use `qualitative` when human or agent judgment is required. Set
  `screen = "always"`; scores may prioritize review but never suppress it.
- Use `indicative` when detectors establish applicability but cannot establish
  correctness. Require a disposition for every detected candidate.
- Use `quantitative` only when the detector fully defines the concern and a
  clean result is mechanically conclusive.
- Keep shape gates factual and machine-checkable. Record evidence for every
  `not-applicable` decision.
- Reject empty registries, duplicate IDs, missing procedures, unknown modes,
  malformed detectors, and unknown gates.

Validate before touching the target:

```sh
ultra-system-reference/scripts/ultra-system registry validate \
  --registry <ultra-skill>/references/concerns.toml
```

## Required run artifacts

Create `.ultra-out/` in the target root unless project policy supplies another
generated-artifact directory. Do not commit it unless the project explicitly
owns these reports.

- `survey.initial.json`: root, source revision, registry hash, exclusions,
  scores, gates, decisions, and matched evidence.
- `profile-ledger.json`: exactly one row per registered profile.
- `score-history.json`: initial and post-stage surveys tied to source state.
- `receipts/<stage>.json`: profiles covered, findings, changes, checks, and
  unresolved work for each stage or delegate.
- `final-validation.json`: final ledger validation and technical gate results.

Initialize the ledger from the deterministic survey. A green build or test
suite validates edits; it never substitutes for a profile receipt.

## Resource budget

The initial survey records logical CPUs, available memory, and conservative
worker recommendations. Treat these as upper bounds unless the user or the
repository supplies a stricter budget.

- Run at most one heavyweight build, test, evaluation, linker, or analyzer
  command at a time by default. Read-only analysis may use the recorded agent
  limit.
- Bound nested tool parallelism too. For Cargo, apply the recorded build-job
  cap with project-authoritative tooling or `CARGO_BUILD_JOBS`; for Nix, bound
  both jobs and cores when the wrapper allows it.
- Do not let every profile delegate run its own full gate. Validate narrowly
  per profile, then run one orchestrator-owned full gate per changed stage.
- Queue profile work when the sum of agent processes and child-process memory
  can exceed the budget. Lower concurrency after memory pressure, OOM kills,
  swapping, or unexplained process termination; record the adjustment.

Subagent count is not the same as execution capacity. Never spawn an
unbounded one-agent-per-profile fan-out.

## Profile ledger

Each row must contain:

`id | status | scope | evidence | findings | disposition | validation | residuals`

The ledger also records the registry hash and a source-state fingerprint. An
approved exclusion is a structured record with profile ID, approver, reason,
and impact; prose such as “out of scope” is not approval.

Use only these statuses:

- `reviewed-clean`: applicable scope was examined and has no open finding.
- `fixed-verified`: findings were fixed and relevant validation passed.
- `not-applicable`: the registry gate failed with recorded evidence.
- `deferred`: applicable work remains, with reason and owner.
- `blocked`: required evidence, authority, or tooling is unavailable.
- `unreviewed`: temporary initial state; never a terminal success state.

Every finding must end as fixed, disproven, accepted by the user or maintainer,
deferred, or blocked. Do not silently discard candidates because a lexical
score fell after moving or renaming code.

## Delegation contract

Subagents improve breadth but do not weaken the completion predicate. When
delegation is available, give each delegate disjoint profile IDs, target scope,
source revision, exclusions, procedure paths, and required receipt fields.
Require the receipt to identify every requested profile exactly once.

Keep the immediate blocker local. Delegate independent profiles in parallel,
then use an independent closer for large runs to compare the registry, ledger,
receipts, and final source revision. If subagents are unavailable, execute the
same contracts serially.

## Convergence and terminal states

Re-survey after every stage that changed source. Preserve score history and
revisit profiles affected by cross-stage changes. An iteration cap limits
automation, not disclosure.

Use terminal states precisely:

- `complete`: every profile is `reviewed-clean`, `fixed-verified`, or evidenced
  `not-applicable`; every finding is closed; final gates are fresh and green.
- `complete-with-approved-exclusions`: only user- or maintainer-approved
  exclusions remain and their impact is explicit.
- `incomplete`: deferred or unreviewed work remains.
- `blocked`: foundational evidence or authority is missing.
- `incomplete-convergence-cap`: the iteration cap was reached with open work.

Never use unqualified `complete` when any profile is deferred, blocked,
unreviewed, absent from the ledger, or covered only by stale validation.

Validate the final ledger:

```sh
ultra-system-reference/scripts/ultra-system ledger validate \
  --registry <ultra-skill>/references/concerns.toml \
  --ledger .ultra-out/profile-ledger.json \
  --root <target>
```

If the launcher cannot find Python 3.11 or newer, use the repository's
authoritative environment or `nix shell nixpkgs#python3`. Report the missing
interpreter and exact recovery command rather than replacing the validator.
