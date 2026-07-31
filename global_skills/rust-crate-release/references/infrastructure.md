# Release Infrastructure Mode

Run `simit init flake` and/or `simit init ci --platform <platform>` first and
inspect the generated diff. Use `rust-project-flake` only for project-specific
crane follow-up. For Codeberg/Forgejo CI, use `.forgejo/workflows/`, the
provider's runner labels, and the canonical checkout/action URLs.
Keep release jobs separate from ordinary CI and preserve concurrency groups.

For Pages documentation, delegate to `mdbook-docs`, `forgejo-pages`,
`forgejo-docs`, or `forgejo-site` according to the requested layout. Do not
copy their deployment policy into this skill.
