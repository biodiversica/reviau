"""``reviau`` — start the reviewer and serve its GUI to a browser."""

from __future__ import annotations

import ipaddress
import os
import secrets
import socket
import sys
import threading
import webbrowser

import typer
import uvicorn

from . import __version__, i18n
from .config import DEFAULT_LABELS_FILE, ReviewConfig
from .review import ReviewSession
from .server import create_app
from .storage import open_backend
from .workspace import OpenError, Workspace

cli = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Review a folder of audio segments in the browser: listen to each clip, "
        "look at its spectrogram, and say what is in it. Whether its label was "
        "correct or incorrect follows from that, and every review is logged to "
        "reviews.csv.\n\n"
        "Everything reviau writes goes in one folder, reviau/, inside the segments "
        "folder: the reviewed clips under correct/, incorrect/ and uncertain/, the "
        "review log, the label list and the reading settings. Nothing is written "
        "beside the clips themselves.\n\n"
        "By default a segment's label is the folder it sits in, and its file name "
        "is read as [site]_[YYYYMMDD]_[HHMMSS]_[start]_[end]_*. How each folder's "
        "names are read is set in the browser, under Reading settings, and kept "
        "in that folder's reviau/settings.json.\n\n"
        "An SSH password, where keys or an agent cannot be used, is read from "
        "the REVIAU_SSH_PASSWORD environment variable.\n\n"
        "SEGMENTS may be a local folder or a remote one over SSH, and may be left "
        "out: the folder can be opened — and changed — from the browser.\n"
        "  reviau\n"
        "  reviau /data/segments\n"
        "  reviau ssh://user@host/data/segments"
    ),
)

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"reviau {__version__}")
        raise typer.Exit()


