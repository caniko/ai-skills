---
name: nix-correctness
description: Diagnose Nix evaluation failures and remove impurity that makes flakes or builds non-reproducible. Use for failed evals, bad option wiring, missing attributes, unpinned fetches, absolute paths, or eval-time filesystem coupling.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Nix Correctness

Load [foundation.md](../nix-ultra/references/foundation.md), then the relevant
profile:

- [eval-failures.md](references/eval-failures.md)
- [store-purity.md](references/store-purity.md)

Fix the narrowest producer of the bad value or impurity. Do not hide failures
with broad `mkForce`, catch-all fallbacks, guessed hashes, or fabricated
artifacts. Validate the original failure and an adjacent affected output.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
