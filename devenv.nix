{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  packages = with pkgs; [
    git
  ];
  starship.enable = true;
  languages.python = {
    enable = true;
    version = "3.12";
    uv = {
      enable = true;
      sync = {
        enable = true;
        allExtras = true;
        allGroups = true;
      };
    };
  };
}
