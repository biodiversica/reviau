import re

from typer.main import get_command
from typer.testing import CliRunner

from reviau import __version__
from reviau.cli import _is_loopback, cli

runner = CliRunner()

_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def plain(text: str) -> str:
    """Rendered output with its colour codes removed.

    Typer draws its help through rich, which colours the output whenever it
    thinks it is on a terminal — on GitHub Actions it always does. That splits a
    switch like ``--lang`` across escape sequences, so raw text is not something
    to assert against.
    """
    return _ANSI.sub("", text)


def declared_options() -> set[str]:
    """Every switch the command actually accepts, whatever the help looks like."""
    names: set[str] = set()
    for param in get_command(cli).params:
        names.update(param.opts)
        names.update(param.secondary_opts)
    return names


def test_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in plain(result.stdout)


def test_help_renders():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in plain(result.stdout)
    assert "SEGMENTS" in plain(result.stdout)


def test_the_documented_options_are_all_accepted():
    """Checked against the command, not its rendering, which rich reflows and
    truncates depending on the terminal it believes it is writing to."""
    names = declared_options()
    for flag in ("--lang", "--multi-label", "--no-multi-label", "--labels-file",
                 "--annotations", "--annotations-path", "--output", "--host",
                 "--port", "--token", "--no-auth", "--open", "--no-open",
                 "--ssh-key", "--known-hosts", "--accept-new-host-key",
                 "--cache-dir", "--version"):
        assert flag in names, flag


REMOVED = ("--filename-pattern", "--datetime-format", "--label-from", "--label-depth",
           "--spec-type", "--fmin", "--fmax", "--db-floor", "--labels",
           "--no-labels-file", "--ssh-user", "--ssh-port", "--ssh-password")


def test_options_moved_to_the_gui_or_dropped_are_gone():
    """Reading settings are per folder in the GUI now; the spectrogram view is
    the browser's; the rest duplicated the address or misbehaved."""
    names = declared_options()
    assert not [flag for flag in REMOVED if flag in names]


def test_a_removed_option_is_refused(tmp_path):
    result = runner.invoke(cli, [str(tmp_path), "--label-depth", "1"])
    assert result.exit_code != 0


def test_missing_folder_exits_with_an_error(tmp_path):
    result = runner.invoke(cli, [str(tmp_path / "nope")])
    assert result.exit_code == 2


def test_loopback_detection():
    assert _is_loopback("127.0.0.1") and _is_loopback("localhost") and _is_loopback("::1")
    assert not _is_loopback("0.0.0.0") and not _is_loopback("100.64.0.5")


def test_the_segments_folder_is_optional():
    """It can be opened — and changed — from the browser instead."""
    segments = next(p for p in get_command(cli).params if p.name == "segments")
    assert segments.required is False
