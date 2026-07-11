# Clippy Profile

Run the repository-authoritative Clippy command, beginning with the narrowest
safe autofix when requested. Verify with all targets and warnings denied:

```sh
cargo clippy --all-targets --all-features -- -D warnings
```

Do not suppress a warning merely to make the gate green. Preserve behavior,
inspect every autofix, and rerun formatting, compilation, and tests.
