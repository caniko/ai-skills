---
name: plinth-personal-visual-review
description: Review canix personal Plinth/static sites through Plinth's Pkl-backed target registry, covering both Can and Dejana.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

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

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
