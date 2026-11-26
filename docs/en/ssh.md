# Reviewing Segments over SSH

*English · [Português (Brasil)](../pt-BR/ssh.md)*

When a remote folder is given, every operation is carried out over SFTP: listing
the folder, reading clips, moving them into the verdict folders and writing the
log and the annotation table. Clips are cached locally as they are opened, so
returning to a previous clip does not require downloading it again.

```bash
reviau ssh://user@fieldserver:22/data/segments
reviau fieldserver:/data/segments          # scp-style address
reviau ssh://fieldserver/data/segments --ssh-key ~/.ssh/id_field
```

A remote folder can also be typed into the folder box of the interface; see
[Opening a Folder](reviewing.md#opening-a-folder).

## Authentication

The user and port are given in the address (`ssh://user@host:port/path`) or
taken from `~/.ssh/config`, together with host aliases and identity files, and an
SSH agent is used when one is running. Where neither a key nor an agent can be
used, a password is read from the `REVIAU_SSH_PASSWORD` environment variable; it
is never accepted on the command line, where it would be recorded in the shell
history. An unknown host key is rejected unless `--accept-new-host-key` is given;
`--known-hosts` adds a known_hosts file to trust.

## What Is Written on the Remote Machine

Nothing is written outside the `reviau/` folder (or the `--output` folder), and
no clip is ever deleted: reviewed clips are only moved from the segments folder
into it. `--cache-dir` sets where the local copies of the clips are kept (by
default, a temporary folder).
