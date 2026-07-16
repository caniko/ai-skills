---
name: nix-security
description: Audit NixOS and Home Manager secret handling, credential ownership, file modes, environment files, and service startup ordering. Use when secrets may enter the store, become world-readable, or race service startup.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Nix Security

Load [foundation.md](../nix-ultra/references/foundation.md) and
[secrets.md](references/secrets.md). Treat missing encrypted/rekeyed data as a
blocker; never synthesize it. Inspect both declaration and consuming service.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
