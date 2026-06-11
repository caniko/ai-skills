# Rust Crane Flake Patterns

Use these as starting points, then adapt to the crate. Keep Rust builds on crane.

## Standard rs-harbor Flake

```nix
{
  description = "Rust project";

  inputs = {
    rs-harbor.url = "github:caniko/rs-harbor";

    nixpkgs.follows = "rs-harbor/nixpkgs";
    rust-overlay.follows = "rs-harbor/rust-overlay";
    crane.follows = "rs-harbor/crane";
    flake-utils.follows = "rs-harbor/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    rs-harbor,
    flake-utils,
    rust-overlay,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [(import rust-overlay)];
      };

      toolchain = rs-harbor.lib.mkToolchain {inherit pkgs;};
      inherit (toolchain) craneLib;

      src = craneLib.cleanCargoSource ./.;

      commonArgs = {
        inherit src;
        strictDeps = true;
      };

      cargoArtifacts = craneLib.buildDepsOnly commonArgs;

      package = craneLib.buildPackage (commonArgs
        // {
          inherit cargoArtifacts;
        });
    in {
      packages.default = package;

      checks = {
        default = package;

        clippy = craneLib.cargoClippy (commonArgs
          // {
            inherit cargoArtifacts;
            cargoClippyExtraArgs = "--all-targets -- --deny warnings";
          });

        fmt = craneLib.cargoFmt {
          inherit src;
        };
      };

      devShells.default = craneLib.devShell {
        checks = self.checks.${system};
        packages = with pkgs; [
          cargo-nextest
          rust-analyzer
        ];
      };
    });
}
```

## rs-harbor Dev Shells And Cargo Config

Use this when cross shells or optimized Cargo config should be exposed.

```nix
      toolchain = rs-harbor.lib.mkToolchain {inherit pkgs;};
      inherit (toolchain) craneLib;
      cross = rs-harbor.lib.mkCross {
        inherit pkgs system;
        # macosSdkStorePath = "/nix/store/<stable-hash>-macosx-sdk-26.1";
        # osxSdkVersion = "26.1";
      };
      cargoConfig = rs-harbor.lib.mkCargoConfig {inherit pkgs;};
```

```nix
      packages.cargo-config = cargoConfig.configPath;

      devShells = rs-harbor.lib.mkDevShells {
        inherit pkgs cross cargoConfig;
        inherit (toolchain) craneLib;
        checks = self.checks.${system};

        packages = with pkgs; [
          cargo-nextest
          rust-analyzer
        ];

        pkgConfigDeps = with pkgs; [
          # openssl
          # sqlite
        ];
      };
```

## Native Dependencies

Add native dependencies to both crane builds and dev shells. Keep `pkgConfigDeps` for libraries with `.pc` files.

```nix
      nativeBuildInputs = with pkgs; [
        pkg-config
        protobuf
      ];

      buildInputs = with pkgs; [
        openssl
        sqlite
      ];

      commonArgs = {
        inherit src buildInputs nativeBuildInputs;
        strictDeps = true;
      };
```

For runtime-loaded libraries during `cargo run` or tests:

```nix
      devShells = rs-harbor.lib.mkDevShells {
        inherit pkgs cross cargoConfig;
        inherit (toolchain) craneLib;
        pkgConfigDeps = buildInputs;
        packages = buildInputs ++ nativeBuildInputs;
        extraEnv = {
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath buildInputs;
        };
      };
```

## Workspace And Multiple Binaries

Build the workspace root by default. Add named packages for specific binaries when useful.

```nix
      myTool = craneLib.buildPackage (commonArgs
        // {
          inherit cargoArtifacts;
          cargoExtraArgs = "-p my-tool";
        });

      myServer = craneLib.buildPackage (commonArgs
        // {
          inherit cargoArtifacts;
          cargoExtraArgs = "-p my-server";
        });
```

```nix
      packages = {
        default = myTool;
        inherit myTool myServer;
      };
```

## Direct Crane Fallback

Use this only when rs-harbor is inappropriate for the repo.

```nix
{
  description = "Rust project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    crane.url = "github:ipetkov/crane";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    crane,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};
      craneLib = crane.mkLib pkgs;
      src = craneLib.cleanCargoSource ./.;

      commonArgs = {
        inherit src;
        strictDeps = true;
      };

      cargoArtifacts = craneLib.buildDepsOnly commonArgs;
      package = craneLib.buildPackage (commonArgs // {inherit cargoArtifacts;});
    in {
      packages.default = package;
      checks.default = package;
      checks.fmt = craneLib.cargoFmt {inherit src;};
      checks.clippy = craneLib.cargoClippy (commonArgs
        // {
          inherit cargoArtifacts;
          cargoClippyExtraArgs = "--all-targets -- --deny warnings";
        });

      devShells.default = craneLib.devShell {
        checks = self.checks.${system};
        packages = with pkgs; [
          cargo-nextest
          rust-analyzer
        ];
      };
    });
}
```
