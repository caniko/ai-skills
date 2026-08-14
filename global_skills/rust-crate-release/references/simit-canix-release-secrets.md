# Simit + Canix Release Secrets

Use this reference only when a simit-managed Rust release gets its Forgejo/Codeberg Actions inputs from canix `services.secretSync`.

## Flow

1. In the project being released, inspect simit's generic runtime contract:

   ```sh
   simit release secrets contract --json
   ```

2. In `/data/nvme0/can/canix`, verify that contract against canix declarations:

   ```sh
   canix release secrets check --project /path/to/project
   ```

3. If the checker reports a missing required credential, fix the upstream canix declaration or source artifact first. Do not copy Codeberg secret values from the UI; Codeberg does not expose secret values back.

4. If a single declared target needs repair, use targeted sync:

   ```sh
   canix secret sync --check --target <target-id>
   canix secret sync --target <target-id>
   ```

5. Rerun the canix checker, then regenerate/check the release workflow:

   ```sh
   simit init release --check --diff
   ```

## Scope Rules

- `simit` owns the generic names, kinds, contexts, and publisher channels required by the workflow.
- canix owns mapping those names to local age/plaintext sources and Codeberg user/repo/org scopes.
- Global/user credentials must not be duplicated into repo secrets unless a runtime visibility probe proves the forge does not expose them.
- Repo-specific credentials and public repo metadata should stay repo-scoped.
- Runner credentials, such as mounted Attic token files, are not managed by `secretSync`.

## Stop Conditions

Stop and report the missing producer when:

- The simit contract requires a credential with no canix `secretSync` target.
- A canix target points at a missing `.age` or plaintext source file.
- FIDO2/age decryption cannot materialize the source.
- The source exists but cannot be proven to match a committed public artifact, such as a minisign public key.
- A workflow runtime probe proves a declared user/global credential is not visible to the workflow.

For Codeberg CI log triage, load `../../forgejo-codeberg-ci/SKILL.md` and use `fj` first, with raw log endpoints only as a fallback.
