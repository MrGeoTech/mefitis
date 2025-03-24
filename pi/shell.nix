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
        ps.lgpio # Yes I know, three gpio packages. Just need to get this done. TODO: Remove two of them
        ps.gpiozero 
        ps.rpi-gpio
    ]))];

    shellHook = ''
        echo "Environment initialized!"
        echo "To start, run './run.sh'"
    '';
}
