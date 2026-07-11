# Retirement Rules

Use these bounded rules instead of replaying the historical lesson log.

## Evidence and preservation

- Verify versions, tags, APIs, feature flags, release commands, and CI claims
  against current manifests, workflows, source, tests, and generated output.
- Run `plan-progress-review` for active or recently executed plans. Checked
  boxes and phase existence are leads, not completion evidence.
- Preserve durable behavior, compatibility rules, invariants, runbooks, and
  maintainer guidance. Remove execution scaffolding, model/dispatch notes,
  phase sequencing, branch choreography, and stale framing.
- If an external gate is missing, retain the exact missing artifact, producer,
  regeneration workflow, and validation command in a stable operational home.

## Navigation and deletion

- Audit every published navigation tree before deleting a plan or directory.
- Retire completed siblings independently; keep partial, blocked, unknown, or
  explicitly deferred work visible or move it to an intentional follow-up home.
- Search both source and generated documentation for the retired slug, old
  paths, phase-era wording, and predecessor links. Rebuild generated docs before
  the final search when the repository commits them.
- Check tracking state before choosing `git rm` versus removal of an untracked
  in-session directory, and re-check it immediately before deletion.

## Verification edge cases

- A final verification phase does not prove that its named durable-doc rollup
  ran; grep the durable destination for the actual invariant.
- A green static audit is not a green runtime gate. Re-run the reproducible
  check after any out-of-band repair and before retirement.
- Retained research dossiers belong in a stable reference section; execution
  plans do not.
- Audit generated manifests and indexes as data. Remove stale existence claims
  for deleted datasets or outputs.
- Rewrite remaining “Phase N” prose into present-tense product behavior after
  the plan disappears.

## Maintenance

Only add a dated entry to `lessons.md` when a user explicitly requests a raw
historical journal. Normal improvements belong here as a replacement rule or in
`SKILL.md`, and must not create append-only growth.
