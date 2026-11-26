# Installation

*English · [Português (Brasil)](../pt-BR/installation.md)*

**Without Python.** The installer sets up everything required and adds the
`reviau` command. Running it again upgrades the installation.

On Windows, open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | iex"
```

On macOS and Linux, open a terminal and run:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

The installer performs the following steps:

1. Installs [uv](https://docs.astral.sh/uv/) into `~/.local/bin` if it is not
   already present. uv downloads its own Python, so no prior installation is
   required, and any existing Python installation is left unchanged.
2. Runs `uv tool install --python 3.12 reviau`, which installs the tool in an
   isolated environment and adds `reviau` to the PATH.

The command becomes available in terminals opened after the installation. The
environment variable `REVIAU_PACKAGE` changes what the installer installs (for
example, a specific version such as `reviau==0.1.0`). To uninstall, run
`uv tool uninstall reviau`.

**With uv or pip.** reviau is published on PyPI and requires Python 3.10 or
later:

```bash
uv tool install reviau   # as an isolated command-line tool
pip install reviau       # or with pip, into the current environment
```

`uv tool upgrade reviau` upgrades the tool. It can also be run once, without a
permanent installation, with `uvx reviau /path/to/segments`.

The audio libraries (librosa and soundfile) depend on `libsndfile`, which is
included in their wheels for Linux, macOS and Windows.

To work on reviau itself, see [Development](development.md).
