## Install

No Python needed: the installer sets everything up and adds the `reviau` command and a **reviau** shortcut that opens the interface. It says what it will do and asks first. Run it again to upgrade.

**Windows**: open PowerShell and paste:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex"
```

**macOS and Linux**: open a terminal and paste:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | sh
```

Already using Python? `uv tool install reviau` or `pip install reviau`. See the [README](https://github.com/biodiversica/reviau#installation) ([português](https://github.com/biodiversica/reviau/blob/main/README.pt-BR.md#instalação)).

Then open **reviau** from the shortcut and choose the folder in the browser, or run `reviau /path/to/segments`. To uninstall, see the [README](https://github.com/biodiversica/reviau#installation).

## What's in this release

<!-- Write the highlights here before publishing. -->
