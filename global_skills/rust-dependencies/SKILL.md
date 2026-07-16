---
name: rust-dependencies
description: Audit and modernize Rust dependency policy, feature flags, MSRV, and breaking dependency upgrades. Use for dependency cleanup or migration work, or when rust-ultra routes dependency concerns here.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Rust Dependencies

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profile:

- [breaking-upgrade.md](references/breaking-upgrade.md)
- [adopt.md](references/adopt.md)
- [unused.md](references/unused.md)
- [features.md](references/features.md)
- [msrv.md](references/msrv.md)

Inspect manifests, lockfiles, source imports, build scripts, features, and
repository policy before changing the dependency graph. Keep upgrades
compatible where possible and report unavoidable semver or MSRV decisions.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
