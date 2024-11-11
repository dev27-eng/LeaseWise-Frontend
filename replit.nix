{pkgs}: {
  deps = [
    pkgs.file
    pkgs.zlib
    pkgs.tk
    pkgs.tcl
    pkgs.openjpeg
    pkgs.libxcrypt
    pkgs.libwebp
    pkgs.libtiff
    pkgs.libjpeg
    pkgs.libimagequant
    pkgs.lcms2
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.gdk-pixbuf
    pkgs.cairo
    pkgs.stripe-cli
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
