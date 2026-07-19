# Module Layout Profile

List source files and line counts, map the module tree, and identify cohesive
splits for oversized files and merges for tiny non-entry modules. Preserve
public re-exports, update imports after each move, document module entry
points, and avoid circular sibling dependencies. Run `cargo check --all-
targets` after every structural change and `cargo test` at the end.

In modernize mode, split every hand-written source file above 1,000 lines
unless it is demonstrably one generated artifact, declarative table, macro
body, or other indivisible exceptional shape. For files from 500–1,000 lines,
split when the responsibility map shows more than two independently changing
areas. A private binary entry point is not an exception, and “revisit when the
next feature arrives” is not a successful disposition.

Extract by stable responsibility—CLI parsing, discovery, reconciliation,
runtime control, protocol adaptation, persistence—not by arbitrary line
chunks. After splitting, reassess type cohesion and behavioral duplication;
module movement alone does not close either obligation. Record before/after
file sizes and the resulting dependency direction.
