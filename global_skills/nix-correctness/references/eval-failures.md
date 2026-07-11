# Evaluation Failure Profile

Capture the exact failing command and classify the trace: missing attribute,
option conflict, type mismatch, assertion, bad import, infinite recursion,
missing generated/secret artifact, or broken flake output. Read every source
definition named by the trace before editing and inspect option declarations
with `rg`/focused `nix eval`.

Correct the producer of the invalid value. Prefer source data or option wiring
over broad `mkForce`, `or null`, or `or {}` fallbacks. Rerun the original
command and one adjacent focused eval. If a generated or rekeyed artifact is
missing, report its producer and regeneration/validation commands instead of
creating a substitute.
