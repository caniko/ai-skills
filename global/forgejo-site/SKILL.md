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

## Prerequisites

- The project must be a Nix flake with `flake.nix`.
- The project must be hosted on Codeberg.
- Determine Codeberg owner and repository from remotes or project metadata before asking the user.
- Gather or infer the project display name, one-line description, key landing-page features, license, author, and documentation sections.
- If documentation or landing-page content depends on missing source material, stop and report the missing source, required producer, regeneration command, and validation command.

## Documentation guidance

Read `/home/can/.agents/skills/mdbook-docs/references/documentation.md` when creating or reorganizing mdBook content. It is the shared, non-invocable guide for documentation structure, `SUMMARY.md`, page conventions, links, and quality expectations.

## Workflow

### 1. Create the documentation site

Create or update `docs/` as an mdBook site. Use this `book.toml` shape for docs served under `/docs/`:

```toml
[book]
title = "<Project> Documentation"
authors = ["<Author>"]
language = "en"
src = "src"

[build]
build-dir = "book"

[output.html]
site-url = "/docs/"
default-theme = "coal"
preferred-dark-theme = "coal"
git-repository-url = "https://codeberg.org/<user>/<repo>"
```

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

Add derivations for `website`, `docs`, and combined `site`:

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

site = pkgs.runCommand "<project>-site" {} ''
  mkdir -p $out
  cp -r ${website}/* $out/
  mkdir -p $out/docs
  cp -r ${docs}/* $out/docs/
'';
```

Expose `website`, `docs`, and `site` in `packages`. Add `pkgs.zola` and `pkgs.mdbook` to the dev shell.

If the flake is already large or this update makes `flake.nix` hard to review, modularize using the shared routine at `/home/can/.codex/skills/simit-project-init/references/flake-modularization.md`. Keep `website`, `docs`, and `site` output names stable.

### 4. Update ignored artifacts

Ignore generated output:

```gitignore
docs/book/
website/public/
```

### 5. Add or update Pages deployment

Use the `forgejo-pages` skill for Forgejo Actions hosted by Codeberg. Do not duplicate its workflow details here.

Before adding or updating CI, ensure:

- `nix build .#site` builds the combined deployable output.
- The deployable root contains the Zola presentation site.
- The deployable output contains mdBook documentation under `/docs/`.
- `website/config.toml` `base_url` matches the final Pages URL.

### 6. Verify

Run:

```sh
nix build .#website
nix build .#docs
nix build .#site
nix flake check
```

For local development:

```sh
cd website && zola serve
cd docs && mdbook serve
```

Clean generated artifacts after verification if they are created in the worktree:

```sh
rm -rf docs/book website/public
```

## Reference implementation

The plinth project at `~/canix/Projects/solo/plinth` has a working implementation of this pattern with Zola landing page, mdBook documentation, rustdoc API reference, and a combined deployable output.
