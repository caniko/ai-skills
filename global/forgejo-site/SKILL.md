---
name: forgejo-site
description: Create a combined Codeberg Pages web presence for a Codeberg-hosted project using a Zola presentation website at the root and mdBook documentation under `/docs/`, with Nix flake packages and Forgejo Actions Pages publishing. Use when the user asks for a landing page plus documentation, a full project site, Zola plus mdBook, or the existing combined website/docs Codeberg Pages pattern.
---

# forgejo-site

## What this does

Set up a complete web presence for a Codeberg-hosted project:

1. **Presentation site** (`website/`) - a Zola static site with custom HTML/Sass templates.
2. **Documentation site** (`docs/`) - an mdBook site served under `/docs/`.
3. **Nix integration** - separate `website` and `docs` packages plus a combined `site` package.
4. **Pages deployment** - a Forgejo Actions workflow hosted by Codeberg, created or updated through the `forgejo-pages` skill.

The combined deployable output places the Zola site at `https://<user>.codeberg.page/<repo>/` and mdBook documentation at `https://<user>.codeberg.page/<repo>/docs/`.

## Required references

- [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md) for the `docs/` mdBook site, `book.toml`, documentation-content guidance, the `docs` derivation, and the docs verify recipe. Set `site-url = "/docs/"` (mdBook is nested under the Zola root). This skill adds the Zola `website` derivation and the combined `site` derivation on top.
- [../repo-pages/SKILL.md](../repo-pages/SKILL.md) (loaded transitively through `forgejo-pages`) for the build → publish model and the base-URL / subpath pitfall.

## Prerequisites

- The project must be a Nix flake with `flake.nix`.
- The project must be hosted on Codeberg.
- Determine Codeberg owner and repository from remotes or project metadata before asking the user.
- Gather or infer the project display name, one-line description, key landing-page features, license, author, and documentation sections.
- If documentation or landing-page content depends on missing source material, stop and report the missing source, required producer, regeneration command, and validation command.

## Workflow

### 1. Create the documentation site

Create or update `docs/` per [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md), with `site-url = "/docs/"` and `git-repository-url = "https://codeberg.org/<user>/<repo>"`.

### 2. Create the presentation site

Create `website/` with custom Zola templates:

```text
website/
  config.toml
  content/_index.md
  templates/
    base.html
    index.html
  sass/style.scss
  static/
```

Use this `config.toml` shape:

```toml
base_url = "https://<user>.codeberg.page/<repo>"
title = "<Project>"
description = "<description>"
default_language = "en"

compile_sass = true
build_search_index = false
minify_html = false
generate_feeds = false
hard_link_static = true

[markdown]
[markdown.highlighting]
theme = "nord"
```

`hard_link_static = true` is required for Nix sandbox compatibility.

The base template must include:

- Project name linking to the home page.
- Documentation link pointing to `{{ config.base_url }}/docs/`.
- Source link pointing to the Codeberg repository.

For `_index.md`, use Zola's `section` variable rather than `page`.

### 3. Update `flake.nix`

Take the `docs` mdBook derivation from [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md). Add the Zola `website` derivation and override `site` to combine the two:

```nix
website = pkgs.stdenv.mkDerivation {
  pname = "<project>-website";
  version = "0.1.0";
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.maybeMissing ./website;
  };
  nativeBuildInputs = [pkgs.zola];
  phases = ["buildPhase" "installPhase"];
  buildPhase = ''
    cp -r --no-preserve=mode $src/website site
    cd site
    zola build
  '';
  installPhase = ''
    cp -r public $out
  '';
};

# docs = ... (mdBook derivation from mdbook-docs)

site = pkgs.runCommand "<project>-site" {} ''
  mkdir -p $out
  cp -r ${website}/* $out/
  mkdir -p $out/docs
  cp -r ${docs}/* $out/docs/
'';
```

Expose `website`, `docs`, and `site` in `packages`. Add `pkgs.zola` and `pkgs.mdbook` to the dev shell.

If the flake is already large or this update makes `flake.nix` hard to review, modularize using the shared routine at [../simit-project-init/references/flake-modularization.md](../simit-project-init/references/flake-modularization.md). Keep `website`, `docs`, and `site` output names stable.

### 4. Update ignored artifacts

Ignore generated output:

```gitignore
docs/book/
website/public/
```

### 5. Add or update Pages deployment

Use the `forgejo-pages` skill for Forgejo Actions hosted by Codeberg (it loads `repo-pages` for the build → publish model and the base-URL / subpath pitfall). Do not duplicate its workflow details here.

Before adding or updating CI, ensure:

- `nix build .#site` builds the combined deployable output.
- The deployable root contains the Zola presentation site.
- The deployable output contains mdBook documentation under `/docs/`.
- `website/config.toml` `base_url` matches the final Pages URL.

### 6. Verify

Verify the docs build per [../mdbook-docs/SKILL.md](../mdbook-docs/SKILL.md), then additionally:

```sh
nix build .#website
nix build .#site
```

For local development, `cd website && zola serve` (docs serve per mdbook-docs).

Clean generated artifacts after verification if they are created in the worktree:

```sh
rm -rf docs/book website/public
```

## Reference implementation

The plinth project at `~/canix/Projects/solo/plinth` has a working implementation of this pattern with Zola landing page, mdBook documentation, rustdoc API reference, and a combined deployable output.
