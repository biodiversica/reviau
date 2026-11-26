#!/bin/sh
# Install reviau and a launcher for its browser interface, on macOS or Linux.
#
#   curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
#
# Installs uv if it is missing (uv brings its own Python, so none is needed
# beforehand), installs reviau as an isolated tool, with the reviau command on
# the PATH, and adds a launcher that opens the interface. Run it again to
# upgrade.
#
# To uninstall, run it with REVIAU_UNINSTALL set:
#
#   curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | REVIAU_UNINSTALL=1 sh
#
# Either way, it says what it is about to do and asks before doing any of it.
#
# Environment overrides:
#   REVIAU_PACKAGE    what to install   (default: reviau)
#   REVIAU_UNINSTALL  1 removes reviau and its launcher. Reviewed segments and
#                     their reviau/ folders are never removed, nor is uv.
#   REVIAU_YES=1      go ahead without asking, e.g. from a script or CI
set -eu

PACKAGE="${REVIAU_PACKAGE:-reviau}"
UNINSTALL="${REVIAU_UNINSTALL:-}"
# The version CI tests the installer on.
PYTHON=3.12

say() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# Ask before going on, unless REVIAU_YES=1. $1 is what to say if the answer is
# no, $2 what is being done, for the message when there is no one to ask.
confirm() {
  if [ "${REVIAU_YES:-}" = 1 ]; then return 0; fi
  # Asked of the terminal: under "curl ... | sh" standard input is the script.
  if ! (: </dev/tty) 2>/dev/null; then
    die "there is no terminal to ask in; set REVIAU_YES=1 to $2 without asking."
  fi
  printf 'Continue? [y/N] '
  read -r ANSWER </dev/tty || ANSWER=
  case "$ANSWER" in
    [yY] | [yY][eE][sS]) ;;
    *) echo "$1"; exit 0 ;;
  esac
}

case "$(uname -s)" in
  Darwin) OS=macos ;;
  Linux) OS=linux ;;
  *) die "unsupported system $(uname -s); on Windows use install.ps1." ;;
esac

if command -v uv >/dev/null 2>&1; then
  UV=$(command -v uv)
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
else
  UV=
fi

# Where the launcher goes, and where its icon is copied to (Linux).
if [ "$OS" = macos ]; then
  LAUNCHER="$HOME/Desktop/reviau.command"
else
  APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  LAUNCHER="$APPS/reviau.desktop"
  ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
fi

# ── uninstall ────────────────────────────────────────────────────────────────
remove() {
  if [ -e "$1" ]; then
    rm -rf "$1"
    say "Removed $2 ($1)"
  fi
}

if [ -n "$UNINSTALL" ]; then
  [ "$UNINSTALL" = 1 ] || die "REVIAU_UNINSTALL must be 1, not '$UNINSTALL'."
  cat <<EOF
This uninstalls reviau. It will:

  - remove reviau, with uv (uv itself stays)
  - remove the launcher, $LAUNCHER

Segments, and the reviau/ folders that hold their reviews, are not removed.

EOF
  confirm "Nothing was removed." uninstall

  if [ -n "$UV" ] && "$UV" tool list 2>/dev/null | grep -q '^reviau '; then
    say "Uninstalling reviau"
    "$UV" tool uninstall reviau
  fi
  remove "$LAUNCHER" launcher
  if [ "$OS" = linux ]; then
    remove "$ICONS/scalable/apps/reviau.svg" icon
    remove "$ICONS/512x512/apps/reviau.png" icon
  fi
  say "Done. reviau is uninstalled."
  cat <<EOF

  Segments and their reviews were left where they are.
EOF
  exit 0
fi

# ── confirmation ─────────────────────────────────────────────────────────────
if [ "$OS" = macos ]; then
  LAUNCHER_TEXT="reviau.command on your Desktop, with its icon"
else
  LAUNCHER_TEXT="a reviau entry in your applications menu, with its icon"
fi
if [ -n "$UV" ]; then
  UV_TEXT="use uv, already installed at $UV"
