#!/usr/bin/env python3
"""Validate OpenPencil parity evidence and optionally run exact gate commands."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path


PRODUCTION_STATUSES = {"direct", "auth-boundary", "not-deployed"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(24)
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError(f"{path}: not a PNG with an IHDR header")
    return struct.unpack(">II", header[16:24])


def require_png(
    base: Path,
    value: object,
    viewport: tuple[int, int],
    label: str,
    tolerance: int = 0,
) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: missing PNG path")
    path = (base / value).resolve()
    if not path.is_file():
        raise ValueError(f"{label}: missing {path}")
    actual = png_size(path)
    if any(abs(actual[index] - viewport[index]) > tolerance for index in range(2)):
        raise ValueError(f"{label}: expected {viewport[0]}x{viewport[1]}, got {actual[0]}x{actual[1]}")
    return str(path)


def validate_manifest(path: Path) -> tuple[Path, list[dict[str, object]]]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("project"), str):
        raise ValueError("manifest requires a string project")
    root_value = data.get("root", ".")
    if not isinstance(root_value, str):
        raise ValueError("manifest root must be a string")
    root = (path.parent / root_value).resolve()
    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ValueError("manifest requires at least one surface")

    names: set[str] = set()
    routes: set[str] = set()
    for index, surface in enumerate(surfaces):
        label = f"surface[{index}]"
        if not isinstance(surface, dict):
            raise ValueError(f"{label}: expected an object")
        name = surface.get("name")
        route = surface.get("route")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"{label}: name must be non-empty and unique")
        if not isinstance(route, str) or not route.startswith("/") or route in routes:
            raise ValueError(f"{name}: route must start with / and be unique")
        names.add(name)
        routes.add(route)

        viewport = surface.get("viewport")
        if (
            not isinstance(viewport, list)
            or len(viewport) != 2
            or any(not isinstance(value, int) or value <= 0 for value in viewport)
        ):
            raise ValueError(f"{name}: viewport must be [positive width, positive height]")
        expected = (viewport[0], viewport[1])
        require_png(
            path.parent,
            surface.get("openpencil_png"),
            expected,
            f"{name} OpenPencil",
            tolerance=1,
        )
        require_png(path.parent, surface.get("implementation_png"), expected, f"{name} implementation")

        production = surface.get("production")
        if not isinstance(production, dict):
            raise ValueError(f"{name}: production must be an object")
        status = production.get("status")
        if status not in PRODUCTION_STATUSES:
            raise ValueError(f"{name}: invalid production status {status!r}")
        if not isinstance(production.get("url"), str) or not production["url"]:
            raise ValueError(f"{name}: production URL is required")
        if status == "direct":
            require_png(path.parent, production.get("png"), expected, f"{name} production")
        elif production.get("png") is not None:
            require_png(path.parent, production["png"], expected, f"{name} production boundary")

        acceptance = surface.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance or any(
            not isinstance(item, str) or not item for item in acceptance
        ):
            raise ValueError(f"{name}: acceptance must contain non-empty statements")
        gates = surface.get("gates")
        if not isinstance(gates, list) or not gates:
            raise ValueError(f"{name}: at least one exact gate command is required")
        for gate in gates:
            if not isinstance(gate, list) or not gate or any(not isinstance(arg, str) for arg in gate):
                raise ValueError(f"{name}: each gate must be a non-empty string array")
    return root, surfaces


def run_gates(root: Path, surfaces: list[dict[str, object]]) -> None:
    completed: set[tuple[str, ...]] = set()
    for surface in surfaces:
        for gate in surface["gates"]:
            command = tuple(gate)
            if command in completed:
                continue
            completed.add(command)
            print(f"+ {' '.join(command)}", flush=True)
            subprocess.run(command, cwd=root, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-gates", action="store_true")
    args = parser.parse_args()
    try:
        root, surfaces = validate_manifest(args.manifest.resolve())
        if args.run_gates:
            run_gates(root, surfaces)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"parity manifest failed: {error}", file=sys.stderr)
        return 1
    print(f"parity manifest passed: {len(surfaces)} surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
