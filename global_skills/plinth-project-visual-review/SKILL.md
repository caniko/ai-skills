---
name: plinth-project-visual-review
description: Review Plinth project sites that use website/plinth-project.toml with plinth-project check/build/dev/audit and visual-rubric reports.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Plinth Project Visual Review

Use this for project sites with `website/plinth-project.toml`.

## Workflow

1. Validate the config:
   ```bash
   nix develop . -c plinth-project check --config website/plinth-project.toml --json
   ```
2. Build or serve the latest local output:
   ```bash
   nix build .#site --no-link
   nix develop . -c plinth-project dev --config website/plinth-project.toml --port 0
   ```
3. Run the full-site visual gate:
   ```bash
   nix develop . -c plinth-project audit site --config website/plinth-project.toml
   ```
4. Inspect the JSON report and screenshot paths printed by the audit command. Treat missing screenshots, missing report JSON, browser failures, or visual-rubric errors as blockers.

## Review Standard

Use the existing visual-rubric guidance and the `plinth-site-beauty` preset. Do not duplicate or soften the rubric locally. Fail/error verdicts block production unless the user explicitly asks for exploratory review with `--no-fail-on-rubric`.

## Notes

- Prefer explicit `--route` only when the site intentionally needs non-rendered routes; default coverage should be every rendered Plinth page.
- Use `--fake-ai` only for plumbing tests, never for a real production review.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
