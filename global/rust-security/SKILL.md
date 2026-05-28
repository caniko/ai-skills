---
name: rust-security
description: Run a security audit on a Rust project — dependency vulnerabilities plus code-level anti-patterns. Use when asked to check for CVEs in dependencies, run cargo audit, find hardcoded secrets, insecure crypto, unvalidated command input, or path traversal. (Unsafe-block soundness, UB hunting, and SAFETY comments live in rust-unsafe-soundness.) Extracted from the yee-haw housekeeping catalog (ConcernId::Security).
---

# Rust: Security Audit

Run a security audit on the project:
1. Check for known vulnerabilities in dependencies
2. For each vulnerability found:
   - If a patched version exists, update to it
   - If no patch exists, document the vulnerability and assess the risk
3. Check for common security anti-patterns in the code:
   - Hardcoded secrets or credentials
   - Use of insecure cryptographic functions
   - Unvalidated user input passed to system commands
   - Path traversal vulnerabilities
4. Commit any dependency updates. Add comments for code-level findings that need attention.

## Rust specifics

Run `cargo audit` to check for known vulnerabilities in dependencies.
If `cargo audit` is not installed, note that it should be installed but proceed with code review.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **6**
as "relevant":

| Pattern | Weight |
|---|---|
| `unsafe ` | 3 |
| `transmute` | 5 |
| `Command::new` | 2 |
| `from_raw` | 4 |
| `as *const` | 3 |
| `as *mut` | 3 |
| `std::ptr::` | 3 |
| `libc::` | 2 |
