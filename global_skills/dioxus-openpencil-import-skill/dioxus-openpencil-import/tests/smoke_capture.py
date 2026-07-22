#!/usr/bin/env python3
from __future__ import annotations
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixture"
SCRIPT = ROOT / "scripts" / "dioxus_to_openpencil.py"
FAKE_OPENPENCIL = ROOT / "tests" / "fake_openpencil.py"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def main() -> int:
    with tempfile.TemporaryDirectory() as output:
        handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(FIXTURE), **kwargs)
        with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_address[1]
            command = [
                sys.executable,
                str(SCRIPT),
                "--url", f"http://127.0.0.1:{port}",
                "--route", "/",
                "--selector", "#app",
                "--openpencil-command", f"{sys.executable} {FAKE_OPENPENCIL}",
                "--out", output,
            ]
            browser = os.environ.get("DIOXUS_OPENPENCIL_TEST_BROWSER")
            if browser:
                command.extend(["--browser-executable", browser])
            completed = subprocess.run(command, text=True, capture_output=True, check=False)
            server.shutdown()
            thread.join(timeout=2)
        if completed.returncode != 0:
            print(completed.stdout)
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
        summary = json.loads((Path(output) / "summary.json").read_text(encoding="utf-8"))
        record = summary["routes"][0]
        assert record["status"] == "ok"
        html = (Path(output) / record["html"]).read_text(encoding="utf-8")
        assert "position: absolute" in html
        assert "data:image/svg+xml;base64," in html
        assert "supersecret" not in html
        assert "••••••••" in html
        assert (Path(output) / record["screenshot"]).exists()
        assert (Path(output) / record["fig"]).exists()
        assert record["export"]["status"] == "ok"
        assert (Path(output) / record["visualDiff"]["diff"]).exists()
        print("smoke capture and import orchestration passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
