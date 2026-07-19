# Trait Architecture Profile

Inventory every local trait, supertrait edge, implementation, blanket
implementation, default method, associated type, and trait-object use. Record
required/default method counts, implementor count, object-safety, public or
sealed extension-point status, and concrete consumers that use only a subset
of an API. Produce a trait-topology table even when no edit is warranted.

Find duplicated behavior, type-tag dispatch, concrete coupling, fat traits,
no-op optional methods, and identical implementations. Give every candidate
an explicit retain, split, default-method, blanket-implementation,
dependency-inversion, or defer disposition. Absence of local traits is not a
clean result by itself: inventory concrete external-system, storage, runtime,
codec, backend, and policy boundaries. Extract a minimal trait when there are
multiple production implementations, a production implementation plus a real
test/fake adapter, or a documented extension point. Prefer enums, generics, or
composition when dynamic polymorphism adds no useful substitution boundary.

In modernize mode, alter downstream trait contracts when the improvement is
material and migrate in-repository implementations and callers. Version or
adapt plugin, serialization, and FFI boundaries rather than letting them freeze
the internal model. Compile after each extraction, test trait contracts, and
report the final topology and unresolved candidates.
