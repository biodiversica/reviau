# (| |) reviau

*English · [Português (Brasil)](https://github.com/biodiversica/reviau/blob/main/README.pt-BR.md)*

reviau is a tool that provides a **browser interface for reviewing a folder of
audio segments**. Each clip is presented as a spectrogram, together with the
information its folder and file name provide. The reviewer listens to the clip
and records **what it contains**; whether the label it arrived with is
**correct** or **incorrect** is derived from that answer. Reviewed clips are
moved into `correct/`, `incorrect/` or `uncertain/`, every review is recorded in
`reviews.csv` (prediction, outcome and the labels actually identified), and the
confirmed labels may also be written to an annotation table. All of this is kept
in a single **`reviau/`** folder inside the segments folder, and nothing is
written beside the clips themselves.

reviau was designed primarily for **bioacoustic analysis**, to review the
segments that detection methods such as **template matching**, **vector
search** and **custom classifiers** under validation find in field recordings,
for example those of passive acoustic monitoring. It is not limited to these
methods, however, and accepts any collection of clips, regardless of how it was
produced, including manually cut examples. The segments folder may be
**local** or **remote over SSH**, and the interface may be served to **another
machine** on a local network or a Tailscale network. The interface is available
in **English** and **Português (Brasil)**.

## Installation

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

The installer lists what it is going to do and asks for confirmation before
changing anything.

**Uninstalling.** Run the installer again with `REVIAU_UNINSTALL` set. On
Windows, close the reviau window first, then run in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c '$env:REVIAU_UNINSTALL=1; irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex'
```

On macOS and Linux:

```sh
curl -LsSf https://github.com/biodiversica/reviau/releases/latest/download/install.sh | REVIAU_UNINSTALL=1 sh
```

Segments, and the reviews in their `reviau/` folders, are never removed.

**With uv or pip.** reviau is published on PyPI and requires Python 3.10 or
later:

```bash
uv tool install reviau   # as an isolated command-line tool
pip install reviau       # or with pip, into the current environment
```

[Installation](https://github.com/biodiversica/reviau/blob/main/docs/en/installation.md)
describes what the installer does, its environment variables, and what
uninstalling removes and leaves behind.

## Quick Start

```bash
reviau                                     # start, and open a folder from the browser
reviau ~/segments                          # open a local folder at start-up
reviau ssh://user@fieldserver/data/segments   # segments on a server, over SSH
reviau ~/segments --lang pt-BR --annotations  # Portuguese interface, with an annotation table
```

The command prints the address to open, and opens a browser on it. By default a
clip's folder is its label and its name is read as
`[site]_[YYYYMMDD]_[HHMMSS]_[start]_[end]_*`; both can be changed per folder
from the **⚙** button. In the browser, <kbd>T</kbd>, <kbd>F</kbd> and
<kbd>U</kbd> record correct, incorrect and uncertain, <kbd>1</kbd>…<kbd>9</kbd>
add labels, and <kbd>Space</kbd> plays the clip. `reviau --help` lists every
option.

## Documentation

| Page | Contents |
|---|---|
| [Installation](https://github.com/biodiversica/reviau/blob/main/docs/en/installation.md) | The installer and its shortcut, uninstalling, uv and pip |
| [How a Segment Is Read](https://github.com/biodiversica/reviau/blob/main/docs/en/segments.md) | The label from the folder, the label depth, the default file-name pattern |
| [Reviewing in the Browser](https://github.com/biodiversica/reviau/blob/main/docs/en/reviewing.md) | Opening a folder, the controls, how the outcome is decided, keyboard shortcuts |
| [The reviau Folder](https://github.com/biodiversica/reviau/blob/main/docs/en/reviau-folder.md) | The label list, where a reviewed clip is filed, `--output`, the review log, the annotation table |
| [Reading Settings](https://github.com/biodiversica/reviau/blob/main/docs/en/reading-settings.md) | Per-folder file-name templates, regular expressions, the label source, the vector-search preset |
| [Reviewing over SSH](https://github.com/biodiversica/reviau/blob/main/docs/en/ssh.md) | Remote folders, authentication, what is written on the remote machine |
| [Running on a Server](https://github.com/biodiversica/reviau/blob/main/docs/en/server.md) | Serving the interface to another machine, the access token, Tailscale and SSH tunnels |
| [Command-Line Options](https://github.com/biodiversica/reviau/blob/main/docs/en/cli.md) | Examples and every option |
| [Development](https://github.com/biodiversica/reviau/blob/main/docs/en/development.md) | Working on reviau itself, tests and CI |

## Licence

[MIT](https://github.com/biodiversica/reviau/blob/main/LICENSE)
