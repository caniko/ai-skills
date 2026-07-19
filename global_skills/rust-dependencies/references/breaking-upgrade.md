# Breaking Upgrade Profile

Inventory direct and transitive dependency versions, semver constraints,
feature flags, MSRV requirements, and upstream migration notes. Upgrade in
small compatible steps, resolve duplicate or conflicting versions, adapt APIs,
and test every affected feature/target. Keep the most compatible dependency
tree supported by repository policy; never claim an upgrade is complete while
the lockfile or generated artifacts are stale.

In Rust-ultra modernize mode, apply a breaking direct upgrade when it removes
unsupported code, fixes correctness or security risk, materially simplifies
the implementation, improves the type/API model, or is required by the active
toolchain. Migrate all in-repository callers and generated artifacts in the
same pass. Retain an older compatible version only with concrete cost/benefit
evidence; “breaking” by itself is not a retain reason.
