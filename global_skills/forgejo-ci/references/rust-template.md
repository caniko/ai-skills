# Raw Cargo Rust Workflow

Use only when the project is genuinely Cargo-only and Simit cannot express the
workflow. Otherwise generate with `simit init ci` and inspect its diff.

```yaml
jobs:
  test:
    runs-on: atlas
    container: rust:<MSRV>-bookworm
    steps:
      - uses: https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
      - uses: https://github.com/Swatinem/rust-cache@v2
        with:
          shared-key: ${{ github.workflow }}
          cache-on-failure: true
      - run: cargo fmt --all -- --check
      - run: cargo clippy --all-targets --all-features -- --deny warnings
      - run: cargo nextest run --all-features
```

Add audit, deny, docs, or package steps only when project metadata and the
requested policy justify them. Use the image tag actually supported by the
project's MSRV; do not invent a distribution tag.
