# Behavioral Duplication Profile

Find repeated behavior across functions, inherent implementations, trait
implementations, match arms, parsing, validation, conversions, builders,
orchestration, and test infrastructure. Use normalized textual similarity to
find candidates, then inspect semantic duplication that token matching misses.

For every cluster, record all locations, meaningful differences, invariants,
and an explicit disposition: extract helper, compose a shared component, use a
default method or blanket implementation, introduce a macro only for genuinely
syntactic repetition, retain intentional duplication, reject as a false
positive, or defer with an owner. Do not force unrelated behavior through a
trait merely to reduce line count.

Keep production and test duplication distinct. Add focused behavioral tests
before non-trivial extraction, verify each cluster independently, then run the
full affected stage gate.
