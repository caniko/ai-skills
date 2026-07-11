# Type Safety Profile

Make illegal states harder to represent: wrap domain primitives in newtypes,
use enums instead of fixed string sets or boolean flags, use typestates for
multi-step state machines, prefer borrowed or copy-on-write inputs when
ownership is unnecessary, and choose static dispatch when the concrete type is
known.

Do not refactor public serialization boundaries or introduce a newtype merely
for style. Preserve behavior and compile frequently.
