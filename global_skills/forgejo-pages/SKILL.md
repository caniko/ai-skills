---
name: forgejo-pages
description: Add Forgejo Actions hosted by Codeberg for Codeberg Pages deployment. Use when a user asks to add Forgejo Pages CI, Codeberg Pages publishing, Pages deployment, or static-site publishing for a Codeberg-hosted repository.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# forgejo-pages

## What this does

Adds a Forgejo Actions workflow that builds a static site and publishes it to Codeberg Pages using `https://codeberg.org/git-pages/action@v2`.

Use the term **Forgejo Actions hosted by Codeberg**. Avoid "Codeberg Actions"; Codeberg's hosted CI service is Forgejo Actions.

This skill is for Codeberg's shared hosted runners. If the repository should run on our self-hosted runner runner, or the request is for Rust crate CI/release readiness rather than Pages publishing, use [../forgejo-runner-ci/SKILL.md](../forgejo-runner-ci/SKILL.md) and the Rust crate release CI skill instead.

## Shared Pages model

This skill layers Codeberg/Forgejo specifics on top of the generic repository-Pages model defined in [repo-pages](../repo-pages/SKILL.md). Read that skill for the build → publish flow, branch gating rationale, build-output / publish-directory matching, and the base-URL / subpath pitfall that causes most post-deploy 404s. Everything below is the Codeberg/Forgejo-specific layer.

## Codeberg-specific preconditions

In addition to the generic preconditions in `repo-pages`:

- The repository is public and available under a free/libre license (Codeberg Pages eligibility).
- Forgejo Actions is enabled in the repository settings: **Settings → Units → Enable Actions**, then save.
- The target site uses either `codeberg.page` or a verified custom domain. For
  custom domains, use git-pages with `server: codeberg.page` and ensure the
  deployment-mode-specific DNS authorization is present; do not add a legacy
  `.domains` file unless the site is explicitly retained on Pages Server v2.

## Defaults

- Workflow path: `.forgejo/workflows/pages.yaml`
- Runner: `codeberg-small`
- Trigger: pushes to `main`
- Checkout action: `actions/checkout@v4`
- Nix build command: `nix build .#site`
- Deploy action: `https://codeberg.org/git-pages/action@v2`
- Deploy source: `result/`
- Site URL: `https://${{ forge.repository_owner }}.codeberg.page/<repo>/`
- Custom site URL: `https://<custom-domain>/` with `server: codeberg.page`
- Token: `${{ forge.token }}`

Use `master` instead of `main` only when the target repository actually uses `master`.

## Hosted runner limits

Codeberg hosted Forgejo Actions runners are constrained. Keep jobs minimal, avoid matrix builds unless there is a strong reason, and do not assume a Docker daemon is available.

- `codeberg-tiny`: 1 CPU, 2 GB RAM, 2 min. Use for static checks, linters, and very lightweight non-Nix jobs.
- `codeberg-small`: 2 CPU, 4 GB RAM, 5 min. Use for ordinary Pages builds that exceed `codeberg-tiny`.
- `codeberg-medium`: 4 CPU, 8 GB RAM, 10 min. Use for larger docs, site, or Nix builds that exceed `codeberg-small`.

Append `-lazy` only when delayed scheduling is acceptable, for example `codeberg-small-lazy`.

Default guidance:

- Static or lint-only non-Nix jobs: `codeberg-tiny`.
- Larger docs, site, or Nix builds: `codeberg-medium` or `codeberg-small-lazy`.

Use flakes only when the workflow intentionally consumes flake outputs, such as a site/docs build that has no lighter maintained image-based path. Do not use this Pages skill as the source of truth for Rust crate CI; runner Rust jobs use Debian Rust containers and the action runtime described in the runner CI skills.

## Workflow

1. Confirm the repository name from the Codeberg remote or project metadata.
2. Confirm Forgejo Actions is enabled with local tooling. Use `fj repo view <owner>/<repo>` plus the Codeberg repository UI/API to confirm the Actions unit.
3. If Actions is disabled, the repository owner must enable **Settings → Units → Enable Actions** in the Codeberg UI. Local tools may be able to read the setting, but do not assume they can enable it.
4. Confirm the build command and output directory. For Nix flake sites, default to `nix build .#site` and `result/`.
5. Select the smallest runner that fits the expected build time. For docs-only jobs with prebuilt tools, consider `codeberg-tiny`. For Nix site builds, start with `codeberg-small` and use `codeberg-medium` or `codeberg-small-lazy` if local evidence suggests more headroom is required.
6. For a custom domain, verify the required CNAME/TXT authorization before editing the workflow; `codeberg-pages-dns` owns the DNS model.
7. Create `.forgejo/workflows/pages.yaml`.
8. Replace `<repo>` or `<custom-domain>` in the `site` input with the actual public URL.
9. Validate the build command locally when feasible.

## Default template

```yaml
name: Publish Pages

on:
  push:
    branches: [main]

jobs:
  publish:
    runs-on: codeberg-small
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install Nix
        uses: https://github.com/cachix/install-nix-action@v31

      - name: Build site
        run: nix build .#site

      - name: Publish to Codeberg Pages
        uses: https://codeberg.org/git-pages/action@v2
        with:
          site: "https://${{ forge.repository_owner }}.codeberg.page/<repo>/"
          token: ${{ forge.token }}
          source: result/
```

For a custom domain, keep the same action and source but add the git-pages
server selector:

```yaml
        uses: https://codeberg.org/git-pages/action@v2
        with:
          site: https://<custom-domain>/
          server: codeberg.page
          token: ${{ forge.token }}
          source: result/
```

## Notes

- Workflows belong in `.forgejo/workflows/`; Forgejo may also look in `.github/workflows/`, but prefer the native path.
- The `site` input must match the final public Pages URL. For a repository named `pages`, the repository path segment may be omitted if publishing to `https://<user>.codeberg.page/`.

## Solution Placement

For durable solutions, prefer the highest suitable owner: generic upstream → Fleetix → standalone flake → canix-toolbelt → canix. Keep consumer policy with the consumer and record why higher layers do not fit.
