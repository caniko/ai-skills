---
name: nix-data-boundaries
description: Enforce single sources of truth for Nix host, service, domain, user, package, and environment data. Use when data is duplicated, directly imported through deep paths, hardcoded in modules, or bypasses adapter modules.
---

# Nix: Data Boundaries

## Goal

Keep shared data in one source and force consumers through a stable facade or adapter.

## Workflow

1. Identify duplicated literals or records for hosts, domains, services, users, ports, package sets, secrets, and profile toggles.
2. Choose or create one pure data source and one module/lib facade for consumers. Do not let every module import the raw data file.
3. Refactor ordinary modules to consume evaluated config or facade helpers, leaving direct imports only in documented adapters/builders.
4. Add a lightweight structure check when the repo can enforce the boundary with grep or evaluation.
5. Verify all consumers still evaluate and that generated aliases/routes/services preserve the same values.

## Nix Specifics

- Prefer `config.<namespace>.lib` or `config.<namespace>.<registry>` facades for NixOS modules.
- For Home Manager integrated with NixOS, prefer `osConfig` when available and keep standalone fallbacks explicit.
- Boundary checks should have narrow allowlists with comments for every exception.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **10** as relevant.

| Pattern | Weight |
|---|---|
| `import ../` | 1 |
| `import ../../` | 1 |
| `hostsData.` | 3 |
| `servicesData` | 2 |
| `domain = "` | 2 |
| `hostname = "` | 1 |
| `port =` | 1 |
