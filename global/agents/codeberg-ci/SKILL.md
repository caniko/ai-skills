---
name: codeberg-ci
description: Add Forgejo Actions hosted by Codeberg for Codeberg Pages deployment. Use when a user asks to add Codeberg CI, Forgejo Actions, Codeberg Pages publishing, Pages deployment, or static-site publishing for a Codeberg-hosted repository.
---

# codeberg-ci

## What this does

Adds a Forgejo Actions workflow that builds a static site and publishes it to Codeberg Pages using `https://codeberg.org/git-pages/action@v2`.

Use the term **Forgejo Actions hosted by Codeberg**. Avoid "Codeberg Actions"; Codeberg's hosted CI service is Forgejo Actions.

## Preconditions

- The repository is public and available under a free/libre license.
- Forgejo Actions is enabled in the repository settings: **Settings → Units → Enable Actions**, then save.
- The site build output is available from a local build command.
- The target site uses the `codeberg.page` domain. Custom domains still require Codeberg's legacy Pages workflow until the new git-pages method supports them.

## Defaults

- Workflow path: `.forgejo/workflows/pages.yaml`
- Runner: `codeberg-small`
- Trigger: pushes to `main`
- Checkout action: `actions/checkout@v4`
- Nix build command: `nix build .#site`
- Deploy action: `https://codeberg.org/git-pages/action@v2`
- Deploy source: `result/`
- Site URL: `https://${{ forge.repository_owner }}.codeberg.page/<repo>/`
- Token: `${{ forge.token }}`

Use `master` instead of `main` only when the target repository actually uses `master`.

## Hosted Runner Limits

Codeberg hosted Forgejo Actions runners are constrained. Keep jobs minimal, avoid matrix builds unless there is a strong reason, and do not assume a Docker daemon is available.

- `codeberg-tiny`: 1 CPU, 2 GB RAM, 2 min. Use for static checks, linters, and very lightweight non-Nix jobs.
- `codeberg-small`: 2 CPU, 4 GB RAM, 5 min. Use for Rust crate jobs that compile, test, run clippy, or package.
- `codeberg-medium`: 4 CPU, 8 GB RAM, 10 min. Use for larger docs, site, or Nix builds that exceed `codeberg-small`.

Append `-lazy` only when delayed scheduling is acceptable, for example `codeberg-small-lazy`.

Default guidance:

- Static or lint-only non-Nix jobs: `codeberg-tiny`.
- Rust crate jobs with compilation: `codeberg-small`.
- Larger docs, site, or Nix builds: `codeberg-medium` or `codeberg-small-lazy`.

Prefer language/runtime images over Nix for ordinary crate CI and crates.io publishing. For Rust crates, use an Alpine Rust image such as `rust:alpine` or `rust:<rust-version>-alpine` and run Cargo directly. Do not select Debian-based images. Do not select Nix just because `flake.nix` exists.

Use flakes only when the workflow intentionally consumes flake outputs, such as cross-platform binary builds, release artifacts, or a site/docs build that has no lighter maintained image-based path.

## Workflow

1. Confirm the repository name from the Codeberg remote or project metadata.
2. Confirm Forgejo Actions is enabled with `berg --owner-repo <owner>/<repo> repo info --output-mode json`; expect `has_actions: true`.
3. If Actions is disabled, the repository owner must enable **Settings → Units → Enable Actions** in the Codeberg UI. `berg` 0.5.5 can read `has_actions` but does not expose an Actions enable command.
4. Confirm the build command and output directory. For Nix flake sites, default to `nix build .#site` and `result/`.
5. Select the smallest runner that fits the expected compile/build time. For Rust crate jobs with tests and clippy, start with `codeberg-small`. For docs-only jobs with prebuilt tools, consider `codeberg-tiny`. For Nix builds, start with `codeberg-small` and use `codeberg-medium` or `codeberg-small-lazy` if local evidence suggests more headroom is required.
6. Create `.forgejo/workflows/pages.yaml`.
7. Replace `<repo>` in the `site` URL with the actual repository name.
8. Validate the build command locally when feasible.

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

## Notes

- Workflows belong in `.forgejo/workflows/`; Forgejo may also look in `.github/workflows/`, but prefer the native path.
- `codeberg-small` is the default because site builds with Nix often need more than the tiny runner. Use `codeberg-tiny` only for very lightweight non-Nix builds.
- Limit deployment to the default branch so draft branches do not publish unfinished content.
- The `site` input must match the final public Pages URL. For a repository named `pages`, the repository path segment may be omitted if publishing to `https://<user>.codeberg.page/`.
- `berg --owner-repo <owner>/<repo> repo info --output-mode json` can verify `has_actions`, but `berg` 0.5.5 does not provide an Actions enable command.
