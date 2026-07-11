# Trait Design Profile

Find duplicated behavior, type-tag dispatch, concrete parameters that only
use a subset of an API, and fat traits. Extract a minimal trait only when it
has multiple meaningful implementations or is a documented extension point.
Use defaults or blanket implementations for genuinely identical behavior,
split optional methods into extension traits, and apply dependency inversion at
module boundaries.

Do not alter plugin or serialization trait contracts casually. Compile after
each extraction and run tests at the end.
