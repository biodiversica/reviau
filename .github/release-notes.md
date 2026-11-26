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

**Windows: use the new install command.** It now ends in `| Out-String | iex`, as above. The 0.1.0 command, `irm … | iex`, makes Windows PowerShell 5.1 run the installer line by line, which fails on its first multi-line block; if it did not work for you, this is why. Upgrade with the new command, which CI now runs exactly as the README writes it.

**A reviau shortcut, with its own icon.** The installer now adds a launcher with the new `(| |)` logo: a Desktop and Start menu shortcut on Windows, `reviau.command` on the macOS Desktop, and an applications menu entry on Linux. It opens the interface with no folder open, so you choose the segments in the browser. Running the installer again over 0.1.0 adds it.

**The installer asks first.** It lists what it is going to do (install uv if needed, install reviau, add the shortcut) and waits for a yes. `REVIAU_YES=1` skips the question, for scripts.

**Uninstalling.** Run the installer with `REVIAU_UNINSTALL=1` to remove reviau, its shortcut and its icon; the exact commands are in the [README](https://github.com/biodiversica/reviau#installation). Segments, and the reviews in their `reviau/` folders, are never removed.

**A new look.** The `(| |)` logo is the browser tab's icon, the tab shows reviau's version, and the dark theme is now a neutral graphite with a cyan accent.

**Faster `--help`.** `reviau --help` and `reviau --version` answer in about 0.15 s instead of 0.7 s, without loading the server.

**Documentation.** The README now covers what reviau is, installing and a quick start; everything else moved to one page per topic under [`docs/`](https://github.com/biodiversica/reviau/tree/main/docs), in English and Portuguese.

Nothing changes in how segments are read, reviewed or filed: `reviews.csv`, the annotation table and the `reviau/` folder are written exactly as in 0.1.0, so a review started with 0.1.0 continues where it stopped.
