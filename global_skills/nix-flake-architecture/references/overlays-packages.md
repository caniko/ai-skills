# Overlay and Package Profile

Map overlays, local packages, package-set variants, `callPackage` arguments,
and `overrideAttrs` chains. Keep overlays small and purpose-specific; prefer
explicit `callPackage` parameters, structured build inputs, and package-set
provenance over global host-only overlays.

Preserve metadata in `overrideAttrs`, do not replace cache-sensitive
`legacyPackages` casually, and keep GPU/CUDA/ROCm package sets separate when
the repository models them separately. Evaluate or build the affected package
derivation as appropriate.
