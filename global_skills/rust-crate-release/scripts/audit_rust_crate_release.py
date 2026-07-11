#!/usr/bin/env python3
"""Read-only Rust crate release readiness audit."""

from __future__ import annotations

import pathlib
import re
import sys
import argparse


BASE_REQUIRED = {
    "README.md": "crates.io package page and user onboarding",
    "LICENSE": "license text matching Cargo.toml license expression",
    "Cargo.toml": "Cargo package manifest",
}


def read(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def has_manifest_field(manifest: str, field: str) -> bool:
    return re.search(rf"(?m)^\s*{re.escape(field)}\s*=", manifest) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--crate-kind",
        choices=("auto", "library", "binary", "workspace"),
        default="auto",
        help="crate shape to require (default: infer from Cargo.toml/source)",
    )
    parser.add_argument(
        "--forge",
        choices=("auto", "forgejo", "github", "none"),
        default="auto",
        help="CI provider whose workflow must exist",
    )
    parser.add_argument(
        "--docs",
        choices=("auto", "mdbook", "rustdoc", "none"),
        default="auto",
        help="documentation surface to require",
    )
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    failures: list[str] = []

    for rel, reason in BASE_REQUIRED.items():
        if not (root / rel).exists():
            failures.append(f"missing {rel}: required for {reason}")

    manifest = read(root / "Cargo.toml")
    kind = args.crate_kind
    if kind == "auto":
        if re.search(r"(?m)^\[workspace\]", manifest):
            kind = "workspace"
        elif (root / "src/lib.rs").exists():
            kind = "library"
        elif (root / "src/main.rs").exists() or "[[bin]]" in manifest:
            kind = "binary"
        else:
            failures.append("cannot infer crate kind: expected workspace, src/lib.rs, src/main.rs, or [[bin]]")
    if kind == "library" and not (root / "src/lib.rs").exists():
        failures.append("missing src/lib.rs: required for --crate-kind library")
    if kind == "binary" and not ((root / "src/main.rs").exists() or "[[bin]]" in manifest):
        failures.append("missing binary target: expected src/main.rs or [[bin]] in Cargo.toml")
    if kind == "workspace" and not re.search(r"(?m)^\[workspace\]", manifest):
        failures.append("missing [workspace]: required for --crate-kind workspace")

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

    for rel in ["Cargo.lock", "flake.nix", "flake.lock"]:
        if not (root / rel).exists():
            failures.append(f"missing {rel}: required for reproducible strict CI/release checks")

    forge = args.forge
    workflow_dirs = {
        "forgejo": root / ".forgejo" / "workflows",
        "github": root / ".github" / "workflows",
    }
    if forge == "auto":
        forge = "forgejo" if workflow_dirs["forgejo"].exists() else "github" if workflow_dirs["github"].exists() else "none"
    if forge in workflow_dirs and not any(workflow_dirs[forge].glob("*.y*ml")):
        failures.append(f"missing {forge} workflow: required for --forge {forge}")

    docs = args.docs
    if docs == "auto":
        docs = "mdbook" if (root / "docs" / "book.toml").exists() else "rustdoc"
    if docs == "mdbook" and not (root / "docs" / "book.toml").exists():
        failures.append("missing docs/book.toml: required for --docs mdbook")
    if docs == "rustdoc" and manifest and not has_manifest_field(manifest, "documentation"):
        failures.append("Cargo.toml missing documentation: required for --docs rustdoc")

    if failures:
        print("release audit failed:")
        for failure in failures:
            print(f"- {failure}")
        print("\nvalidation commands after fixing:")
        print("- nix flake check --keep-going --print-build-logs")
        print("- nix develop -c cargo package --allow-dirty")
        print("- nix develop -c cargo publish --dry-run")
        return 1

    print("release audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
