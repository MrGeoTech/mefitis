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
        # Yes I know, two gpio packages. Just need to get this done. TODO: Clean up
        ps.gpiozero 
        ps.rpi-gpio
        ps.numpy
    ]))];

    shellHook = ''
        echo "Dev environment initialized!"
        echo "To start, run './run.sh'"
    '';
}
