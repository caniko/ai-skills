# Chaperone and Publishing Mode

Determine whether the current version is a repair of an already published
release (`simit release sync-up`) or a new semver release. Use repository tags,
Cargo version, changelog, Git diff, and registry state; do not guess. For a
new release, choose major/minor/patch from documented public changes.

Before publication, require clean release scope, package listing, dry-run,
trust checks, version/tag/changelog alignment, and the appropriate CI status.
For Codeberg/Forgejo, push the validated release commit and tag and let CI
publish. Continue through remote workflow diagnosis and external crates.io
verification unless a real remote, credential, network, registry, or policy
blocker prevents it.

Release commits and annotated tags must use factual structured summaries and
validation commands. Never move an existing published tag during cleanup.
Report hook installation, release action, commit/tag/push state, changelog,
checks, trust root, publication verification, fixes, and remaining blockers.
