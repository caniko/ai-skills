# Unsafe Soundness Profile

Inventory every unsafe block and record validity, alignment, initialization,
exclusive-access, lifetime, ABI, and thread-safety invariants. Confirm a safe
API cannot express the operation first.

Check transmutes and invalid bit patterns, aliasing `&mut`, `MaybeUninit`, raw
pointer bounds/alignment, `get_unchecked`, dangling pointers, FFI ownership
and null handling, panic unwinding across FFI, and handwritten `Send`/`Sync`.
Add a `// SAFETY:` comment naming the invariants directly above retained
unsafe code. If callers must uphold a precondition, expose it as `unsafe fn`
and document `# Safety` requirements. Run compile/tests and Miri where
available.
