{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    deno
    sqlite
    termdbms
    python312Packages.faker
  ];

  shellHook = ''
    echo "Deno development environment loaded!"
    echo "To start the webserver, use 'deno run --allow-net --allow-read --allow-write webserver.js'"
  '';
}
