---
name: nix-flake-architecture
description: Modernize Nix flake outputs, input follows, overlays, packages, formatters, checks, dev shells, and NixOS or Home Manager builders. Use when flake output wiring is crowded, inputs drift, overlays are cache-hostile, or package architecture is unclear.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Flake Architecture

Load [foundation.md](../nix-ultra/references/foundation.md), then the
relevant profiles:

- [flake-outputs.md](references/flake-outputs.md)
- [inputs.md](references/inputs.md)
- [overlays-packages.md](references/overlays-packages.md)

Keep output names stable, preserve intentional cache-sensitive pins, and use
`--no-update-lock-file` for validation. Do not remove legacy outputs or merge
package sets without checking downstream consumers.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
