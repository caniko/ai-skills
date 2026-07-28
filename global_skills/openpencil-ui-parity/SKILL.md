---
name: openpencil-ui-parity
description: Compare OpenPencil, deployed, and local UIs at exact routes and viewports, then repair measured visual, responsive, or interaction drift with a fix-loop.
---

# OpenPencil UI Parity

Make OpenPencil the design source of truth and use `$fix-loop` to close verified gaps without inventing states, credentials, or replacement designs.

## Required inputs

Resolve these before editing:

- the `.op` file and OpenPencil MCP connection;
- the implementation repository and its supported build/test commands;
- the deployed base URL;
- the route and authentication boundary for each compared surface;
- exact desktop and mobile viewports;
- a deterministic browser capture path that waits for hydration, fonts, network idle, and stable layout.

If an authenticated production surface cannot be reached with an authorized session, record it as `auth-boundary`. Compare the public redirect or identity-provider page honestly, and use the project's isolated authenticated E2E harness for implementation evidence. Never copy cookies, guess credentials, or label a local fixture as production.

## Workflow

### 1. Discover the complete surface

Read the implementation route tree, backend-visible capabilities, OpenPencil page list, and existing visual or geometry tests. Build a route/artboard matrix before changing code.

Include:

- every user-facing route and meaningful state represented in OpenPencil;
- desktop and mobile variants;
- empty, loading, validation, unavailable, forbidden, and success states when designed;
- overlays, drawers, trays, menus, and modals;
- authentication and external identity-provider boundaries.

Do not count callbacks, health endpoints, thumbnails, or static resources as fake application pages.

### 2. Capture three evidence sets

Use OpenPencil MCP for all design inspection and `.op` mutation. For each mapped artboard:

1. Read the node tree and computed layout.
2. Export or screenshot the exact artboard.
3. Run layout lint and record error-severity findings.

Capture the deployed route at the same viewport. Then build and capture the local implementation through its real server or authenticated E2E harness. A server-rendered page is not settled evidence until its client bundle loaded and hydration completed.

Keep screenshots as artifacts. Do not compare a live page from memory.

### 3. Compare in this order

Evaluate each surface on five axes:

1. **Capability** — every designed action and state exists and maps to a real backend capability.
2. **Structure** — shell, tracks, navigation, reading order, responsive composition, and overlays.
3. **Geometry** — exact viewport, major rectangles, overlap, overflow, card count, row width, and touch targets.
4. **Tokens** — font files actually load; colors, type scale, spacing, radii, and borders use the intended tokens.
5. **Finish** — visual hierarchy, density, wrapping, alignment, icon treatment, and state legibility.

Capability and structure outrank pixel similarity. Do not hide missing functionality behind a visually similar mock.

### 4. Run the fix-loop

Follow `$fix-loop` for every failing surface:

1. Name one exact failing gate and preserve its evidence.
2. Trace the shared implementation path before editing.
3. Fix the smallest root cause that explains the failure.
4. Rebuild assets when the changed source requires it.
5. Rerun the exact failing gate first.
6. Recapture and compare the same viewport.
7. Run adjacent route, mobile, and interaction gates.
8. Repeat until the exact gate and post-checks are green.

Typical root causes include an unserved client bundle, stale generated CSS, an unscoped grid rule, a shell dimension mismatch, or one shared component diverging across routes. Prefer fixing that shared cause once.

Do not make speculative visual edits while hydration, fonts, seed data, or screenshots are invalid.

### 5. Verify and report

Run the repository's focused geometry tests, visual rubric, accessibility checks, asset build, and UI-health gate. Re-run OpenPencil lint for any changed artboard.

The final report must separate:

- OpenPencil-to-local parity;
- deployed-to-local parity;
- authentication boundaries that prevent a direct deployed comparison;
- fixed defects;
- remaining measured gaps, with routes and evidence;
- exact passing and failing commands.

“Looks close” is not a passing result.

## Evidence manifest

For broad audits, create a JSON manifest and validate it with:

```bash
python scripts/check_parity_manifest.py parity-manifest.json
```

Use `--run-gates` only after inspecting the manifest's command arrays:

```bash
python scripts/check_parity_manifest.py parity-manifest.json --run-gates
```

Paths are resolved relative to the manifest. Each surface requires a unique name and route, `[width, height]`, OpenPencil and implementation PNGs, a production status, at least one acceptance statement, and at least one exact gate command. `production.status` is one of `direct`, `auth-boundary`, or `not-deployed`; `direct` also requires a production PNG.

Implementation and direct-production PNGs must match the viewport exactly. OpenPencil exports may be one pixel larger on either axis because an artboard border is included.

Minimal shape:

```json
{
  "project": "example",
  "root": ".",
  "surfaces": [{
    "name": "plans-grid",
    "route": "/workspaces/demo/plans?view=grid",
    "viewport": [1440, 1024],
    "openpencil_png": "evidence/op/plans-grid.png",
    "implementation_png": "evidence/local/plans-grid.png",
    "production": {
      "status": "auth-boundary",
      "url": "https://example.test/app",
      "png": "evidence/production/login.png"
    },
    "acceptance": ["facets and results do not intersect", "grid has at least two columns"],
    "gates": [["cargo", "test", "--test", "ui_geometry", "plans_grid"]]
  }]
}
```

## Non-negotiable rules

- OpenPencil MCP, not an importer or a screenshot trace, owns design changes.
- Preserve unrelated working-tree changes.
- Do not weaken a test, visual rubric, or acceptance threshold to obtain green.
- Do not silently substitute unavailable fonts, images, seed data, or auth.
- Do not deploy unless the user requested release or deployment.
- Keep desktop and mobile in one OpenPencil project when the product does.
