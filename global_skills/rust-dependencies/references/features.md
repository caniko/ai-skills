# Feature-Flag Profile

Map every declared feature, `dep:` activation, optional dependency, and
`cfg(feature = ...)` use. Ensure features are additive, defaults are deliberate
and documented, optional dependencies are gated, feature names are not
misspelled, and no declared feature is a no-op. Test no-default, all-features,
and representative combinations. Treat default changes as compatibility
events. Keep docs.rs feature visibility accurate.
