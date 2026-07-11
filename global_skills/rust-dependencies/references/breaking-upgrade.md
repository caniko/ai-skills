# Breaking Upgrade Profile

Inventory direct and transitive dependency versions, semver constraints,
feature flags, MSRV requirements, and upstream migration notes. Upgrade in
small compatible steps, resolve duplicate or conflicting versions, adapt APIs,
and test every affected feature/target. Keep the most compatible dependency
tree supported by repository policy; never claim an upgrade is complete while
the lockfile or generated artifacts are stale.
