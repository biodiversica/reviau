"""Everything the reviewer is configured with, in one place."""

from __future__ import annotations

from dataclasses import dataclass

from .naming import DEFAULT_DATETIME_FORMAT
from .reading import Reading

#: The folder reviau writes in, inside the segments folder unless --output
#: names another: the verdict folders, the review log, the label list, the
#: annotation table and the reading settings. Nothing is written beside the
#: clips themselves, so deleting this one folder undoes everything but the moves.
WORK_DIR = "reviau"

#: Optional manifest mapping each clip to the recording it was cut from. When a
#: collection carries one, the annotation table can name that recording. It is
#: input, written by whatever cut the clips, so it is read from the segments
#: folder.
SOURCES_CSV = "segment_sources.csv"
ANNOTATION_COLUMNS = ["site", "file", "label", "start_time", "end_time"]

#: The review log: one row per reviewed segment, written beside the verdict
#: folders. ``labels`` and ``added`` hold ``;``-separated labels.
REVIEW_LOG = "reviews.csv"
REVIEW_COLUMNS = [
    "reviewed_at", "source", "destination", "predicted", "score", "outcome",
    "labels", "added", "site", "recording", "start_time", "end_time",
]

#: Where the editable label list is kept, relative to the work folder.
DEFAULT_LABELS_FILE = "labels.txt"


@dataclass
class ReviewConfig:
    """Settings a review session runs with.

    Most come from the command line and apply to every folder opened. The four
    reading fields describe one collection instead: they are filled in per
    folder from the ``settings.json`` in its work folder (see
    :mod:`reviau.reading`), and changed from the GUI. The verdict folders are
    named after the outcomes and never translated, so a review split over
    sessions in two languages files its clips in one place.
    """

    segments: str = "."
    lang: str = "en"

    # How a segment's metadata is read — per folder, see reviau.reading.
    #: "auto" reads the label from the file name when the pattern captures one.
    label_from: str = "auto"
    #: Which folder carries the label, counting down from the segments root.
    #: 0 is the folder the clip sits in; 1 the first folder under the root, for
    #: collections that keep the class on top and sites inside it.
    label_depth: int = 0
    filename_pattern: str = "default"
    datetime_format: str = DEFAULT_DATETIME_FORMAT

    multi_label: bool = True
    save_annotations: bool = False
    annotations_path: str = ""

    #: The editable label list. Empty keeps the list for the session only; a
    #: relative path is read against the work folder.
    labels_file: str = DEFAULT_LABELS_FILE

    #: The work folder (see :data:`WORK_DIR`). Empty means ``reviau/`` inside
    #: the segments folder; a relative path is read against the segments
    #: folder, an absolute one is taken as given, so a review can write
    #: anywhere the reviewer can reach.
    output: str = ""

    @property
    def reading(self) -> Reading:
        """The reading fields, as the :class:`~reviau.reading.Reading` they form."""
        return Reading(self.filename_pattern, self.datetime_format,
                       self.label_from, self.label_depth)


def work_folder(backend, output: str = "") -> str:
    """The folder reviau writes in for the segments folder *backend* is open on."""
    raw = str(output or "").strip()
    return backend.resolve(raw) if raw else backend.join(backend.root, WORK_DIR)
