---
name: mdbook-docs
description: Create or update a docs-only mdBook site, integrate it with a Nix flake as `docs` and `site` outputs, and leave deployment wiring to a host-specific CI skill such as Forgejo Pages or GitLab Pages. Use when the user asks for mdBook docs, a docs-only site, Nix-flake docs packaging, or wants documentation prepared before CI/Pages wiring.
---

**Cross-repository work:** As soon as work is known to span more than one Git repository, invoke `$graphify` before further discovery, planning, or edits. Query a relevant existing graph first; build or update a merged graph if none exists, it is stale, or it does not cover every repository in scope. Reuse a current graph already produced for the same repository set.

# mdbook-docs

## What this does

Set up project documentation as a deployable docs-only mdBook site:

1. **Documentation** (`docs/`) - an mdBook site with sidebar navigation, search, and chapter hierarchy.
2. **Nix integration** - a `docs` package and a `site` package that produce the same deployable output.
3. **CI hand-off** - leaves deployment wiring to a host-specific Pages skill.

## Prerequisites

- The project must be a Nix flake with `flake.nix`.
- Gather or infer the project display name, one-line description, license, author, and documentation sections.
- Determine the final `site-url` and `git-repository-url` from the target hosting platform before editing `docs/book.toml`.
- If documentation content must be generated from missing source material, stop and report the missing source, required producer, regeneration command, and validation command.

## Documentation guidance

Read `references/documentation.md` when creating or reorganizing mdBook content. It is the shared, non-invocable guide for documentation structure, `SUMMARY.md`, page conventions, links, and quality expectations.

## Workflow

### 1. Create or update `docs/`

For the `docs/` layout, `SUMMARY.md`, and page conventions, follow `references/documentation.md`.

Use this `book.toml` shape:

```toml
[book]
title = "<Project> Documentation"
authors = ["<Author>"]
language = "en"
src = "src"

[build]
build-dir = "book"

[output.html]
site-url = "<site-url>"
default-theme = "coal"
preferred-dark-theme = "coal"
git-repository-url = "<repo-url>"
```

Common `site-url` patterns:

- `"/"` for root-hosted deployments
- `"/<repo>/"` for project-scoped Pages deployments
- `"/docs/"` when the mdBook is nested under a larger site

### 2. Update `flake.nix`

Add or keep an mdBook derivation and make `site` resolve to the docs output:

```nix
docs = pkgs.stdenv.mkDerivation {
  pname = "<project>-docs";
  version = "0.1.0";
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.maybeMissing ./docs;
  };
  nativeBuildInputs = [pkgs.mdbook];
  phases = ["buildPhase" "installPhase"];
  buildPhase = ''
    cp -r --no-preserve=mode $src/docs docs
    mdbook build docs
  '';
  installPhase = ''
    cp -r docs/book $out
  '';
};

site = docs;
```

Expose `docs` and `site` in `packages`. Add `pkgs.mdbook` to the dev shell.

If the flake is already large or this update makes `flake.nix` hard to review, modularize using the shared routine at [../simit-project-init-common/references/flake-modularization.md](../simit-project-init-common/references/flake-modularization.md). Keep `docs` and `site` output names stable.

### 3. Update ignored artifacts

Ignore mdBook output:

```gitignore
docs/book/
```

Remove stale generated site artifacts when deleting a former landing site.

### 4. Hand off deployment wiring

Use a host-specific Pages skill instead of duplicating CI instructions here:

- [../forgejo-pages/SKILL.md](../forgejo-pages/SKILL.md) for Codeberg Pages via Forgejo Actions hosted by Codeberg
- [../gitlab-pages/SKILL.md](../gitlab-pages/SKILL.md) for GitLab Pages

Before adding CI, ensure:

- `nix build .#site` builds the deployable docs output
- the deployable output root contains mdBook files such as `index.html`, `book.js`, and `searchindex.js`
- the chosen Pages URL matches `docs/book.toml` `site-url`

### 5. Verify

Run:

```sh
nix build .#docs
nix build .#site
nix flake check
```

For local development:

```sh
cd docs && mdbook serve
```

Clean generated artifacts after verification if they are created in the worktree:

```sh
rm -rf docs/book
```

## Solution Placement

When this skill recommends or implements a durable solution, evaluate owners in this order and stop at the first suitable layer:

1. Generic upstream.
2. Fleetix.
3. A new standalone flake, only when the scope is cohesive and no existing owner fits.
4. canix-toolbelt.
5. canix.

Keep consumer-specific data and policy with the consumer even when mechanics move upstream. Before choosing a lower layer, record why each higher-priority owner does not fit.
