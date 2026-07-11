# Module Layout Profile

Measure every `.nix` file. Split files over 500 lines by cohesive
responsibility and merge files under 30 lines only when they are not useful
module entry points or independent toggles. Preserve import paths or update
all imports in one focused change, keep public outputs/options stable, and
never split generated hardware or disk files solely because they are long.

Keep incident-learned operational comments with the code they explain. Run
the formatter and a focused eval after every structural move.
