"""How a collection's file names and folders are read — set per folder.

A filename pattern, a date-time format, where the label comes from and which
folder level carries it describe one collection, not the reviewer: two folders
opened in one session may be named in two different ways. They are therefore
set from the GUI and kept with the folder, in ``settings.json`` in its work
folder (``reviau/``), so a folder reopens with its own settings from any machine
or browser. Like the label list, the file is written only when settings are
applied, never on opening.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from .naming import (
    DEFAULT_DATETIME_FORMAT,
    LABEL_SOURCES,
    PRESETS,
    SegmentParser,
    expressions,
)

#: The settings file, in the segments folder.
READING_FILE = "settings.json"

#: "auto" reads the label from the file name when the pattern captures one,
#: and from the folder otherwise.
LABEL_FROM_CHOICES: tuple[str, ...] = ("auto", *LABEL_SOURCES)


class ReadingError(ValueError):
    """Reading settings that cannot be used; the message says why."""


def pattern_has_label(pattern: str) -> bool:
    """True when the filename pattern captures a ``label`` group."""
    try:
        exprs = expressions(pattern)
    except ValueError:
        return False
    for expr in exprs:
        try:
            if "label" in re.compile(expr).groupindex:
                return True
        except re.error:
            return False
    return False


@dataclass(frozen=True)
class Reading:
    """How the names and folders of one collection are read."""

    filename_pattern: str = "default"
    datetime_format: str = DEFAULT_DATETIME_FORMAT
    label_from: str = "auto"
    label_depth: int = 0

    @property
    def resolved_label_from(self) -> str:
        """The label source in effect, with "auto" decided by the pattern."""
        if self.label_from != "auto":
            return self.label_from
        return "filename" if pattern_has_label(self.filename_pattern) else "folder"

    def validated(self) -> Reading:
        """These settings, cleaned, or :class:`ReadingError` saying what is wrong."""
        pattern = str(self.filename_pattern or "").strip() or "default"
        if pattern not in PRESETS:
            try:
                for expr in expressions(pattern):
                    re.compile(expr)
            except re.error as exc:
                raise ReadingError(f"The filename pattern is not a valid regular expression: {exc}.") from exc
            except ValueError as exc:        # a template with an unknown placeholder
                raise ReadingError(f"The filename pattern is not valid: {exc}") from exc
        fmt = str(self.datetime_format or "").strip() or DEFAULT_DATETIME_FORMAT
        if self.label_from not in LABEL_FROM_CHOICES:
            raise ReadingError(
                f"The label source must be one of: {', '.join(LABEL_FROM_CHOICES)}."
            )
        try:
            depth = int(self.label_depth)
        except (TypeError, ValueError) as exc:
            raise ReadingError("The label depth must be a whole number.") from exc
        if depth < 0:
            raise ReadingError("The label depth cannot be negative.")
        return Reading(pattern, fmt, self.label_from, depth)

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> Reading:
        """Settings from a JSON object, ignoring keys it does not know."""
        data = data if isinstance(data, dict) else {}
        defaults = cls()
        return cls(
            filename_pattern=data.get("filename_pattern", defaults.filename_pattern),
            datetime_format=data.get("datetime_format", defaults.datetime_format),
            label_from=data.get("label_from", defaults.label_from),
            label_depth=data.get("label_depth", defaults.label_depth),
        )


def load(backend, folder: str) -> tuple[Reading, str]:
    """The folder's settings, and an error message when its file is unusable.

    A missing file means the defaults. A file that cannot be read or holds
    settings that do not work also falls back to the defaults — a folder must
    always open — and the message says why, so the GUI can report it.
    *folder* is the work folder the file is kept in.
    """
    path = backend.join(folder, READING_FILE)
    try:
        text = backend.read_text(path)
    except Exception as exc:  # noqa: BLE001
        return Reading(), f"{READING_FILE} could not be read: {exc}"
    if text is None:
        return Reading(), ""
    try:
        return Reading.from_dict(json.loads(text)).validated(), ""
    except (ValueError, TypeError) as exc:
        return Reading(), f"{READING_FILE} is not valid ({exc}); the default settings are in use."


def save(backend, folder: str, reading: Reading) -> str:
    """Write the folder's settings into its work *folder*; returns the path."""
    path = backend.join(folder, READING_FILE)
    body = json.dumps(reading.as_dict(), indent=2, ensure_ascii=False) + "\n"
    backend.write_bytes(path, body.encode("utf-8"))
    return path


def parser_for(reading: Reading) -> SegmentParser:
    return SegmentParser(
        pattern=reading.filename_pattern,
        label_from=reading.resolved_label_from,
        datetime_format=reading.datetime_format,
        label_depth=reading.label_depth,
    )


def preview(session, reading: Reading, samples: int = 4) -> dict:
    """What *reading* would make of the folder's pending names, before applying it."""
    reading = reading.validated()
    parser = parser_for(reading)
    backend = session.backend
    with session._lock:
        pending = list(session.segments)
    matched, example = 0, ""
    for path in pending:
        name = backend.basename(path)
        if parser.matches(name):
            matched += 1
        elif not example:
            example = name
    rows = []
    for path in pending[:samples]:
        info = parser.parse(path, backend.root)
        rows.append({
            "name": backend.basename(path),
            "label": info.label or None,
            "site": info.site,
            "recorded_at": info.recorded_at.strftime("%Y-%m-%d %H:%M:%S") if info.recorded_at else None,
            "det_start": info.det_start,
            "det_end": info.det_end,
            "score": info.score,
        })
    return {
        "reading": reading.as_dict(),
        "label_from": reading.resolved_label_from,
        "matched": matched,
        "total": len(pending),
        "example": example,
        "samples": rows,
    }


__all__ = [
    "LABEL_FROM_CHOICES", "READING_FILE", "Reading", "ReadingError",
    "load", "parser_for", "pattern_has_label", "preview", "save",
]
