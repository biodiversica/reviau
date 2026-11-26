# Command-Line Options

*English · [Português (Brasil)](../pt-BR/cli.md)*

## Examples

```bash
# Start without a folder and open one from the browser
reviau

# Open a local folder at start-up, with the interface on this machine
reviau ~/segments

# Portuguese interface, one label list shared by every folder, an annotation table
reviau ~/segments --lang pt-BR --labels-file ~/classes.txt --annotations

# Segments on a server, reviewed from another computer
reviau ssh://user@fieldserver/data/segments

# Serve the interface to the network (local network, Tailscale, …)
reviau /data/segments --host 0.0.0.0 --port 8765
```

The command prints a summary and the address to open.

## Options

```
reviau [SEGMENTS] [OPTIONS]

  SEGMENTS                      Folder to open at start-up: a local path, or
                                ssh://[user@]host[:port]/path. Optional; a folder
                                can be opened, and changed, in the browser

  -l, --lang TEXT               Interface language at start-up: en, pt-BR  [default: en]
      --labels-file TEXT        Location of the label list, one label per line.
                                Relative paths are inside the reviau folder; an
                                absolute path shares one list between folders
                                [default: <output>/labels.txt]
      --no-multi-label          Restrict each segment to one label (several labels
                                per segment are allowed by default)
      --annotations             Also write the annotation table of confirmed labels
      --annotations-path TEXT   Location of the table  [default: <output>/annotations.csv]

  -o, --output TEXT             Folder in which the reviewed segments, reviews.csv,
                                labels.txt and settings.json are written
                                [default: <SEGMENTS>/reviau]

      --host TEXT               Address to bind  [default: 127.0.0.1]
  -p, --port INTEGER            Port  [default: 8765]
      --token TEXT              Access token for the interface
      --no-auth                 Serve the interface without an access token
      --open / --no-open        Open a browser at start-up  [default: open]

      --ssh-key TEXT            Private key file for SSH connections
      --known-hosts TEXT        Additional known_hosts file to trust
      --accept-new-host-key     Accept an unknown SSH host key
      --cache-dir TEXT          Location of the local cache of remote clips
                                [default: a temporary folder]

      --version                 Show the version and exit

  Environment: REVIAU_SSH_PASSWORD  SSH password, where keys or an agent cannot be used
```

The filename pattern, the date-time format, the label source and the label depth
are set per folder in the [reading settings](reading-settings.md), and the
spectrogram view is set in the interface and stored in the browser.

| Topic | Options | Page |
| --- | --- | --- |
| Labels and the annotation table | `--labels-file`, `--no-multi-label`, `--annotations`, `--annotations-path` | [The reviau Folder](reviau-folder.md) |
| Results elsewhere | `--output` | [Writing to Another Location](reviau-folder.md#writing-to-another-location) |
| Remote folders | `--ssh-key`, `--known-hosts`, `--accept-new-host-key`, `--cache-dir` | [SSH](ssh.md) |
| Serving to the network | `--host`, `--port`, `--token`, `--no-auth`, `--no-open` | [Running on a Server](server.md) |
