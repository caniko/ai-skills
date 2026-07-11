# Unused Dependency Profile

Check normal, dev, and build dependencies against source, tests, benches, and
build scripts. Remove only dependencies with no legitimate use, update the
lockfile, and run `cargo check --all-targets` and `cargo test`. Keep generated,
macro, platform, or feature-gated uses when repository evidence requires them.