else
  UV_TEXT="install uv, the tool that installs reviau, into ~/.local/bin"
fi
cat <<EOF
This installs reviau, a tool for reviewing folders of audio segments in the
browser. It will:

  - $UV_TEXT
  - install $PACKAGE with uv, isolated, along with a Python $PYTHON
    of its own; your other Pythons are not touched (if reviau is already
    installed, it is upgraded)
  - add uv's tools folder to your PATH, in your shell's startup file
  - add $LAUNCHER_TEXT

EOF
confirm "Nothing was installed." install

# ── uv ───────────────────────────────────────────────────────────────────────
if [ -z "$UV" ]; then
  say "Installing uv"
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$HOME/.local/bin" sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$HOME/.local/bin" sh
  else
    die "neither curl nor wget is available to download uv."
  fi
  UV="$HOME/.local/bin/uv"
fi

# ── reviau ───────────────────────────────────────────────────────────────────
say "Installing $PACKAGE"
"$UV" tool install --python "$PYTHON" --upgrade "$PACKAGE"
"$UV" tool update-shell >/dev/null 2>&1 || true
EXE="$("$UV" tool dir --bin)/reviau"
[ -x "$EXE" ] || die "reviau was not installed where uv said it would be ($EXE)."

# The logo, from the tool's environment (scripts/make_icons.py). A package from
# before the logo has none, and the launcher then keeps the default icon.
ICON_DIR=
for dir in "$("$UV" tool dir)"/reviau/lib/python*/site-packages/reviau/web/icons; do
  if [ -f "$dir/reviau.png" ]; then ICON_DIR="$dir"; fi
done

# ── launcher ─────────────────────────────────────────────────────────────────
# Both open a terminal: it shows the address and is where Ctrl+C stops the
# interface. They start in the home folder, where Browse… begins, with no
# folder open: the reviewer chooses one in the browser.
if [ "$OS" = macos ]; then
  mkdir -p "$HOME/Desktop"
  cat > "$LAUNCHER" <<EOF
#!/bin/sh
cd "\$HOME" && exec "$EXE"
EOF
  chmod +x "$LAUNCHER"
  # A .command file has no icon setting of its own; Finder shows the one
  # attached to the file, which keeps its own copy of the image.
  if [ -n "$ICON_DIR" ]; then
    osascript -l JavaScript -e '
      function run(argv) {
        ObjC.import("AppKit");
        var image = $.NSImage.alloc.initWithContentsOfFile(argv[0]);
        $.NSWorkspace.sharedWorkspace.setIconForFileOptions(image, argv[1], 0);
      }' "$ICON_DIR/reviau.png" "$LAUNCHER" >/dev/null 2>&1 || true
  fi
  WHERE="double-click reviau on your Desktop"
else
  mkdir -p "$APPS"
  # Copied into the user's icon theme, which the launcher names: the tool's
  # environment may be rebuilt on an upgrade.
  ICON=audio-x-generic
  if [ -n "$ICON_DIR" ]; then
    mkdir -p "$ICONS/scalable/apps" "$ICONS/512x512/apps"
    cp "$ICON_DIR/reviau.svg" "$ICONS/scalable/apps/reviau.svg"
    cp "$ICON_DIR/reviau.png" "$ICONS/512x512/apps/reviau.png"
    touch "$ICONS"  # so menus notice the theme changed
    ICON=reviau
  fi
  cat > "$LAUNCHER" <<EOF
[Desktop Entry]
Type=Application
Name=reviau
Comment=Review folders of audio segments in the browser
Exec="$EXE"
Path=$HOME
Terminal=true
Icon=$ICON
Categories=Science;AudioVideo;
EOF
  WHERE="open reviau from your applications menu"
fi

say "Done. $("$EXE" --version 2>/dev/null || echo reviau) is installed."
cat <<EOF

  To start: $WHERE, and choose the folder of
  segments in the browser. Or, in a new terminal:

    reviau /path/to/segments

  'reviau --help' lists every option.
  To upgrade later, run this installer again.
EOF
