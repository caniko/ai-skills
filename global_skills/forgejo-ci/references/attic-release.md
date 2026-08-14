# Attic Publication

Issue trusted-runner credentials through canix:

```sh
cd /data/nvme0/can/canix
canix cache token onboard <project> --runner atlas
agenix rekey -a
canix rebuild switch atlas
```

The workflow reads `$ATTIC_TOKENS_DIR/<project>` and must never expose the
token to pull-request jobs. Gate publication on protected trunk/tag refs and
use `atlas-nix-trusted` only when the job writes the host Nix store.

If the project uses an external runner, follow that runner's documented secret
path instead of copying the self-hosted template. Validate the actual package
targets before pushing them.
