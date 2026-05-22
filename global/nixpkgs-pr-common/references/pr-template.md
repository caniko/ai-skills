# Nixpkgs PR Template

Always fetch the current nixpkgs PR template before creating or updating a PR body:

```bash
gh api repos/NixOS/nixpkgs/contents/.github/PULL_REQUEST_TEMPLATE.md \
  -H 'Accept: application/vnd.github.raw+json'
```

Write the body in two parts:

1. A short human summary above the template with what changed, why it changed, upstream links, review notes, and validation status.
2. The live template filled truthfully.

Checklist rules:

- Check only boxes supported by completed validation.
- If `nixpkgs-review-gha` is running, leave `Ran nixpkgs-review` unchecked and include the run URL in the summary.
- After a successful review run, update the body and check the `Ran nixpkgs-review` box.
- Do not use cached or remembered template text when publishing upstream.
