{
  description = "caniko's AI skills mirror";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.follows = "skillnet/flake-utils";
    skillnet = {
      # CI environments without Codeberg SSH credentials can switch this to:
      # git+https://codeberg.org/caniko/skillnet.git?rev=3d35951a3de622fa6995c4ddb681e9d4efc26ea3
      url = "git+ssh://git@codeberg.org/caniko/skillnet.git?rev=3d35951a3de622fa6995c4ddb681e9d4efc26ea3";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    skillnet,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        skillnetPackage = skillnet.packages.${system}.skillnet;
      in {
        packages.default = skillnetPackage;
        packages.skillnet = skillnetPackage;

        apps.default = {
          type = "app";
          program = "${skillnetPackage}/bin/skillnet";
        };

        devShells.default = skillnet.devShells.${system}.default;
      }
    )
    // {
      hmModules.default = {...}: {
        # Downstream ai-skills HM importers get skillnet wiring without an extra import.
        imports = [
          skillnet.hmModules.default
        ];
      };
    };
}
