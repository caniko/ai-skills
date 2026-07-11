# Application Security Profile

Run `cargo audit` and inspect advisories, dependency changes, and repository
policy. Review command construction, path traversal, untrusted input, crypto,
hard-coded secrets, and secret lifetime.

- Never pass secrets as CLI flags; use files, environment variables, or a
  secret manager.
- Zeroize decrypted/generated secret buffers on success and every error path.
- Prefer a single AEAD-encrypted container over hand-rolled unauthenticated
  headers and payload formats.
- Keep credentials, tokens, and sensitive identifiers out of logs and errors.

Commit dependency updates only when the active workflow owns commits. Add
comments for findings that require maintainer decisions. Run the project test
gate after repairs.
