# Installation

*English · [Português (Brasil)](../pt-BR/installation.md)*

**Without Python.** The installer sets up everything required, adds the
`reviau` command and a **reviau** shortcut that opens the interface. Running it
again upgrades the installation.

On Windows, open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex"
```

On macOS and Linux, open a terminal and run:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

The installer first lists what it is going to do and asks for confirmation
before changing anything. It then performs the following steps:

1. Installs [uv](https://docs.astral.sh/uv/) into `~/.local/bin` if it is not
   already present. uv downloads its own Python, so no prior installation is
   required, and any existing Python installation is left unchanged.
2. Runs `uv tool install --python 3.12 reviau`, which installs the tool in an
   isolated environment and adds `reviau` to the PATH. The command becomes
   available in terminals opened after the installation.
3. Adds a **reviau** launcher, with the `(| |)` logo as its icon: a Desktop and
   Start menu shortcut on Windows, `reviau.command` on the macOS Desktop, and
   an applications menu entry on Linux. The launcher runs `reviau` in the home
   folder with no segments folder open, so the folder is chosen in the browser
   (see [Opening a Folder](reviewing.md#opening-a-folder)). It also opens a
   terminal window next to the browser. This window runs the interface, and
   closing it (or pressing Ctrl+C) stops it.

Two environment variables change the installer's behaviour: `REVIAU_PACKAGE`
(what to install, for example a specific version such as `reviau==0.1.0`) and
`REVIAU_YES=1`, which skips the confirmation, for installing or uninstalling
from a script.

**Uninstalling.** Run the installer again with `REVIAU_UNINSTALL` set. It
lists what it is going to remove and asks for confirmation first. On Windows,
close the reviau window first, then run in PowerShell:

```powershell
$env:REVIAU_UNINSTALL=1; irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex
```

On macOS and Linux:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | REVIAU_UNINSTALL=1 sh
```

This removes reviau, its launcher and the launcher's icon. Segments, and the
`reviau/` folders that hold their reviews, are never removed. A plain
`uv tool uninstall reviau` removes only the program, leaving a launcher that no
longer works: delete it by hand (on Windows, **reviau** on the Desktop and in
the Start menu).

**What uninstalling leaves behind.** reviau's own environment, with every
Python package installed for it, is removed, together with the `reviau`
command. What it was installed with stays, since the uninstaller cannot tell
whether anything else uses it:

| Left in place | Where | Why |
|---|---|---|
| uv | `~/.local/bin/uv` and `uvx` (`.exe` on Windows) | Other programs may use it. |
| Python 3.12 | `uv python dir` | uv's own Python, which other uv tools may use. If a Python 3.12 was already installed, uv used it and downloaded none. |
| uv's download cache | `uv cache dir` | Shared by everything uv installs. It holds the downloaded packages, which for reviau come to several hundred MB, llvmlite and scipy the largest. |
| Segments and their `reviau/` folders | | Reviews are never removed. |
| Interface settings | The browser | Language, theme, spectrogram view and recent folders are kept by the browser, which clears them with the site's data. |

If nothing else on the machine uses uv, the rest can be removed by hand after
uninstalling:

```bash
uv cache clean                # every downloaded package
uv python uninstall 3.12      # uv's Python, if it downloaded one
```

and then uv itself, by deleting `uv` and `uvx` from `~/.local/bin`.

**With uv or pip.** reviau is published on PyPI and requires Python 3.10 or
later:

```bash
uv tool install reviau   # as an isolated command-line tool
pip install reviau       # or with pip, into the current environment
```

`uv tool upgrade reviau` upgrades and `uv tool uninstall reviau` uninstalls.
It can also be run once, without a permanent installation, with
`uvx reviau /path/to/segments`. Installed this way, reviau adds no launcher.

The audio libraries (librosa and soundfile) depend on `libsndfile`, which is
included in their wheels for Linux, macOS and Windows.

To work on reviau itself, see [Development](development.md).
