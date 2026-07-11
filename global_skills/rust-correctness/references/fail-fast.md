# Fail-Fast Validation Profile

Review public functions, methods, builders, and initialization boundaries.
Identify invalid inputs, missing required state, silently swallowed errors,
and unsafe fallback defaults. Add early-return validation with actionable
errors at the boundary, without duplicating type-system guarantees or changing
public signatures. Keep error-type design in the API errors profile and panic
site repair in the panic profile.

Useful signals include `.unwrap()`, `panic!`, `unimplemented!`,
`unreachable!`, `todo!`, and fallback branches. Run the relevant compile and
test gates from `foundation.md`.
