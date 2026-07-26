---
name: graphify
description: Build and query persistent graphs for codebases, documents, media, and cross-repository architecture. Use first when graphify-out exists or scope spans repositories.
---

# Graphify

Use the installed `graphify` CLI as the source of truth. Do not reproduce its
extraction, caching, clustering, or export pipeline in shell or Python.
If it is missing, install it with `uv tool install graphifyy` and validate with
`graphify --version`; otherwise report the missing package manager instead of
substituting another graph format.

## Existing graph

If `graphify-out/graph.json` exists, query it before rebuilding:

```sh
graphify query "<question>"
```

Use `--dfs` for a specific chain, `--budget N` for a larger answer, and
`graphify path "<node A>" "<node B>"` or `graphify explain "<node>"` for direct
traversals. Answer only from graph nodes and source locations; say when the
graph does not contain enough evidence.

## Build or update

Run a full extraction from the target root:

```sh
graphify extract <path>
```

For a code-only repository with no semantic backend, use:

```sh
graphify extract <path> --code-only
```

Use `--backend`, `--model`, `--mode deep`, or `--no-cluster` only when the
request and installed CLI support require them. Use `graphify update <path>`
for an existing graph, `graphify cluster-only <path>` to recluster it, and
`graphify diagnose multigraph` for graph integrity diagnostics.

Generated state belongs in the ignored `<path>/graphify-out/` directory. Do not
commit caches, manifests, reports, or intermediate extraction files.

## Cross-repository work

Clone remote repositories with `graphify clone <github-url>`, extract each
repository, then merge their graph outputs:

```sh
graphify merge-graphs <repo-a>/graphify-out/graph.json \
  <repo-b>/graphify-out/graph.json \
  --out graphify-out/graph.json
```

For a local multi-repository request, use the same extract-and-merge flow.
Reuse a graph for the same repository set; rebuild when it is missing, stale,
or incomplete.

## Other native commands

Use `graphify watch <path>` for code-change rebuilding, `graphify add <url>` for
URL ingestion, and the CLI's `export`, `tree`, or `global` commands for their
respective outputs. Run `graphify --help` when a requested operation is not
listed here; the installed CLI owns the current flags and behavior.

Never invent graph edges or silently replace a missing backend, source file, or
generated artifact. Report the missing producer, recovery command, and
validation command when a required input is unavailable.
