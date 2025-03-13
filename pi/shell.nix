{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
    buildInputs = with pkgs; [
        deno
        sqlite
        termdbms
    ] ++ [(pkgs.python312.withPackages (ps: [
        ps.faker
        ps.w1thermsensor
        ps.pyserial
    ]))];

    shellHook = ''
        echo "Environment initialized!"
        echo "To start, run './run.sh'"
    '';
}
