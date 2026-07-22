# Dioxus → OpenPencil agent skill

A portable Agent Skills bundle that turns hydrated Dioxus web routes into editable OpenPencil `.fig` files.

The browser renders the real Dioxus state first. The script then converts resolved browser geometry and computed styles into self-contained HTML, embeds supported assets, invokes OpenPencil's HTML/CSS importer, and compares browser and OpenPencil renders.

## Install as a project skill

Copy this folder to:

```text
<project>/.agents/skills/dioxus-openpencil-import/
```

The folder name must match the `name` in `SKILL.md`.

## First run

```bash
uvx --from 'playwright==1.61.0' playwright install chromium
uv run scripts/dioxus_to_openpencil.py \
  --project /path/to/dioxus-project \
  --route / \
  --route /settings
```

See `SKILL.md` for the agent workflow and `references/compatibility.md` for fidelity and security limits.

## Tests

```bash
python -m pytest -q
python tests/smoke_capture.py
```

The smoke test uses Playwright's installed Chromium by default. Set `DIOXUS_OPENPENCIL_TEST_BROWSER=/path/to/chromium` to select another executable.

## License

MIT
