"""The review session: which segment is on screen, and what a verdict does to it."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from .annotations import AnnotationTable, Review, ReviewLog, SourceManifest, segment_bounds
from .config import REVIEW_LOG, ReviewConfig
from .labels import LabelStore
from .naming import SegmentParser, nfc, slug, split_labels, with_labels
from .outcome import OUTCOMES, Outcome, decide
from .spectrogram import SpectrogramError, duration_seconds, render
from .storage import Backend


@dataclass
class SegmentView:
    """What the browser is told about the segment on screen."""

    index: int
    total: int
    name: str
    relpath: str
    #: Folders between the segments root and the clip, as one path.
    folder: str
    label: str
    #: Where that label came from: "folder", "filename" or "" when it has none.
    label_from: str
    site: str | None
    recorded_at: str | None
    det_start: float | None
    det_end: float | None
    score: float | None
    extra: str | None


class StaleSegment(LookupError):
    """The browser asked to review a clip that is no longer the one on screen."""


class ReviewSession:
    """Holds the pending list and files each reviewed segment.

    One session per running server: the reviewer is a single person walking a
    folder, and every mutation is serialised behind one lock so a double-click
    cannot file the same clip twice.
    """

    def __init__(self, backend: Backend, config: ReviewConfig) -> None:
        self.backend = backend
        self.config = config
        #: Where the verdict folders live — the segments folder unless --output
        #: says otherwise. Resolved once, so every path built from it agrees.
        self.output_root = (
            backend.resolve(config.output) if str(config.output).strip() else backend.root
        )
        self.parser = SegmentParser(
            pattern=config.filename_pattern,
            label_from=config.label_from,
            datetime_format=config.datetime_format,
            label_depth=config.label_depth,
        )
        self._lock = threading.RLock()
        self._ensure_dirs()
        self.sources = SourceManifest(backend)
        self.log = ReviewLog(backend, backend.join(self.output_root, REVIEW_LOG))
        self.annotations = AnnotationTable(
            backend,
            self._annotations_path(),
            enabled=config.save_annotations,
            sources=self.sources,
        )
        self.segments: list[str] = []
        self.index = 0
        self._reviewed: dict[str, int] = {k: 0 for k in OUTCOMES}
        self.rescan()
        self.labels = LabelStore(
            backend,
            backend.resolve(config.labels_file) if config.labels_file else "",
            configured=config.labels,
            discovered=self.discovered_labels(),
            persist=config.persist_labels,
        )

    # ── setup ────────────────────────────────────────────────────────────────
    def _ensure_dirs(self) -> None:
        # ``labelled/`` only ever holds clips that came with no prediction, so it
        # is made when the first one is filed rather than in every collection.
        for name in OUTCOMES[:3]:
            self.backend.makedirs(self.verdict_root(name))

    def _annotations_path(self) -> str:
        if not self.config.save_annotations:
            return self.backend.resolve(self.config.annotations_path)
        raw = self.config.annotations_path.strip()
        if not raw:
            # A written table is reviewed output, so it goes where the verdict
            # folders go; a path given by hand is still read as documented,
            # against the segments folder.
            return self.backend.join(self.output_root, "annotations.csv")
        return self.backend.resolve(raw)

    # ── the pending list ─────────────────────────────────────────────────────
    def verdict_root(self, name: str) -> str:
        """Absolute path of one verdict folder, under wherever the output goes."""
        return self.backend.join(self.output_root, name)

    def _skip_roots(self) -> list[str]:
        """Folders excluded from review — the verdict folders.

        Taken under the segments folder as well as under ``--output``: a review
        writing elsewhere must still skip the verdict folders of an earlier run
        that wrote in place, and an output folder nested inside the segments
        folder must not hand its own clips back as pending.
        """
        roots = {self.backend.root, self.output_root}
        return sorted(
            self.backend.join(root, name) for root in roots for name in OUTCOMES
        )

    def collect(self) -> list[str]:
        skip = self._skip_roots()
        return [
            path
            for path in self.backend.walk_wavs(self.backend.root)
            if not any(self.backend.is_inside(path, root) for root in skip)
        ]

    def rescan(self) -> None:
        with self._lock:
            current = self.segments[self.index] if 0 <= self.index < len(self.segments) else None
            self.segments = self.collect()
            self.index = self.segments.index(current) if current in self.segments else 0
            self.index = max(0, min(self.index, max(0, len(self.segments) - 1)))
            self._reviewed = self._count_reviewed()

    def _count_reviewed(self) -> dict[str, int]:
        """Walk the verdict folders once. Over SFTP this is the expensive call."""
        done = {}
        for name in OUTCOMES:
            folder = self.verdict_root(name)
            done[name] = len(self.backend.walk_wavs(folder)) if self.backend.isdir(folder) else 0
        return done

    def counts(self) -> dict[str, int]:
        """Pending and reviewed totals.

        The reviewed tallies are taken at rescan and then kept up to date by each
        review, rather than re-walking the folders on every request the browser
        makes — a recount over SFTP costs a full remote listing.
        """
        with self._lock:
            return {**self._reviewed, "pending": len(self.segments)}

    # ── the segment on screen ────────────────────────────────────────────────
    def path_at(self, index: int) -> str:
        with self._lock:
            if not self.segments:
                raise IndexError("no segments pending review")
            if not 0 <= index < len(self.segments):
                raise IndexError(f"segment {index} is out of range")
            return self.segments[index]

    def view(self) -> SegmentView | None:
        with self._lock:
            if not self.segments:
                return None
            path = self.segments[self.index]
            info = self._parse(path)
            relpath = self.backend.relpath(path, self.backend.root)
            folder = self.backend.dirname(relpath).replace(self.backend.sep, "/")
            return SegmentView(
                index=self.index,
                total=len(self.segments),
                name=self.backend.basename(path),
                relpath=relpath.replace(self.backend.sep, "/"),
                folder=folder,
                label=info.label,
                label_from=("filename" if info.label_in_filename
                            else ("folder" if info.label else "")),
                site=info.site,
                recorded_at=info.recorded_at.strftime("%Y-%m-%d %H:%M:%S") if info.recorded_at else None,
                det_start=info.det_start,
                det_end=info.det_end,
                score=info.score,
                extra=info.extra,
            )

    def navigate(self, delta: int) -> None:
        with self._lock:
            if not self.segments:
                return
            self.index = max(0, min(len(self.segments) - 1, self.index + delta))

    def goto(self, index: int) -> None:
        with self._lock:
            if self.segments:
                self.index = max(0, min(len(self.segments) - 1, index))

    def _parse(self, path: str):
        return self.parser.parse(path, self.backend.root)

    # ── labels offered in the reviewer ───────────────────────────────────────
    def discovered_labels(self) -> list[str]:
        """Every label the pending clips already carry, in alphabetical order.

        The label folder in folder mode — the one ``--label-depth`` points at, so
        the sites kept under a class folder are not mistaken for classes — and
        the labels in the file names in filename mode. Used to seed the label
        list the first time a collection is opened.
        """
        with self._lock:
            pending = list(self.segments)
        return sorted({
            nfc(info.label).strip()
            for info in map(self._parse, pending)
            if str(info.label).strip()
        })

    def pattern_report(self) -> tuple[int, int, str]:
        """How many pending names the filename pattern reads, and one it does not.

        A template that does not fit the collection captures nothing, and the
        clips then arrive in the GUI with no site, time or score — reviewable,
        but with the pattern silently doing nothing. Counting the matches at
        start-up turns that into a line the user can act on.
        """
        with self._lock:
            pending = list(self.segments)
        matched, example = 0, ""
        for path in pending:
            name = self.backend.basename(path)
            if self.parser.matches(name):
                matched += 1
            elif not example:
                example = name
        return matched, len(pending), example

    def label_choices(self) -> list[str]:
        """The labels offered as buttons in the reviewer."""
        return self.labels.labels

    # ── reviewing a segment ──────────────────────────────────────────────────
    def _destination_dir(self, info, outcome: Outcome) -> str:
        """Where a reviewed segment goes: its outcome, then what was predicted.

        Filing by the *prediction* keeps each folder answering one question —
        ``wrong/PONTO_A/BOAALB/`` holds exactly the clips the model called
        BOAALB and got wrong, so counting a folder is that class's precision.
        The labels the reviewer added beyond the prediction are appended to
        the file name, and every clip's labels are in the review log.

        * **Label in a folder** (the default) — the folders that stood *above*
          the label are kept: ``PONTO_A/BOAALB/x.wav`` becomes
          ``correct/PONTO_A/BOAALB/x.wav`` or ``wrong/PONTO_A/BOAALB/x.wav``.
          Whatever sat *below* the label is not rebuilt: under
          ``--label-depth``, ``BOAALB/PONTO_A/20240115/x.wav`` becomes
          ``wrong/BOAALB/x.wav`` — the site and day are in the file name.
        * **Label in the file name** — filed flat under the prediction:
          ``wrong/BOAALB/x.wav``.
        * **No prediction** — the folders it sat in, under ``labelled/``.
        """
        parts = [] if info.label_in_filename else list(info.prefix)
        if outcome.predicted:
            parts.append(slug(outcome.predicted))
        root = self.verdict_root(outcome.kind)
        return self.backend.join(root, *parts) if parts else root

    def review(self, labels: list[str] | None = None, *, unsure: bool = False,
               relpath: str | None = None) -> dict:
        """File the current segment as holding *labels*, and drop it from the list.

        The outcome — correct, wrong, unsure, or labelled when nothing was
        predicted — follows from *labels* and the clip's own label; see
        :func:`segment_reviewer.outcome.decide`. *relpath*, when given, must be
        the clip on screen: a second tab, or a click racing a rescan, must not
        file a clip the reviewer never heard.
        """
        with self._lock:
            if not self.segments:
                return {"moved": None, "outcome": None}
            src = self.segments[self.index]
            rel_src = self.backend.relpath(src, self.backend.root).replace(self.backend.sep, "/")
            if relpath is not None and relpath != rel_src:
                raise StaleSegment(
                    f"{relpath} is no longer the segment on screen ({rel_src} is)"
                )
            info = self._parse(src)
            outcome = decide(info.label, labels, unsure=unsure)
            if len(outcome.labels) > 1 and not self.config.multi_label:
                raise ValueError("this review allows one label per segment")

            # Read the clip before moving it: it has to be on disk to be measured.
            try:
                duration = duration_seconds(self.backend.fetch(src))
            except Exception:  # noqa: BLE001 - fall back to the filename window
                duration = None
            start_s, end_s = segment_bounds(duration, info.det_start, info.det_end)

            folder = self._destination_dir(info, outcome)
            self.backend.makedirs(folder)
            # The folder names the prediction; the file name gains every label
            # the reviewer added beyond it, so the tree reads without the log:
            #   wrong/PONTO_A/BOAALB/x_TURDRU.wav    called BOAALB, really TURDRU
            #   correct/PONTO_A/BOAALB/x_PHYLUT.wav  BOAALB, and PHYLUT as well
            # Nothing added — a plain correct, a wrong holding nothing on the
            # list — and anything marked unsure keep the name as it was found.
            name = self.backend.basename(src)
            if outcome.is_annotation:
                name = with_labels(name, outcome.added)
            dest = self.backend.free_path(folder, name)
            self.backend.move(src, dest)

            record = Review(
                outcome=outcome,
                source=rel_src,
                destination=self.backend.relpath(dest, self.output_root)
                .replace(self.backend.sep, "/"),
                site=info.site,
                recording=self.sources.recording_for(self.backend.basename(src)),
                score=info.score,
                start_s=start_s,
                end_s=end_s,
            )
            try:
                self.log.append(record)
            except Exception:
                # The log is the record of the review: a clip filed without a
                # row would be a verdict nobody can read back. Undo the move.
                self.backend.move(dest, src)
                raise
            self.segments.pop(self.index)
            # The clip's own folder, and whatever else it was the last clip in,
            # are no longer part of the collection: a reviewed folder empties out
            # rather than leaving a shell of the tree behind.
            self.backend.prune_empty(self.backend.dirname(src), self.backend.root)

            try:
                self.annotations.append(record)
            except Exception as exc:  # noqa: BLE001 - derived data; the log has it
                self.annotations.state.error = str(exc)

            self._reviewed[outcome.kind] = self._reviewed.get(outcome.kind, 0) + 1
            if self.index >= len(self.segments) and self.index > 0:
                self.index -= 1
            return {"moved": record.destination, "outcome": outcome.kind}

    # ── media ────────────────────────────────────────────────────────────────
    def spectrogram(self, index: int, *, spec_type: str, fmin: int, fmax: int,
                    db_min: int) -> bytes:
        path = self.path_at(index)
        local: Path = self.backend.fetch(path)
        return render(
            local, spec_type=spec_type, fmin_hz=fmin, fmax_hz=fmax, db_min=db_min
        )

    def audio_bytes(self, index: int) -> tuple[bytes, str]:
        path = self.path_at(index)
        return self.backend.read_bytes(path), self.backend.basename(path)

    # ── helpers used by the API layer ────────────────────────────────────────
    @staticmethod
    def parse_labels(text: str, fallback: str = "") -> list[str]:
        return split_labels(text, fallback)


__all__ = ["ReviewSession", "SegmentView", "SpectrogramError", "StaleSegment"]
