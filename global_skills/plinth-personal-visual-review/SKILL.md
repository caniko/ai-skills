---
name: plinth-personal-visual-review
description: Review canix personal Plinth/static sites through Plinth's Pkl-backed target registry, covering both Can and Dejana.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# Plinth Personal Visual Review

Use this for personal sites declared under `~/canix/canix`.

## Workflow

1. Work from the canix repository.
2. If personal-site data changed, regenerate the sidecar from `lib/PlinthPersonalSites.pkl` with the repo's Pkl sidecar workflow. Do not hand-copy generic defaults into Nix.
3. Validate Pkl and sidecar drift:
   ```bash
   nix build --no-link .#checks.x86_64-linux.pkl-validate
   nix build --no-link .#checks.x86_64-linux.pkl-nix-sidecars
   ```
4. Validate the Plinth-derived visual target registry:
   ```bash
   nix build --no-link .#checks.x86_64-linux.plinth-personal-visual-targets
   ```
5. Confirm both `can` and `dejana` are covered before treating the personal-site gate as complete.

## Review Standard

Use the existing visual-rubric guidance and Plinth's `plinth-site-beauty` preset. Missing target config, screenshots, reports, or Plinth helper exports are blockers. canix should declare only personal-site facts; route defaults, viewports, rubric preset, and production gate policy come from Plinth helpers.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
