---
name: codeberg-docs
description: Create or update a docs-only mdBook site for a Codeberg-hosted project, integrate it with a Nix flake, and publish it to Codeberg Pages through Forgejo Actions. Use when the user asks for Codeberg documentation, mdBook docs, docs-only Pages publishing, or to remove a separate landing website while keeping documentation deployed.
---

# codeberg-docs

## What this does

Set up project documentation as the deployable Codeberg Pages site:

1. **Documentation** (`docs/`) - an mdBook site with sidebar navigation, search, and chapter hierarchy.
2. **Nix integration** - a `docs` package and a `site` package that produce the same deployable output.
3. **Pages deployment** - a Forgejo Actions workflow hosted by Codeberg, created or updated through the `codeberg-ci` skill.

The deployed site is docs-only. Serve mdBook at the Pages root, for example `https://<user>.codeberg.page/<repo>/`, not below `/docs/`.

## Prerequisites

- The project must be a Nix flake with `flake.nix`.
- The project must be hosted on Codeberg.
- Determine the Codeberg owner and repository from remotes or project metadata before asking the user.
- Gather or infer the project display name, one-line description, license, author, and documentation sections.
- If documentation content must be generated from missing source material, stop and report the missing source, required producer, regeneration command, and validation command.

## Documentation guidance

Read `references/documentation.md` when creating or reorganizing mdBook content. It is the shared, non-invocable guide for documentation structure, `SUMMARY.md`, page conventions, links, and quality expectations.

## Workflow

### 1. Create or update `docs/`

Use this structure:

```text
docs/
  book.toml
  src/
    SUMMARY.md
    introduction.md
    getting-started/
      installation.md
      quick-start.md
```

Use this `book.toml` shape for docs published at the Pages root:

```toml
[book]
title = "<Project> Documentation"
authors = ["<Author>"]
language = "en"
src = "src"

[build]
build-dir = "book"

[output.html]
site-url = "/<repo>/"
default-theme = "coal"
preferred-dark-theme = "coal"
git-repository-url = "https://codeberg.org/<user>/<repo>"
```

For a repository named `pages`, use `site-url = "/"` if it publishes at `https://<user>.codeberg.page/`.

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

Expose `docs` and `site` in `packages`. Add `pkgs.mdbook` to the dev shell and avoid `pkgs.zola` unless another part of the repository still needs it.

If the flake is already large or this update makes `flake.nix` hard to review, modularize using the shared routine at `/home/can/.codex/skills/simit-project-init/references/flake-modularization.md`. Keep `docs` and `site` output names stable.

### 3. Update ignored artifacts

Ignore mdBook output:

```gitignore
docs/book/
```

Remove stale website build artifacts when deleting a former Zola site.

### 4. Add or update Pages deployment

Use the `codeberg-ci` skill for Forgejo Actions hosted by Codeberg. Do not duplicate its workflow details here.

Before adding or updating CI, ensure:

- `nix build .#site` builds the deployable docs output.
- The deployable output root contains mdBook files such as `index.html`, `book.js`, and `searchindex.js`.
- The workflow publishes `result/` to `https://<user>.codeberg.page/<repo>/` or the repository's actual Pages URL.

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
