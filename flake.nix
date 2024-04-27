{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-unstable";

    # flake-utils
    systems.url = "github:nix-systems/x86_64-linux";
    flake-utils.url = "github:numtide/flake-utils";
    flake-utils.inputs.systems.follows = "systems";

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, systems, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; })
          mkPoetryApplication;

        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true; # Propietary software
        };

        python = pkgs.python312;

        app = mkPoetryApplication {
          inherit python;
          preferWheels = true;
          projectDir = self;
        };
      in {

        packages.default = app;

        devShells.default = pkgs.mkShell {
          nativeBuildInputs = [ python ]
            ++ (with python.pkgs; [ black pip pytest pytest-cov ])
            ++ (with pkgs; [
              engage
              nixpkgs-fmt
              poetry
              pyright
              nodejs-slim
              beancount
              pgcli
            ]) ++ (with pkgs.nodePackages; [ markdownlint-cli ]);

          NIX_PYTHON_SITE_PACKAGES = python.sitePackages;

          # pkgs.iconv
          # pkgs.glibc
          # pkgs.pythonManylinuxPackages.manylinux2014Package
          shellHook = ''
            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath [ pkgs.zlib ]
            }:$LD_LIBRARY_PATH"

            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH"
          '';
        };
      });
}
