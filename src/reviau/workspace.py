"""Which segments folder is open, and opening another one from the GUI.

The server starts with a folder or without one; either way the reviewer can
open any folder — local, or ``ssh://`` — from the browser, and switch to another
without restarting. Every folder opened gets the options the command line was
started with (output folder, annotations, SSH keys, …), and its own reading
settings — filename pattern, label source and depth — from the
``settings.json`` in its work folder.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from .config import REVIEW_LOG, WORK_DIR, ReviewConfig, work_folder
from .reading import READING_FILE, Reading, ReadingError
from .reading import load as load_reading
from .reading import save as save_reading
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
        #: Why the open folder's reading settings are not the ones it stores,
        #: if they are not — an unreadable settings.json, or one not saved.
        self.reading_error = ""

    def open(self, spec: str, reading: Reading | None = None) -> Opened:
        """Open *spec* for review, replacing whatever was open.

        The folder is read with its own settings from its ``settings.json``, or
        with *reading* when one is given. Nothing changes unless the new folder
        opens cleanly: a typo leaves the current review exactly where it was.
        """
        spec = str(spec or "").strip()
        if not spec:
            raise OpenError("No folder was specified.")
        try:
            backend = self._open_backend(spec)
        except Exception as exc:
            raise OpenError(f"The folder {spec} could not be opened: {exc}") from exc
        try:
            if not backend.isdir(backend.root):
                raise OpenError(f"{backend.display} is not a folder.")
            if _is_work_folder(backend):
                raise OpenError(
                    f"{backend.display} is the folder in which reviau keeps its results. "
                    "Open the segments folder that contains it."
                )
            problem = ""
            if reading is None:
                reading, problem = load_reading(backend, work_folder(backend, self.config.output))
            session = ReviewSession(
                backend, replace(self.config, segments=spec, **reading.as_dict())
            )
            pattern = session.pattern_report()
        except Exception:
            backend.close()
            raise
        with self._lock:
            previous, self.session = self.session, session
            self.reading_error = problem
        if previous is not None:
            previous.backend.close()
        return Opened(session, pattern)

    def apply_reading(self, reading: Reading) -> Opened:
        """Read the open folder with *reading* from now on, and keep it there.

        The settings are saved to the folder's ``settings.json`` and the folder
        is reopened with them. A folder that cannot be written to still gets them
        for this session, and :attr:`reading_error` says they were not kept.
        """
        session = self.session
        if session is None:
            raise OpenError("No segments folder is open.")
        reading = reading.validated()            # ReadingError when unusable
        try:
            save_reading(session.backend, session.output_root, reading)
            problem = ""
        except Exception as exc:  # noqa: BLE001 - reported, the session carries on
            problem = (f"The settings could not be saved ({exc}); "
                       "they apply to this session only.")
        opened = self.open(session.config.segments, reading=reading)
        self.reading_error = problem
        return opened

    def close(self) -> None:
        with self._lock:
            previous, self.session = self.session, None
        if previous is not None:
            previous.backend.close()


def _is_work_folder(backend: Backend) -> bool:
    """Whether the folder opened is a work folder rather than segments.

    Reviewed as segments, its verdict folders would come back as pending clips
    and be filed a second time, inside a work folder of their own.
    """
    root = backend.root
    if backend.basename(root) != WORK_DIR:
        return False
    return any(backend.exists(backend.join(root, name)) for name in (REVIEW_LOG, READING_FILE))


# ── browsing for a folder ────────────────────────────────────────────────────
def browse(path: str | None, *, start: str | None = None) -> dict:
    """The folders inside *path* on this machine, for the GUI's folder picker.

    Lists the machine the reviewer runs on — the one that reads the clips — not
    the one the browser runs on. Hidden folders are left out. A remote
    ``ssh://`` folder cannot be browsed; it is typed in instead.
    """
    raw = str(path or "").strip()
    if raw and parse_ssh_spec(raw) is not None:
        raise OpenError("Remote folders cannot be browsed; enter the ssh:// path instead.")
    here = Path(os.path.expanduser(raw or start or "~")).resolve()
    while not here.is_dir() and here != here.parent:
        here = here.parent        # a half-typed path browses its nearest folder
    try:
        entries = list(os.scandir(here))
    except OSError as exc:
        raise OpenError(f"The folder {here} could not be listed: {exc.strerror or exc}") from exc

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


__all__ = ["OpenError", "Opened", "ReadingError", "Workspace", "browse"]
