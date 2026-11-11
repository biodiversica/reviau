"""Which segments folder is open, and opening another one from the GUI.

The server starts with a folder or without one; either way the reviewer can
open any folder — local, or ``ssh://`` — from the browser, and switch to another
without restarting. Every folder opened gets the same settings the command line
was started with (filename pattern, label depth, output folder, SSH keys, …).
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .config import ReviewConfig
from .review import ReviewSession
from .storage import Backend, parse_ssh_spec


class OpenError(ValueError):
    """A folder that cannot be opened for review; the message says why."""


@dataclass
class Opened:
    """The session for the folder just opened, and how its names were read."""

    session: ReviewSession
    #: (names the filename pattern read, pending names, one it did not read)
    pattern: tuple[int, int, str]


class Workspace:
    """Holds the open review session, if any, and swaps it for another."""

    def __init__(self, config: ReviewConfig,
                 open_backend: Callable[[str], Backend]) -> None:
        self.config = config
        self._open_backend = open_backend
        self._lock = threading.Lock()
        self.session: ReviewSession | None = None

    def open(self, spec: str) -> Opened:
        """Open *spec* for review, replacing whatever was open.

        Nothing changes unless the new folder opens cleanly: a typo leaves the
        current review exactly where it was.
        """
        spec = str(spec or "").strip()
        if not spec:
            raise OpenError("no folder given")
        try:
            backend = self._open_backend(spec)
        except Exception as exc:  # noqa: BLE001 - a connection or path problem
            raise OpenError(f"could not open {spec}: {exc}") from exc
        try:
            if not backend.isdir(backend.root):
                raise OpenError(f"not a folder: {backend.display}")
            session = ReviewSession(backend, replace(self.config, segments=spec))
            pattern = session.pattern_report()
        except Exception:
            backend.close()
            raise
        with self._lock:
            previous, self.session = self.session, session
        if previous is not None:
            previous.backend.close()
        return Opened(session, pattern)

    def close(self) -> None:
        with self._lock:
            previous, self.session = self.session, None
        if previous is not None:
            previous.backend.close()


# ── browsing for a folder ────────────────────────────────────────────────────
def browse(path: str | None, *, start: str | None = None) -> dict:
    """The folders inside *path* on this machine, for the GUI's folder picker.

    Lists the machine the reviewer runs on — the one that reads the clips — not
    the one the browser runs on. Hidden folders are left out. A remote
    ``ssh://`` folder cannot be browsed; it is typed in instead.
    """
    raw = str(path or "").strip()
    if raw and parse_ssh_spec(raw) is not None:
        raise OpenError("remote folders cannot be browsed — type the ssh:// path instead")
    here = Path(os.path.expanduser(raw or start or "~")).resolve()
    while not here.is_dir() and here != here.parent:
        here = here.parent        # a half-typed path browses its nearest folder
    try:
        entries = list(os.scandir(here))
    except OSError as exc:
        raise OpenError(f"cannot list {here}: {exc.strerror or exc}") from exc

    folders, wavs = [], 0
    for entry in entries:
        try:
            if entry.is_dir() and not entry.name.startswith("."):
                folders.append({"name": entry.name, "path": entry.path,
                                "has_wavs": _holds_wavs(entry.path)})
            elif entry.is_file() and entry.name.lower().endswith(".wav"):
                wavs += 1
        except OSError:
            continue
    folders.sort(key=lambda f: f["name"].lower())
    return {
        "path": str(here),
        "parent": None if here == here.parent else str(here.parent),
        "folders": folders,
        "wavs": wavs,
    }


def _holds_wavs(folder: str) -> bool:
    """Whether *folder* holds a ``.wav`` directly — stops at the first one."""
    try:
        with os.scandir(folder) as it:
            return any(e.name.lower().endswith(".wav") for e in it)
    except OSError:
        return False


__all__ = ["OpenError", "Opened", "Workspace", "browse"]
