---
name: forgejo-docs
description: Create or update a docs-only mdBook site for a Codeberg-hosted project, integrate it with a Nix flake, and publish it to Codeberg Pages through Forgejo Actions hosted by Codeberg. Use when the user asks for Codeberg documentation, mdBook docs, docs-only Pages publishing, or to remove a separate landing website while keeping documentation deployed.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# forgejo-docs

## What this does

This is the Codeberg/Forgejo-hosted wrapper around the generic mdBook docs workflow.

It keeps the docs work in [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md) and adds the host-specific wiring needed for Codeberg Pages published through Forgejo Actions hosted by Codeberg.

## Required references

Load these two skills together:

- [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md) for the actual `docs/`, `book.toml`, flake, ignore-file, and verification workflow.
- [../forgejo-pages/SKILL.md](../forgejo-pages/SKILL.md) for `.forgejo/workflows/pages.yaml`.

## Host-specific inputs

Determine the Codeberg owner and repository from remotes or project metadata before editing.

Set these mdBook fields as follows:

- `git-repository-url = "https://codeberg.org/<owner>/<repo>"`
- `site-url = "/<repo>/"` for normal project Pages deployments
- `site-url = "/"` only when the repository itself is the `pages` repository and publishes at `https://<owner>.codeberg.page/`

If documentation content would need to be invented from missing source material, stop and report the missing source, required producer, regeneration command, and validation command.

## Workflow

1. Run the generic docs workflow from [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md).
2. Apply the Codeberg-specific `site-url` and `git-repository-url` values above.
3. Use [../forgejo-pages/SKILL.md](../forgejo-pages/SKILL.md) for Pages deployment wiring.
4. Verify the local docs build per mdbook-docs before adding CI.
5. For custom domain wiring (`<name>.example.com`), use `codeberg-pages-dns` after the initial Pages deploy.

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
