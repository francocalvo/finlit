{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-23.05";
    flake-utils.url = "github:numtide/flake-utils";

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs =
    { self
    , nixpkgs
    , flake-utils

    , poetry2nix
    }: flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python311;

      builder = poetry2nix.legacyPackages.${system}.mkPoetryApplication;
    in
    {
      packages.default = builder {
        inherit python;

        projectDir = ./.;
      };

      devShells.default = pkgs.mkShell {
        nativeBuildInputs = [
          python
        ] ++ (with python.pkgs; [
          black
          pip
          pytest
          pytest-cov
        ]) ++ (with pkgs; [
          engage
          nixpkgs-fmt
          poetry
          pyright
          ruff
        ]) ++ (with pkgs.nodePackages; [
          markdownlint-cli
        ]);

        NIX_PYTHON_SITE_PACKAGES = python.sitePackages;
      };

      checks = {
        packagesDefault = self.packages.${system}.default;
        devShellsDefault = self.devShells.${system}.default;
      };
    });
}
