# Release Infrastructure Mode

Run `simit init flake` and/or `simit init ci --platform <platform>` first and
inspect the generated diff. Use `rust-project-flake` only for project-specific
crane follow-up. For Codeberg/Forgejo CI, use `.forgejo/workflows/`, the atlas
runner labels from `atlas-runner`, and the canonical checkout/action URLs.
Keep release jobs separate from ordinary CI and preserve concurrency groups.

For Pages documentation, delegate to `mdbook-docs`, `forgejo-pages`,
`forgejo-docs`, or `forgejo-site` according to the requested layout. Do not
copy their deployment policy into this skill.

For canix-backed publication, load
`simit-canix-release-secrets.md` and inspect
`simit release secrets contract --json` before pushing a release tag.
