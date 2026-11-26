# Running on a Server

*English · [Português (Brasil)](../pt-BR/server.md)*

The interface is an ordinary web page, so the tool can run on the machine that
holds the audio and be used from any other:

```bash
reviau /data/segments --host 0.0.0.0 --port 8765 --no-open
```

With `--host 0.0.0.0` the command also prints the address that other machines
should use.

## Access Token

When a non-loopback address is bound, an **access token** is generated and
included in the printed address; once that address has been opened, the token is
stored in a cookie. `--token mysecret` sets the token explicitly, and `--no-auth`
serves the interface without one.

The token prevents casual access but does not provide encryption (TLS). Anyone
holding it can open and review (and therefore move clips in) any folder the
reviewer can read, and can list the folder names of that machine. The token
should therefore be treated as a password, and `--no-auth` should be avoided on
shared networks.

## Untrusted Networks

On untrusted networks, Tailscale (binding to the Tailscale address, or to
`0.0.0.0` on a machine reachable only through the tailnet) or an SSH tunnel is
recommended:

```bash
# on the server
reviau /data/segments --port 8765 --no-open
# on the local computer
ssh -N -L 8765:127.0.0.1:8765 user@server   # then open http://127.0.0.1:8765
```

## One Reviewer at a Time

The tool supports one reviewer at a time. The pending list, the current position
and the open folder are held by the server, so two browsers connected to the same
instance control the same session; a folder opened in one is opened in both.
