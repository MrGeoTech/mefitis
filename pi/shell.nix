{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
    buildInputs = with pkgs; [
        deno
        termdbms
    ] ++ [(pkgs.python312.withPackages (ps: [
        ps.faker
        ps.w1thermsensor
        ps.pyserial
        ps.psycopg2
        ps.gpiozero
    ]))];

    shellHook = ''
        echo "Environment initialized!"
        echo "To start, run './run.sh'"
    '';
}