def _is_loopback(host: str) -> bool:
    if host in LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _lan_address() -> str:
    """This machine's address on the network it routes through, for the hint line."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        sock.close()


def _pattern_note(session: ReviewSession, t) -> str:
    """Warning shown when the filename pattern reads few of the pending names.

    A pattern that fits nothing is silent otherwise: the clips still show up,
    just without their site, time or score, which looks like the GUI dropping
    them rather than the pattern missing.
    """
    matched, total, example = session.pattern_report()
    if not total or matched == total:
        return ""
    key = "cli.pattern_none" if matched == 0 else "cli.pattern_some"
    note = t(key, matched=matched, total=total)
    return f"{note}\n  {t('cli.pattern_example', name=example)}" if example else note


def _summary(session: ReviewSession | None, config: ReviewConfig, t) -> str:
    if session is None:
        folder_rows = [(t("cli.folder"), t("cli.folder_none"))]
    else:
        counts = session.counts()
        folder_rows = [
            (t("cli.folder"), session.backend.display),
            (t("cli.output"), session.output_root),
            (t("cli.pending"), str(counts["pending"])),
            (t("cli.already_correct"), str(counts["correct"])),
            (t("cli.already_incorrect"), str(counts["incorrect"])),
            (t("cli.already_uncertain"), str(counts["uncertain"])),
            *([(t("cli.already_labelled"), str(counts["labelled"]))]
              if counts["labelled"] else []),
            (t("cli.review_log"), session.log.path),
        ]
    if session is not None and session.annotations.enabled:
        annotations = session.annotations.state.path
    elif session is None and config.save_annotations:
        annotations = t("cli.on")
    else:
        annotations = t("cli.off")
    # How names are read is the open folder's own setting, from its settings.json.
    reading = [] if session is None else [
        (t("cli.label_from"), session.config.reading.resolved_label_from),
        *([(t("cli.label_depth"), str(session.config.label_depth))]
          if session.config.label_depth else []),
        (t("cli.pattern"), session.config.filename_pattern),
    ]
    rows = [
        *folder_rows,
        *reading,
        *([] if session is None else [
            (t("cli.pattern_match"), "{} / {}".format(*session.pattern_report()[:2])),
            (t("cli.labels"), ", ".join(session.label_choices()) or t("cli.labels_none")),
            (t("cli.labels_file"),
             session.labels.path if session.labels.persisted else t("cli.off")),
        ]),
        (t("cli.multi"), t("cli.on") if config.multi_label else t("cli.off")),
        (t("cli.annotations"), annotations),
    ]
    width = max(len(name) for name, _ in rows)
    return "\n".join(f"{name.ljust(width)} : {value}" for name, value in rows)


@cli.command()
def review(
    segments: str | None = typer.Argument(
        None,
        metavar="[SEGMENTS]",
        help="Segments folder to open at start: a local path, or "
             "ssh://user@host:port/path (user and port optional). "
             "Leave it out to open one from the browser.",
    ),
    lang: str = typer.Option(
        "en", "--lang", "-l",
        help=f"Interface language at start: {', '.join(i18n.available())}.",
    ),
    multi_label: bool = typer.Option(
        True, "--multi-label/--no-multi-label",
        help="Allow several labels per segment, e.g. two species singing at once. "
             "On by default; --no-multi-label restricts each segment to one label.",
    ),
    labels_file: str | None = typer.Option(
        None, "--labels-file",
        help="Where the editable label list is kept, one label per line. Relative "
             "paths are inside the reviau folder; an absolute path shares one "
             "list between folders.  [default: <output>/labels.txt]",
    ),
    annotations: bool = typer.Option(
        False, "--annotations/--no-annotations",
        help="Also write a CSV with one row per label a segment is confirmed to "
             "hold; rejected predictions and uncertain segments add no row.",
    ),
    annotations_path: str = typer.Option(
        "", "--annotations-path",
        help="Where that table lives. Relative paths are inside the reviau folder. "
             "[default: <output>/annotations.csv]",
    ),
    output: str = typer.Option(
        "", "--output", "-o",
        help="The folder reviau writes in: correct/, incorrect/, uncertain/, "
             "reviews.csv, labels.txt and settings.json. Relative paths are inside "
             "the segments folder.  [default: <SEGMENTS>/reviau]",
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host",
        help="Address to bind. Use 0.0.0.0 to reach the GUI from another machine.",
    ),
    port: int = typer.Option(8765, "--port", "-p", min=1, max=65535, help="Port to listen on."),
    token: str | None = typer.Option(
        None, "--token",
        help="Access token required by the GUI. One is generated when binding a "
             "non-loopback address; use --no-auth to serve without it.",
    ),
    no_auth: bool = typer.Option(False, "--no-auth", help="Serve without an access token."),
    open_browser: bool = typer.Option(
        True, "--open/--no-open", help="Open the GUI in a browser on start."
    ),
    ssh_key: str | None = typer.Option(None, "--ssh-key", help="Private key file for the SSH connection."),
    known_hosts: str | None = typer.Option(
        None, "--known-hosts", help="Extra known_hosts file to trust."
    ),
    accept_new_host_key: bool = typer.Option(
        False, "--accept-new-host-key",
        help="Accept an unknown SSH host key instead of refusing to connect.",
    ),
    cache_dir: str | None = typer.Option(
        None, "--cache-dir", help="Where remote clips are cached locally. [default: a temp folder]"
    ),
    _version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Open SEGMENTS in the browser reviewer."""
    language = i18n.normalize(lang)
    if language != lang:
        typer.secho(
            f"Unknown language {lang!r}; using {language!r}. "
            f"Available: {', '.join(i18n.available())}",
            fg=typer.colors.YELLOW, err=True,
        )
    t = i18n.Translator(language)

    config = ReviewConfig(
        segments=segments or "",
        lang=language,
        labels_file=labels_file or DEFAULT_LABELS_FILE,
        multi_label=multi_label,
        save_annotations=annotations,
        annotations_path=annotations_path,
        output=output,
    )
    # A password on the command line would land in the shell history and the
    # process list; it is only ever taken from the environment.
    ssh_password = os.environ.get("REVIAU_SSH_PASSWORD") or None

    def opener(spec: str):
        # Every folder opened — here or later from the browser — connects with
        # the SSH settings the command line was started with.
        return open_backend(
            spec,
            ssh_key=ssh_key,
            ssh_password=ssh_password,
            known_hosts=known_hosts,
            accept_new_host_key=accept_new_host_key,
            cache_dir=cache_dir,
        )

    workspace = Workspace(config, opener)
    pattern = None
    if segments:
        try:
            pattern = workspace.open(segments).pattern
        except OpenError as exc:
            # A folder named on the command line was asked for explicitly: a
            # typo there stops the run rather than opening an empty reviewer.
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2) from exc
    session = workspace.session

    access_token: str | None = None
    if not no_auth:
        access_token = token or (None if _is_loopback(host) else secrets.token_urlsafe(16))

    app = create_app(workspace, config, access_token)
    app.state.pattern = pattern

    shown_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    suffix = f"?token={access_token}" if access_token else ""
    url = f"http://{shown_host}:{port}/{suffix}"

    typer.echo(_summary(session, config, t))
    note = _pattern_note(session, t) if session is not None else ""
    if note:
        typer.echo("")
        typer.secho(note, fg=typer.colors.YELLOW, err=True)
    typer.echo("")
    typer.secho(f'{t("cli.serving")}  {url}', fg=typer.colors.GREEN, bold=True)
    if host in ("0.0.0.0", "::"):
        typer.echo(f"  http://{_lan_address()}:{port}/{suffix}")
        typer.echo(f"  {t('cli.network_hint')}")
    if access_token:
        typer.echo(f"  {t('cli.token_hint')}")
    typer.echo(f"  {t('cli.stop_hint')}")

    if open_browser and not os.environ.get("REVIAU_NO_BROWSER"):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)
    finally:
        workspace.close()


def main() -> None:
    try:
        cli()
    except KeyboardInterrupt:  # pragma: no cover - user pressed Ctrl+C
        sys.exit(130)


if __name__ == "__main__":
    main()
