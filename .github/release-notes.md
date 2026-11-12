## Install

No Python needed: the installer sets everything up and adds the `reviau` command. Run it again to upgrade.

**Windows**: open PowerShell and paste:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | iex"
```

**macOS and Linux**: open a terminal and paste:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

Already using Python? `uv tool install reviau` or `pip install reviau`. See the [README](https://github.com/biodiversica/reviau#installation) ([português](https://github.com/biodiversica/reviau/blob/main/README.pt-BR.md#instalação)).

Then run `reviau /path/to/segments`, or `reviau` alone to choose the folder in the browser.

## What's in this release

<!-- Write the highlights here before publishing. -->
