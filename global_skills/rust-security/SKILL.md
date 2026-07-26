---
name: rust-security
description: Audit Rust dependencies and code for security vulnerabilities, unsafe-code soundness, secret handling, command injection, and memory-safety hazards. Use for focused security reviews or when rust-ultra routes safety concerns here.
---

# Rust Security

Load [foundation.md](../rust-ultra/references/foundation.md), then the
relevant profile:

- [security.md](references/security.md) for dependency and application
  security.
- [unsafe-soundness.md](references/unsafe-soundness.md) for unsafe blocks,
  FFI, UB, and `SAFETY` invariants.

Treat unresolved vulnerability findings, unsoundness, secret exposure, and
missing authoritative security input as blockers. Do not weaken a sound unsafe
abstraction merely to remove the `unsafe` keyword.
