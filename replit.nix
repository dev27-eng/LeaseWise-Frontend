{pkgs}: {
  deps = [
    pkgs.nodePackages.prettier
    pkgs.postgresql
    pkgs.openssl
  ];
}
