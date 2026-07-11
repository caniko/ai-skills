# Store Purity Profile

Search for absolute host paths, `builtins.pathExists`, `builtins.readFile`,
`builtins.getFlake`, path inputs, and unpinned fetchers. Classify each finding
as intentional local state, generated source, secret material, package source,
or accidental workstation coupling.

Move reusable constants into pure data or declared flake inputs. Keep runtime
host paths behind options, not eval-time reads. Require pinned hashes and lock
data for fetches. Path inputs are acceptable only for explicitly local
development flakes and must be documented as non-portable. Validate with
`--no-update-lock-file`.
