# Format and Style Profile

Run the repository formatter check before style edits. Replace broad
`with pkgs;`, `with upkgs;`, and broad package lists with explicit provenance,
local `inherit`, or package-set prefixes. Keep conventional local metadata
idioms such as maintainer scopes and preserve meaningful `let` names.

Watch for variables that intentionally shadow package names. Avoid style-only
churn in generated hardware/disk files and add grep-based enforcement only
after the tree is clean.
