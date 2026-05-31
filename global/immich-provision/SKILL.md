---
name: immich-provision
description: Use when working on the immich-provision project, declarative Immich user provisioning, Immich/Kanidm OIDC migrations, or NixOS modules that manage Immich identity. Enforces the patched-only short-lived provisioning-token model, Kanidm-derived users, declarative OAuth config, and conservative handling of existing photo-library accounts.
---

# immich-provision

Use this skill for the `immich-provision` project and for canix-style Immich OIDC
identity work.

## Rules

- Use patched-only provisioning. Do not add or recommend long-lived Immich admin
  API keys.
- Obtain admin authority through patched `immich-admin provision-token --ttl N`
  and pass the token by a private runtime file or pipe, never a Nix store path.
- Keep OAuth settings declarative through `services.immich.settings.oauth` or
  `services.immich.provision.oauth`.
- Derive internal users from `services.kanidm.provision.persons` with
  `immich-provision.lib.usersFromKanidmPersons` when Kanidm is present.
- Match users by normalized email. Never pre-set or rewrite `oauthId`; Immich
  links the first OIDC login to an existing matching-email user.
- Treat existing Immich libraries as high-value state. Do not delete users,
  storage labels, quotas, or account bindings without explicit proof and the
  double-delete lock.

## Workflow

1. Inspect current Immich version, NixOS `services.immich.settings`, and Kanidm
   person/group declarations before editing.
2. For project work, edit the Rust CLI, `nix/module.nix`, `nix/lib.nix`, RFC,
   and Immich patch together so semantics stay aligned.
3. For canix adoption, add only the consumer wiring: patched Immich package,
   shared OIDC secret, `services.kanidm.provision.systems.oauth2.immich`, and
   `services.immich.provision`.
4. Verify with:

   ```sh
   cargo test
   nix flake check --no-build
   nix flake check
   ```

5. If full Immich patch tests cannot run locally, state that explicitly and
   include the exact Immich checkout command sequence needed.

## Invariants

- User create requests omit both `password` and `oauthId`.
- User deletion requires both CLI `--allow-user-delete` and per-user
  `delete.force = true`.
- OAuth email-link behavior must be validated before migrating accounts with
  existing libraries.
