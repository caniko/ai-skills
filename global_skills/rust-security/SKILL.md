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
4. **Never pass secrets as CLI flags.** Command-line arguments are visible to other processes via `/proc/` and persist in shell history. Secrets should be read from config files, environment variables, or secret managers — never from `--secret` / `--key` / `--password` flags.
5. **Zeroize secret-bearing buffers after use, including on error paths.** Plaintext secret values (passwords, keys, tokens) that were decrypted, deserialized, or generated should be cleared from memory once they are no longer needed. Use `zeroize::Zeroize` or explicit `ptr::write_bytes` / `volatile` clearing. Ensure error-return paths also zeroize before propagating the error, not only the success path.
6. **Prefer AEAD-encrypted single-struct containers over manual on-disk formats.**  Instead of composing a file layout with a magic number, version bytes, a header, and a separate payload, encrypt the entire content (including version and metadata) as one AEAD ciphertext. Decryption then serves as the integrity check — there is no separate header to forge or validate. This eliminates a class of format-parsing bugs and reduces the attack surface.
7. **Check that decrypted/deserialized buffers containing secrets are zeroized at every exit point.**  If a buffer is returned and the caller is expected to zeroize it, verify the caller actually does. If the buffer is short-lived, zeroize it immediately after use. On error paths, also zeroize any partial output before returning the error.
8. Commit any dependency updates. Add comments for code-level findings that need attention.

## Rust specifics

Run `cargo audit` to check for known vulnerabilities in dependencies.
If `cargo audit` is not installed, note that it should be installed but proceed with code review.

For secret zeroization:
- Use `zeroize::Zeroize` on types that implement it, or `zeroize::Zeroizing<T>` wrappers.
- For raw buffers, use `std::ptr::write_volatile` or `zeroize_derive` to prevent the compiler from optimizing away the clear.
- Verify that the zeroize call is on the *exit path* — after all uses including error branches, not just after the success return.
- Check that `Drop` impls for secret-bearing types call `zeroize` or use `#[derive(Zeroable, ZeroizeOnDrop)]`.
- Audit that intermediate deserialization scratch buffers (e.g. `serde_json::from_slice` into a `String`-bearing struct) also get zeroized, even when the struct's own fields separately zeroize.

For AEAD over manual formats:
- The on-disk format should be a single serialized (JSON, bincode, etc.) struct encrypted under a single AEAD key — no separate magic/version/header bytes outside the ciphertext.
- Decryption failure IS the integrity check; there is no need for a separate magic-number or checksum layer.
- The plaintext struct can carry its own version/metadata fields; the AEAD authenticates them as part of the ciphertext.

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
