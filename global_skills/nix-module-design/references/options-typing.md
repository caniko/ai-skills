# Options Typing Profile

List every `mkOption`, `mkEnableOption`, freeform block, assertion, default,
example, and deprecation in scope. Replace `types.raw`, untyped attrs, and
loose strings with the narrowest practical type: enum, port, path, `attrsOf`
submodule, `nullOr`, or `listOf`.

Add `defaultText` when defaults depend on `config`, `pkgs`, flake inputs, or
generated paths. Use `lib.types.submodule` for repeated structured settings
and assertions for cross-option invariants that types cannot express. Preserve
backward compatibility with warnings or aliases when necessary.
