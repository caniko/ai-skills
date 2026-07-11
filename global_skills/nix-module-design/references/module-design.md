# Module Design Profile

Map module inputs, imports, option namespaces, defaults, and config fragments.
Move reusable behavior into modules and reusable data into pure sources or
lib helpers. Keep host/user decisions at host/profile layers.

Prefer `mkIf cfg.enable` around coherent config fragments and `mkMerge` for
independent conditionals. Avoid nested merges that obscure ownership and keep
`mkForce` only where a real upstream/default conflict is documented. Do not
create a second engine for an upstream module capability. Keep NixOS and Home
Manager concerns separate unless integrated Home Manager needs `osConfig`.
