# Flake Outputs Profile

Inspect `flake.nix`, `flake.lock`, per-system helpers, flake modules,
formatters, checks, packages, apps, dev shells, and host builders. Separate
per-system outputs from system/host builders and keep public output names
stable. Ensure maintained systems expose a formatter, useful checks, and a
dev shell where the repository promises them.

Validate with `nix flake show`, focused output evals, and
`nix flake check --no-build --no-update-lock-file`.
