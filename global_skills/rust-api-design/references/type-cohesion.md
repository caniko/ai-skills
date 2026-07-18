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
more than three independently changing responsibilities as review triggers,
not automatic refactoring rules. Preserve invariants, ownership, serde/FFI
formats, public compatibility, and lock ordering. Add focused tests for any
decomposition and run the affected full gate.
