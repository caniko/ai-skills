# Retirement Checklist

Use this checklist at the start of every run.

## Inventory

- Find the published-doc navigation file such as `docs/src/SUMMARY.md`, sidebar config, or site router.
- List the planning files currently exposed to readers.
- List the stable docs that can absorb durable guidance.

## Classification

- Mark execution-only content for removal.
- Mark durable behavior, invariants, feature-flag behavior, release checks, and maintainer guidance for preservation.
- Mark any version, release, CI, or API claim that must be re-verified from source artifacts.

## Verification Targets

- Version and install snippets: verify against `Cargo.toml`, package manifests, and actual Git tags.
- Feature flags and optional dependencies: verify against build metadata and code.
- API names and parsing examples: verify against the current implementation and tests.
- Compatibility or semantic rules: verify against the current code and tests, not the retired plan.
- Release commands and packaged files: verify against workflows, manifests, and package metadata.

## Retirement Edits

- Update stable docs first.
- Remove planning entries from navigation.
- Delete obsolete planning files after their durable content has been preserved.
- Remove empty planning directories when practical.

## Final Checks

- Search for stale references to the retired planning section.
- Inspect the diff for accidental loss of durable knowledge.
- Promote only a novel, reusable rule to `references/retirement-rules.md` when
  the skill repository is explicitly in scope; do not append a task log.
