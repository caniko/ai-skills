---
name: nix-security
description: Audit NixOS and Home Manager secret handling, credential ownership, file modes, environment files, and service startup ordering. Use when secrets may enter the store, become world-readable, or race service startup.
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Nix Security

Load [foundation.md](../nix-ultra/references/foundation.md) and
[secrets.md](references/secrets.md). Treat missing encrypted/rekeyed data as a
blocker; never synthesize it. Inspect both declaration and consuming service.

## Solution Placement

Read `.skillnet/deps/solution-placement-policy/SKILL.md` for the shared ownership rule.
