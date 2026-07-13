---
name: nix-code-health
description: Improve Nix file organization, dead-code hygiene, formatter-neutral style, and generated shell scripts without changing behavior. Use for Nix reorganization, stale module cleanup, idiomatic style, heredoc, hook, or activation-script work.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Nix Code Health

Load [foundation.md](../nix-ultra/references/foundation.md), then the
relevant profiles:

- [module-layout.md](references/module-layout.md)
- [dead-code.md](references/dead-code.md)
- [format-style.md](references/format-style.md)
- [shell-scripts.md](references/shell-scripts.md)

Keep generated hardware/disk files, secret migrations, and operational
comments stable unless the task explicitly includes them. Validate every
structural move with formatter and focused evaluation.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
