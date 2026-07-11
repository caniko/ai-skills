# Input Hygiene Profile

Map input families, follows edges, duplicate nixpkgs pins, path inputs, manual
pins, lock drift, and update blast radius. Classify each duplicate as an
intentional cache/compatibility pin, local-development input, or accidental
drift. Prefer follows when consumers can safely share a revision, but retain
separate pins when cache hashes, platform support, or upstream regressions
require them.

Treat committed path inputs as local-only unless policy says otherwise. Do not
update locks during validation unless input updating is explicitly requested.
