{
  description = "caniko's AI skills mirror";

  inputs = {
    skillnet.url = "path:~/canix/Projects/skillnet";
    nixpkgs.follows = "skillnet/nixpkgs";
    flake-utils.follows = "skillnet/flake-utils";
  };

  outputs = {
    self,
    skillnet,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      skillnetPackage = skillnet.packages.${system}.skillnet;
    in {
      packages.default = skillnetPackage;
      packages.skillnet = skillnetPackage;

      apps.default = {
        type = "app";
        program = "${skillnetPackage}/bin/skillnet";
      };

      devShells.default = skillnet.devShells.${system}.default;
    });
}
