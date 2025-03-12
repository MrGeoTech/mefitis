{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
    buildInputs = with pkgs.python312Packages; [
        w1thermsensor
        pyserial
    ] ++ [ pkgs.python312 ];
}
