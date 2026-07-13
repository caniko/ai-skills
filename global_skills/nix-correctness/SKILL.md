---
name: nix-correctness
description: Diagnose Nix evaluation failures and remove impurity that makes flakes or builds non-reproducible. Use for failed evals, bad option wiring, missing attributes, unpinned fetches, absolute paths, or eval-time filesystem coupling.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Correctness

Load [foundation.md](../nix-ultra/references/foundation.md), then the relevant
profile:

- [eval-failures.md](references/eval-failures.md)
- [store-purity.md](references/store-purity.md)

Fix the narrowest producer of the bad value or impurity. Do not hide failures
with broad `mkForce`, catch-all fallbacks, guessed hashes, or fabricated
artifacts. Validate the original failure and an adjacent affected output.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
