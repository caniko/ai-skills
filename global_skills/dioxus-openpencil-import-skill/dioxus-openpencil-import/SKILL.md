---
name: dioxus-openpencil-import
description: Use this skill when importing, reconstructing, or syncing a Dioxus UI or Rust/RSX project into OpenPencil. It launches or connects to a Dioxus web build, captures hydrated routes in Chromium, resolves browser-computed CSS and layout, embeds images/SVG/canvas assets, creates editable HTML, invokes OpenPencil's HTML/CSS importer, and produces .fig files, screenshots, and compatibility reports. Use for Dioxus-to-OpenPencil imports, route capture, design reverse engineering, or visual handoff.
license: MIT
compatibility: Requires Python 3.11+, Playwright with Chromium (or a system Chrome/Chromium), Dioxus CLI for local projects, and @open-pencil/cli 0.13.x or a compatible newer release. Network access may be needed for first-time dependency installation.
metadata:
  author: OpenAI
  version: "0.1.0"
---

**Cross-repository work:** Read `.skillnet/deps/graphify-policy/SKILL.md` before discovery, planning, or edits when scope spans repositories.

# Dioxus to OpenPencil import

Convert the **rendered web target** of a Dioxus project into editable OpenPencil `.fig` files. Do not parse RSX directly. Dioxus state, routing, server functions, and conditional rendering must run first so Chromium exposes the hydrated DOM and browser-computed styles.

## Outputs

For every captured route, produce:

- `capture.html`: self-contained, inline-styled DOM with fixed browser geometry.
- `browser.png`: the browser reference image.
- `<route>.fig`: editable OpenPencil document.
- `openpencil.png` and `diff.png`: imported render and visual difference when verification succeeds.
- `capture.json`: compatibility details, unsupported effects, warnings, and asset failures.

For multiple routes, also produce `combined/<project>.fig`, arranging route frames on one project canvas.

## Inputs to resolve

Use the user's existing answers. Otherwise infer safe defaults instead of blocking:

- Source: a Dioxus project directory or an already-running URL.
- Routes: explicit URLs/paths, or statically discoverable `#[route("/...")]` attributes.
- Root selector: default `body`; prefer `main`, `#app`, or a stable screen container when identified.
- Viewport: default `1440x900`.
- State/auth: optional Playwright storage state, non-secret headers, wait selector, or setup JavaScript.

Dynamic route patterns are not guessed. Capture supplied concrete paths and list skipped patterns.

## Workflow

1. **Preflight the source.**
   - For a local project, confirm `Cargo.toml` contains Dioxus somewhere in the workspace or `Dioxus.toml` exists.
   - Use a browser-renderable web target. Native-only Dioxus/WGPU output cannot be read as DOM.
   - Reuse an existing server when the configured URL already responds.

2. **Resolve the skill directory.** Run the bundled script by absolute path; do not copy it into the user's repository and do not add Playwright to the project's dependencies.

3. **Install Chromium once when needed.** Prefer the pinned Python Playwright release:

   ```bash
   uvx --from 'playwright==1.61.0' playwright install chromium
   ```

4. **Run the importer.** Prefer `uv`, which reads the script's pinned inline dependencies:

   ```bash
   uv run /absolute/path/to/dioxus-openpencil-import/scripts/dioxus_to_openpencil.py \
     --project /absolute/path/to/dioxus-project \
     --out /absolute/path/to/dioxus-project/.openpencil-import
   ```

   For selected routes:

   ```bash
   uv run /absolute/path/to/dioxus-openpencil-import/scripts/dioxus_to_openpencil.py \
     --project /absolute/path/to/dioxus-project \
     --route / \
     --route /settings \
     --route /account/profile \
     --selector main \
     --viewport 1440x900 \
     --out /absolute/path/to/dioxus-project/.openpencil-import
   ```

   For an already-running app:

   ```bash
   uv run /absolute/path/to/dioxus-openpencil-import/scripts/dioxus_to_openpencil.py \
     --url http://127.0.0.1:8080 \
     --route /dashboard \
     --out /absolute/path/to/output
   ```

5. **Handle project-specific startup.** The default is `dx serve --web`. Override rather than editing the project:

   ```bash
   --serve-command 'dx serve --package frontend --web'
   ```

   For fullstack projects, keep the backend available so server functions and hydration complete.

6. **Handle stateful screens when needed.**
   - Use `--storage-state auth.json` for an authenticated browser context.
   - Use repeated `--header Name=Value` only for non-secret test headers.
   - Use `--wait-selector '[data-ready=true]'` for asynchronous UI readiness.
   - Use `--setup-js setup.js` for clicks, form state, theme selection, or fixture injection. The file is an async JavaScript function body and can read `window.__DIOXUS_OPENPENCIL_ROUTE__`.
   - Never place credentials directly in `setup.js`, command history, reports, or generated HTML. Password inputs are automatically redacted, but all other visible values and images should be treated as sensitive.

7. **Inspect `summary.json`.** Treat a run as complete only when every requested route is `ok` and its `.fig` exists. A `partial` result requires remediation or a transparent user-facing note. When `--capture-only` was explicitly requested, `captured` is expected.

8. **Review visual differences.** Open `browser.png`, `openpencil.png`, and `diff.png`. Prioritize geometry, text wrapping, images, clipping, and backgrounds. A numerical diff is diagnostic, not a pass/fail oracle.

9. **Report limitations.** Read `references/compatibility.md` when `unsupportedCount`, `assetFailureCount`, or `warningCount` is nonzero, or when visual drift is material.

## Dependency fallback

If `uv` is unavailable, use a temporary virtual environment outside the project:

```bash
python3 -m venv /tmp/dioxus-openpencil-venv
/tmp/dioxus-openpencil-venv/bin/pip install 'playwright==1.61.0' 'Pillow==12.3.0'
/tmp/dioxus-openpencil-venv/bin/python -m playwright install chromium
/tmp/dioxus-openpencil-venv/bin/python \
  /absolute/path/to/dioxus-openpencil-import/scripts/dioxus_to_openpencil.py \
  --project /absolute/path/to/project
```

The script uses an installed `openpencil` binary first, then falls back to:

```bash
npx --yes @open-pencil/cli@0.13.2
```

Use `--openpencil-command` to pin a project-approved executable. Use `--capture-only` only when the user explicitly accepts HTML/screenshots without `.fig` output.

## Quality checks

Before completion:

- Confirm every requested route loaded the intended state, not an error, login, loading, or blank screen.
- Confirm `.fig` files are non-empty and render verification did not fail silently.
- Confirm local images and inline SVG/canvas content were embedded or list failures.
- Do not claim application logic, Dioxus components, Rust modules, signals, event handlers, or router semantics were imported. The editable output represents a rendered visual state.
- Preserve the original repository. Generated files belong under the chosen output directory only.
