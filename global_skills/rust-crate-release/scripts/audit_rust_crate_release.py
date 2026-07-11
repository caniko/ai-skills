#!/usr/bin/env python3
"""Read-only Rust crate release readiness audit."""

from __future__ import annotations

import pathlib
import re
import sys


REQUIRED = {
    "README.md": "crates.io package page and user onboarding",
    "LICENSE": "license text matching Cargo.toml license expression",
    "Cargo.toml": "Cargo package manifest",
    "src/lib.rs": "library crate root",
}


def read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def has_manifest_field(manifest: str, field: str) -> bool:
    return re.search(rf"(?m)^\s*{re.escape(field)}\s*=", manifest) is not None


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []

    for rel, reason in REQUIRED.items():
        if not (root / rel).exists():
            failures.append(f"missing {rel}: required for {reason}")

    manifest = read(root / "Cargo.toml")
    if manifest:
        for field in [
            "description",
            "license",
            "repository",
            "readme",
            "documentation",
            "rust-version",
            "keywords",
            "categories",
            "include",
        ]:
            if not has_manifest_field(manifest, field):
                failures.append(f"Cargo.toml missing `{field}`")
        if "[package.metadata.docs.rs]" not in manifest:
            failures.append("Cargo.toml missing `[package.metadata.docs.rs]`")

    for rel in ["Cargo.lock", "flake.nix", "flake.lock", ".forgejo/workflows/ci.yml"]:
        if not (root / rel).exists():
            failures.append(f"missing {rel}: required for reproducible strict CI/release checks")

    if not (root / "docs" / "book.toml").exists():
        failures.append("missing docs/book.toml: required for Codeberg Pages docs")

    if failures:
        print("release audit failed:")
        for failure in failures:
            print(f"- {failure}")
        print("\nvalidation commands after fixing:")
        print("- nix flake check --keep-going --print-build-logs")
        print("- nix develop -c cargo publish --dry-run")
        return 1

    print("release audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
