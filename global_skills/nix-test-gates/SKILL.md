---
name: nix-test-gates
description: Strengthen and validate Nix formatter, flake, host, Home Manager, package, activation, and CI checks. Use when Nix cleanup needs durable regression protection or focused evaluation gates.
---

# Nix Test Gates

Load [foundation.md](../nix-ultra/references/foundation.md) and
[test-gates.md](references/test-gates.md). Prefer cheap checks that explain
the exact violating file or value, then run the focused evals they protect.
