# Module Layout Profile

List source files and line counts, map the module tree, and identify cohesive
splits for oversized files and merges for tiny non-entry modules. Preserve
public re-exports, update imports after each move, document module entry
points, and avoid circular sibling dependencies. Run `cargo check --all-
targets` after every structural change and `cargo test` at the end.
