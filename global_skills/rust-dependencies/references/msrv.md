# MSRV Profile

Read `rust-version`, edition, lockfile, CI, Nix, and documented compatibility
policy. If MSRV is declared, validate it with the repository toolchain. If it
is absent, derive the minimum only from repository evidence and toolchain/API
requirements; do not invent a promise. Update metadata and documentation only
when the maintainer policy is clear.
