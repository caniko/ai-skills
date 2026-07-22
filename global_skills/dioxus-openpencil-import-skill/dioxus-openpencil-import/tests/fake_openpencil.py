#!/usr/bin/env python3
"""Minimal CLI double for exercising OpenPencil orchestration."""
from __future__ import annotations
import base64
import json
import sys
from pathlib import Path

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
)


def value_after(arguments: list[str], flag: str) -> str:
    try:
        return arguments[arguments.index(flag) + 1]
    except (ValueError, IndexError) as error:
        raise SystemExit(f"missing {flag}") from error


def main(arguments: list[str]) -> int:
    if not arguments:
        return 2
    command, *rest = arguments
    if command == "import":
        if "--json" not in rest:
            raise SystemExit("import should request JSON output")
        output = Path(value_after(rest, "-o"))
        output.write_bytes(b"fake-openpencil-fig")
        print(json.dumps({"output": str(output), "pages": 1, "rootElements": 1}))
        return 0
    if command == "export":
        if "--json" in rest:
            raise SystemExit("export does not support --json")
        if value_after(rest, "-f").lower() != "png":
            raise SystemExit("fake exporter only supports PNG")
        output = Path(value_after(rest, "-o"))
        output.write_bytes(PNG)
        print(f"Exported {output}")
        return 0
    raise SystemExit(f"unsupported command: {command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
