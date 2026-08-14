---
name: forgejo-site
description: Create or update a Codeberg Pages site with Plinth landing, mdBook docs, Nix outputs, and Forgejo publishing. Use for full sites; route docs-only work here to forgejo-docs.
---

# Forgejo Site

Load [canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) when
the target project or Plinth producer must be resolved from canix. This skill
owns only the combined site layout; the reference owns canix project paths.

Compose three focused skills rather than reimplementing them:

- [mdbook-docs](../mdbook-docs/SKILL.md) owns `docs/`, `book.toml`, the docs
  derivation, and documentation validation.
- [forgejo-pages](../forgejo-pages/SKILL.md) owns hosted Pages workflow and
  build/publish URL rules.
- [codeberg-pages-dns](../codeberg-pages-dns/SKILL.md) owns custom-domain DNS.

This skill owns only the combined layout: Plinth at `/`, mdBook at `/docs/`,
and stable Nix outputs named `docs` and `site`. Read
[composition.md](references/composition.md) for the minimum TOML and Nix
composition when implementing that layout.

## Preconditions

- The project is a Codeberg-hosted Nix flake.
- Derive owner, repository, description, license, and source URL from real
  repository metadata.
- Stop on missing content or unsupported Plinth features. Report the missing
  source, upstream producer (`/data/nvme0/can/canix/projects/repos/owned/codeberg.org/caniko/plinth`),
  regeneration workflow, and validation command.

## Workflow

1. Create/update `docs/` using `mdbook-docs`, with `site-url = "/docs/"`.
2. Create/update `website/plinth-project.toml` using real metadata; preserve
   authored fields and add only generated-safe values.
3. Expose `docs` and `site` in `flake.nix`; render the Plinth site and copy the
   docs output beneath `/docs/`. Preserve public output names and existing
   flake outputs.
4. Ignore generated artifacts such as `docs/book/`, `website/public/`, and
   Plinth build state.
5. Validate the combined output before invoking `forgejo-pages`:

   ```sh
   plinth-project check --config website/plinth-project.toml
   plinth-project build --config website/plinth-project.toml
   nix build .#site
   ```

6. Hand off Pages deployment to `forgejo-pages`; do not duplicate its workflow
   template or runner details.

For a large flake, use the shared modularization routine at
`.skillnet/deps/simit-project-init-common/references/flake-modularization.md`.
