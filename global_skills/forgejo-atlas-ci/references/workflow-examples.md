# Atlas Workflow Examples

Use these only when Simit cannot render the required workflow. Prefer the
installed generator and keep generated checkout/cache steps intact.

## Cargo

```yaml
jobs:
  test:
    runs-on: atlas
    container: rust:1.85-bookworm
    steps:
      - uses: https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
      - run: cargo test --all-features
      - run: cargo clippy --all-targets --all-features -- --deny warnings
      - run: cargo fmt --all -- --check
```

Use `rust-cache` or the Forgejo cache action keyed on `Cargo.lock`; CI
containers must not assume host-side sccache is available.

## Nix

Use `atlas` with in-job Nix for read-only evaluation. Use
`atlas-nix-trusted` only for jobs that write through the host Nix daemon:

```yaml
jobs:
  flake-check:
    runs-on: atlas
    steps:
      - uses: https://code.forgejo.org/actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
      - uses: https://github.com/cachix/install-nix-action@ba0dd844c9180cbf77aa72a116d6fbc515d0e87b # v27
        with:
          extra_nix_config: |
            experimental-features = nix-command flakes
            substituters = https://attic.candee.baby/canix https://cache.nixos.org
            trusted-public-keys = canix:lPzPzKrmYqW5Rxa5r0uQWvCqD3S5nx0h2eCy7XD5JM8= cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
      - run: nix flake check --keep-going --print-build-logs
```
