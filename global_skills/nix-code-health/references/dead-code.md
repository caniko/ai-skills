# Dead-Code Profile

Map Nix files and import references, flake outputs, host/profile imports,
packages, overlays, checks, CI, and deployment references before deleting
anything. Treat migrations, rollback modules, archived docs with operational
context, public outputs, and secret definitions as live until their consumers
are disproven.

Remove only confirmed unused modules, imports, overlays, outputs, and checks;
update parents in the same change and run focused evals.
