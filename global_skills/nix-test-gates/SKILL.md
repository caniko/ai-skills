---
name: nix-test-gates
description: Strengthen and validate Nix formatter, flake, host, Home Manager, package, activation, and CI checks. Use when Nix cleanup needs durable regression protection or focused evaluation gates.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Nix Test Gates

Load [foundation.md](../nix-ultra/references/foundation.md) and
[test-gates.md](references/test-gates.md). Prefer cheap checks that explain
the exact violating file or value, then run the focused evals they protect.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
