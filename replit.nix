{pkgs}: {
  deps = [
    pkgs.pango
    pkgs.harfbuzz
    pkgs.glib
    pkgs.ghostscript
    pkgs.fontconfig
    pkgs.nodePackages.prettier
    pkgs.postgresql
    pkgs.openssl
  ];
}
