# Ultra-System Failure Analysis

An ultra pass fails structurally when it can finish without proving that each
promised kind of review happened. More prompting or more agents does not fix
an unobservable completion predicate.

| Failure mode | Why it escaped | System invariant |
|---|---|---|
| One routed concern owned several profiles | Invoking the owner looked like coverage even when profiles were omitted | One registry row and one ledger row per profile |
| Lexical score suppressed qualitative review | Absence of a token was mistaken for absence of an architectural concern | Qualitative profiles always screen; scores only prioritize |
| Green builds stood in for design analysis | Technical gates prove compilability or tests, not cohesion or topology | No-change reviews require analytical evidence and a disposition |
| Structural concerns were unnamed | Trait hierarchy, behavioral duplication, and oversized types had no completion identity | Explicit trait-architecture, behavior-reuse, and type-cohesion profiles |
| Delegates returned prose summaries | The orchestrator could not compare requested and delivered coverage | Disjoint profile assignments and exact-cardinality receipts |
| Completion had no global ledger | Missing work was indistinguishable from clean work | Terminal success rejects absent, unreviewed, deferred, or blocked rows |
| Evidence was not tied to source state | A later edit could invalidate an earlier review silently | Registry hash and streaming source fingerprint validation |
| Parallel workers nested heavyweight commands | Agent fan-out multiplied Cargo, Nix, linker, and analyzer memory use | Bounded read-only agents, one heavy command, capped child-tool jobs |
| Iteration caps implied success | Automation stopping was confused with convergence | `incomplete-convergence-cap` is explicit and non-successful |

Subagents help only after the work has profile identity, disjoint ownership,
bounded execution, and machine-checkable receipts. The orchestrator remains
responsible for the coverage ledger and final source-bound validation.
