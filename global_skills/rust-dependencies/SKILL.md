---
name: rust-dependencies
description: Audit and modernize Rust dependency policy, feature flags, MSRV, and breaking dependency upgrades. Use for dependency cleanup or migration work, or when rust-ultra routes dependency concerns here.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

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

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
