# Combined Site Composition

The public outputs are `docs` (mdBook) and `site` (Plinth landing page with
the docs copied under `/docs/`). Keep `docs/book.toml` at `site-url = "/docs/"`
and derive owner/repository URLs from the Codeberg remote.

Minimum project-site shape:

```toml
[site]
title = "<Project>"
description = "<description>"
base_url = "/"

[[nav]]
label = "Docs"
href = "/docs/"

[[nav]]
label = "Source"
href = "https://codeberg.org/<user>/<repo>"

[[pages]]
slug = "index"
title = "<Project>"
description = "<description>"

[[pages.sections]]
type = "hero"
```

Add only fields supported by `plinth-project`; a required unsupported feature is
a Plinth feature void, not a reason to add another site generator.

The `site` derivation should render `website/plinth-project.toml`, install the
generated landing output, then copy the `docs` derivation into `$out/docs/`.
Prefer Plinth's current `mkProjectSite` helper when the project imports it.
Keep generated output ignored and preserve the public `docs`/`site` names.
