# Test Gates Profile

Inventory formatter checks, flake checks, CI, pre-commit hooks, host evals,
package builds, activation assertions, and deployment commands. Add focused
checks for invariants that can be proven cheaply with grep, pure assertions,
or small derivations. For touched NixOS hosts, prefer toplevel drv-path evals;
for Home Manager and packages, evaluate the affected output.

Run the new check plus the narrow evals it protects. If it depends on a
generated secret or artifact, document its producer and regeneration command.
