from pathlib import Path
import importlib.util
import sys
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dioxus_to_openpencil.py"
spec = importlib.util.spec_from_file_location("dioxus_to_openpencil", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_route_discovery():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "src").mkdir()
        (root / "src" / "main.rs").write_text(
            '''
            #[derive(Routable)]
            enum Route {
                #[route("/")]
                Home {},
                #[route("/settings")]
                Settings {},
                #[route("/users/:id")]
                User { id: String },
            }
            ''',
            encoding="utf-8",
        )
        routes, skipped = module.discover_dioxus_routes(root)
        assert [route.path for route in routes] == ["/", "/settings"]
        assert skipped == ["/users/:id"]


def test_viewport():
    assert module.parse_viewport("1440x900") == (1440, 900)


def test_workspace_validation_accepts_member_dioxus_dependency():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "Cargo.toml").write_text('[workspace]\nmembers = ["app"]\n', encoding="utf-8")
        (root / "app").mkdir()
        (root / "app" / "Cargo.toml").write_text(
            '[dependencies]\ndioxus = "0.7"\n', encoding="utf-8"
        )
        module.validate_project(root)


def test_url_redaction_and_query_safe_slug():
    value = "https://user:pass@example.com/path?view=grid&token=secret-value#fragment"
    assert module.redact_url_for_report(value) == (
        "https://example.com/path?view=grid&token=%5BREDACTED%5D"
    )
    slug = module.slugify(value)
    assert "secret" not in slug
    assert slug.startswith("path-query-")


def test_export_command_uses_current_cli_flags(monkeypatch, tmp_path):
    captured = {}

    def fake_run(command, cwd, timeout=300):
        captured["command"] = list(command)
        output = Path(command[command.index("-o") + 1])
        output.write_bytes(b"png")
        return module.CommandResult(list(command), 0, "ok", "")

    monkeypatch.setattr(module, "run_command", fake_run)
    fig = tmp_path / "input.fig"
    fig.write_bytes(b"fig")
    png = tmp_path / "output.png"
    result = module.export_fig(["openpencil"], fig, png, tmp_path)
    assert result["status"] == "ok"
    assert captured["command"] == [
        "openpencil", "export", str(fig), "-f", "png", "-o", str(png)
    ]
