# Trait Architecture Profile

Inventory every local trait, supertrait edge, implementation, blanket
implementation, default method, associated type, and trait-object use. Record
required/default method counts, implementor count, object-safety, public or
sealed extension-point status, and concrete consumers that use only a subset
of an API. Produce a trait-topology table even when no edit is warranted.

Find duplicated behavior, type-tag dispatch, concrete coupling, fat traits,
no-op optional methods, and identical implementations. Give every candidate
an explicit retain, split, default-method, blanket-implementation,
dependency-inversion, or defer disposition. Extract a minimal trait only when
it has multiple meaningful implementations or is a documented extension
point.

Do not alter plugin, serialization, FFI, or downstream trait contracts
casually. Mark would-be breaking changes. Compile after each extraction, test
trait contracts, and report the final topology and unresolved candidates.
