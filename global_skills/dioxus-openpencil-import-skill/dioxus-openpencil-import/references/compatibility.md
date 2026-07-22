# Compatibility and known limits

## What is preserved

The capture script converts browser layout into fixed, nested, absolute-positioned frames. This avoids relying on OpenPencil's headless CSS engine for margins, CSS Grid, selector matching, variables, media queries, or `calc()` resolution.

It preserves browser-resolved values for:

- Width, height, and relative x/y geometry
- Solid backgrounds
- Per-side borders and corner radii
- Simple shadows and opacity
- Clipping for hidden/clip overflow
- Text color, family, size, weight, style, line height, letter spacing, alignment, decoration, case, whitespace, and simple shadow
- `<img>` content when it can be fetched and embedded as a base64 data URL
- Inline SVG and readable `<canvas>` content as embedded image layers
- Current values for common text inputs, textareas, selects, and checked controls; password values are replaced with a fixed redaction marker

## Visual reference rather than editable fidelity

The browser screenshot remains authoritative for:

- Gradients and CSS background images
- Filters and backdrop filters
- Transforms, rotations, perspective, and 3D effects
- Masks, clip paths, and blend modes
- Pseudo-elements and generated markers (`::before`, `::after`, and `::marker`), including icon-font glyphs
- Video frames without an embeddable poster
- Cross-origin or authenticated assets that the page cannot fetch
- Browser-native form-control appearance
- Complex multi-shadow lists, outlines, and nontrivial stacking contexts (`z-index`)
- Font substitutions when OpenPencil cannot access the browser's font

These are recorded in `capture.json`. Repair the design manually, supply an embeddable asset, or accept a raster reference rather than hiding the limitation.

## Dioxus-specific boundaries

- The workflow captures Dioxus **web/fullstack web output**. Desktop/mobile/native-renderer-only projects need a web feature or a separate native screenshot reconstruction path.
- It captures concrete UI states, not RSX component boundaries, Rust types, signals, hooks, event handlers, router definitions, or server functions.
- Static `#[route("/path")]` values can be discovered. Parameterized routes require concrete `--route` values.
- Fullstack screens must be captured while their backend and fixture data are available.
- Responsive designs should be captured once per required viewport and named accordingly.

## Security

Generated HTML contains visible text, non-password form values, and embedded images from the captured screen. Password fields and common secret-bearing URL query parameters are redacted, but other sensitive screen content is not. Use test accounts and fixtures, avoid production secrets, and inspect artifacts before sharing.

## Upstream references

- OpenPencil DOM/CSS mapping: https://openpencil.dev/reference/dom-css-mapping
- OpenPencil CLI: https://openpencil.dev/reference/cli
- OpenPencil repository: https://github.com/open-pencil/open-pencil
- Dioxus 0.7 getting started: https://dioxuslabs.com/learn/0.7/getting_started/
- Dioxus web testing with Playwright: https://dioxuslabs.com/learn/0.7/guides/testing/web/
