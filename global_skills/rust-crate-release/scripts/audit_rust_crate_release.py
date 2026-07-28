#!/usr/bin/env python3
"""Read-only Rust crate release readiness audit."""

from __future__ import annotations

import pathlib
import sys
import argparse
import tomllib


BASE_REQUIRED = {
    "README.md": "crates.io package page and user onboarding",
    "LICENSE": "license text matching Cargo.toml license expression",
    "Cargo.toml": "Cargo package manifest",
}


def read_manifest(path: pathlib.Path) -> dict[str, object]:
    try:
        with path.open("rb") as source:
            return tomllib.load(source)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}


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

    manifest = read_manifest(root / "Cargo.toml")
    kind = args.crate_kind
    if kind == "auto":
        if "workspace" in manifest:
            kind = "workspace"
        elif (root / "src/lib.rs").exists():
            kind = "library"
        elif (root / "src/main.rs").exists() or manifest.get("bin"):
            kind = "binary"
        else:
            failures.append("cannot infer crate kind: expected workspace, src/lib.rs, src/main.rs, or [[bin]]")
    if kind == "library" and not (root / "src/lib.rs").exists():
        failures.append("missing src/lib.rs: required for --crate-kind library")
    if kind == "binary" and not ((root / "src/main.rs").exists() or manifest.get("bin")):
        failures.append("missing binary target: expected src/main.rs or [[bin]] in Cargo.toml")
    if kind == "workspace" and "workspace" not in manifest:
        failures.append("missing [workspace]: required for --crate-kind workspace")

    if manifest:
        package = manifest.get("package") or {}
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
            if field not in package:
                failures.append(f"Cargo.toml missing `{field}`")
        metadata = package.get("metadata") or {}
        docs_metadata = metadata.get("docs") or {}
        if "rs" not in docs_metadata:
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
    if docs == "rustdoc" and manifest and "documentation" not in (manifest.get("package") or {}):
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
