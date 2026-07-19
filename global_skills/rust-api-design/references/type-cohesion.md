# Type Cohesion Profile

Inventory candidate structs and enums using field or variant count, method and
impl size, constructor arity, construction sites, dependency fan-out, shared
state, and serialization or public-boundary constraints. Review private and
public types; file size alone is not evidence of type cohesion.

For a large type, build a field-use and responsibility map. Identify fields
and methods that change together, independent state lifecycles, orchestration,
I/O, domain policy, caching, and synchronization responsibilities. Give each
candidate an explicit retain, split-module, decompose-type, extract-component,
or defer disposition with evidence.

Treat more than 12 fields, more than 15 methods, constructor arity above 8, or
more than three independently changing responsibilities as action thresholds
in modernize mode. Decompose the type or extract components unless evidence
shows it is a generated record, immutable schema/FFI mirror, flat lookup table,
or another genuinely single-purpose exceptional shape. “Coherent lifecycle,”
public compatibility, and “retain for this pass” are not sufficient exceptions
when several responsibilities or independent field clusters exist.

Preserve invariants, ownership, serde/FFI formats, and lock ordering through
boundary adapters or versioned wire types while improving the internal model.
Migrate in-repository construction and access sites, add focused tests, and run
the affected full gate. Record threshold counts before and after the change.
