---
name: nix-test-gates
description: Strengthen and validate Nix formatter, flake, host, Home Manager, package, activation, and CI checks. Use when Nix cleanup needs durable regression protection or focused evaluation gates.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Nix Test Gates

Load [foundation.md](../nix-ultra/references/foundation.md) and
[test-gates.md](references/test-gates.md). Prefer cheap checks that explain
the exact violating file or value, then run the focused evals they protect.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
