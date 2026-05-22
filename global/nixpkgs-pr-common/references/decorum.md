# Nixpkgs PR Decorum

## Scope and reviewability

- Keep PRs narrowly scoped to one package, module, update, or bug fix.
- Explain why the change is needed when the reason is not obvious from the title.
- Do not open duplicate PRs. Search open and recently closed PRs before publishing.
- Prefer draft PRs until local validation and review workflow status are reflected in the PR body.
- Stage explicit paths only; never sweep unrelated dirty work into a nixpkgs PR.

## Commit and PR style

- Use a concise nixpkgs-style title, for example `pname: old -> new` or `openrazer: fix build with newer hid_report_raw_event API`.
- Do not put a period at the end of the commit summary line.
- Put maintainer-facing context in the PR summary: what changed, why, upstream references, and validation status.
- Check only PR-template boxes that are already true.

## Missing required data

If a foundational input is missing, stop and report:

- the missing artifact or source;
- why it is required;
- the upstream producer or owner to fix it;
- the exact command or workflow to regenerate it;
- the validation command that proves it is fixed.
