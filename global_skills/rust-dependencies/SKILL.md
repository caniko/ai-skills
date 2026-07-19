---
name: rust-dependencies
description: Audit and modernize Rust dependency policy, feature flags, MSRV, and breaking dependency upgrades. Use for dependency cleanup or migration work, or when rust-ultra routes dependency concerns here.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

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
compatible where possible in focused or compatibility mode. In Rust-ultra
modernize mode, take justified breaking upgrades, adapt all in-repository APIs
and features, and report downstream/MSRV migration decisions. Do not churn a
dependency solely to maximize version numbers.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
