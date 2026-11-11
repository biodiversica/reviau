"""The tables written as each segment is reviewed.

* The **review log** (``reviews.csv``) is the record of the review: one row per
  segment, always written, holding what the model predicted, what the reviewer
  heard, the outcome that follows, and where the clip was moved. Per-class
  precision and the confusion between classes are read straight off it, and the
  source/destination pair is what an undo needs.
* The **annotation table** (``annotations.csv``, opt-in) is derived data: one row
  per label a clip is confirmed to hold — ``site, file, label, start_time,
  end_time``. A rejected prediction never appears in it, and neither does a clip
  the reviewer was unsure of.

Both are appended as they happen, so a lost session keeps what was reviewed.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime

from .config import ANNOTATION_COLUMNS, REVIEW_COLUMNS, SOURCES_CSV
from .naming import nfc, source_key
from .outcome import Outcome
from .storage import Backend

#: How a segment's labels are joined in one review-log cell.
LABEL_SEPARATOR = ";"


class SourceManifest:
    """The optional ``segment_sources.csv`` naming each clip's source recording.

    A clip's file name rarely carries the recording it was cut from, so without
    the manifest the ``recording``/``file`` columns stay empty.
    """

    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.path = backend.join(backend.root, SOURCES_CSV)
        self.error = ""
        self._sources: dict[str, str] = {}
        self._load()

    @property
    def present(self) -> bool:
        return bool(self._sources)

    def _load(self) -> None:
        try:
            text = self.backend.read_text(self.path)
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            return
        if text is None:
            return
        try:
            for row in csv.DictReader(io.StringIO(text)):
                if row.get("segment"):
                    self._sources[source_key(row["segment"])] = row.get("recording", "")
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)

    def recording_for(self, filename: str) -> str:
        return self._sources.get(source_key(filename), "")


@dataclass
class Review:
    """Everything known about one reviewed segment, ready to be written out."""

    outcome: Outcome
    source: str
    destination: str
    site: str | None
    recording: str
    score: float | None
    start_s: float | None
    end_s: float | None
    reviewed_at: datetime = field(default_factory=lambda: datetime.now().astimezone())


def _seconds(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"


class ReviewLog:
    """Appends one row per reviewed segment to ``reviews.csv``."""

    def __init__(self, backend: Backend, path: str) -> None:
        self.backend = backend
        self.path = path
        self.rows = 0

    def append(self, review: Review) -> None:
        o = review.outcome
        row = [
            review.reviewed_at.isoformat(timespec="seconds"),
            review.source,
            review.destination,
            o.predicted,
            "" if review.score is None else f"{review.score:g}",
            o.kind,
            LABEL_SEPARATOR.join(o.labels),
            LABEL_SEPARATOR.join(o.added),
            nfc(review.site),
            review.recording or "",
            _seconds(review.start_s),
            _seconds(review.end_s),
        ]
        self.backend.append_csv_row(self.path, row, REVIEW_COLUMNS)
        self.rows += 1


@dataclass
class AnnotationState:
    """What the status line under the buttons reports."""

    rows: int = 0
    rows_without_recording: int = 0
    error: str = ""
    have_sources: bool = False
    path: str = ""
    enabled: bool = False
    extra: dict = field(default_factory=dict)


class AnnotationTable:
    """Appends one row per confirmed label to the annotation CSV."""

    def __init__(self, backend: Backend, path: str, *, enabled: bool,
                 sources: SourceManifest) -> None:
        self.backend = backend
        self.path = path
        self.state = AnnotationState(path=path, enabled=enabled)
        if enabled and not path:
            self.state.enabled = False
            self.state.extra["no_path"] = True
        elif enabled:
            self.state.have_sources = sources.present
            if sources.error:
                self.state.extra["read_error"] = sources.error

    @property
    def enabled(self) -> bool:
        return self.state.enabled

    def append(self, review: Review) -> None:
        """Write a row for every label the clip is confirmed to hold.

        A clip marked unsure says nothing confident, and a clip that holds
        nothing on the list has no label to write — neither adds a row.
        """
        if not self.enabled or not review.outcome.is_annotation:
            return
        for label in review.outcome.labels:
            row = [
                nfc(review.site),
                review.recording or "",
                nfc(label),
                _seconds(review.start_s),
                _seconds(review.end_s),
            ]
            self.backend.append_csv_row(self.path, row, ANNOTATION_COLUMNS)
            self.state.rows += 1
            if not review.recording:
                self.state.rows_without_recording += 1


def segment_bounds(duration: float | None, det_start: float | None,
                   det_end: float | None) -> tuple[float | None, float | None]:
    """Start and end of a segment within its source recording, in seconds.

    The file name carries the window that was detected, but the clip on disk may
    be wider because of the padding used when it was cut. The difference between
    the clip's real duration and that window is split evenly over both sides,
    which reproduces a symmetric pad (clamped at the start of the recording).
    Falls back to the file name's window when the clip cannot be measured.
    """
    if det_start is None or det_end is None:
        return None, None
    if duration is None:
        return det_start, det_end
    start = max(0.0, det_start - (duration - (det_end - det_start)) / 2.0)
    return start, start + duration
