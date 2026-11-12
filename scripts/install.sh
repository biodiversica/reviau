#!/bin/sh
# Install reviau on macOS or Linux.
#
#   curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
#
# Installs uv if it is missing (uv brings its own Python, so none is needed
# beforehand) and installs reviau as an isolated tool, with the reviau command
# on the PATH. Run it again to upgrade.
#
# Environment overrides:
#   REVIAU_PACKAGE   what to install   (default: reviau)
set -eu

PACKAGE="${REVIAU_PACKAGE:-reviau}"
# The version CI tests the installer on.
PYTHON=3.12

say() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Darwin | Linux) ;;
  *) die "unsupported system $(uname -s); on Windows use install.ps1." ;;
esac

# ── uv ───────────────────────────────────────────────────────────────────────
if command -v uv >/dev/null 2>&1; then
  UV=$(command -v uv)
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
else
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

say "Done. $("$EXE" --version 2>/dev/null || echo reviau) is installed."
cat <<EOF

  Open a new terminal and run, for example:

    reviau /path/to/segments

  The review interface opens in a web browser. Run 'reviau' alone to choose
  the folder from the interface instead.
  'reviau --help' lists every option.
  To upgrade later, run this installer again.
EOF
