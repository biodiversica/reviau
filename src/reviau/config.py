"""Everything the reviewer is configured with, in one place."""

from __future__ import annotations

from dataclasses import dataclass, field

from .naming import DEFAULT_DATETIME_FORMAT

#: Optional manifest mapping each clip to the recording it was cut from. When a
#: collection carries one, the annotation table can name that recording.
SOURCES_CSV = "segment_sources.csv"
ANNOTATION_COLUMNS = ["site", "file", "label", "start_time", "end_time"]

#: The review log: one row per reviewed segment, written beside the verdict
#: folders. ``labels`` and ``added`` hold ``;``-separated labels.
REVIEW_LOG = "reviews.csv"
REVIEW_COLUMNS = [
    "reviewed_at", "source", "destination", "predicted", "score", "outcome",
    "labels", "added", "site", "recording", "start_time", "end_time",
]

#: Where the editable label list is kept, relative to the segments folder.
DEFAULT_LABELS_FILE = "labels.txt"


@dataclass
class ReviewConfig:
    """Settings the reviewer starts with.

    The spectrogram fields are only the *initial* values shown in the browser;
    they can be changed live without restarting. The rest is fixed for the run —
    the verdict folders are named after the outcomes and never translated, so
    a review split over sessions in two languages files its clips in one place.
    """

    segments: str = "."
    lang: str = "en"
    labels: list[str] = field(default_factory=list)

    # How a segment's metadata is read
    label_from: str = "folder"
    #: Which folder carries the label, counting down from the segments root.
    #: 0 is the folder the clip sits in; 1 the first folder under the root, for
    #: collections that keep the class on top and sites inside it.
    label_depth: int = 0
    filename_pattern: str = "default"
    datetime_format: str = DEFAULT_DATETIME_FORMAT

    multi_label: bool = True
    save_annotations: bool = False
    annotations_path: str = ""

    # The editable label list
    labels_file: str = DEFAULT_LABELS_FILE
    persist_labels: bool = True

    # Spectrogram defaults
    spec_type: str = "mel"
    freq_min_hz: int = 0
    freq_max_hz: int = 0  # 0 → Nyquist
    db_min: int = -80

    #: Folder the verdict folders and the review log are created in. Empty
    #: means the segments folder itself; a relative path is read against it, an
    #: absolute one is taken as given, so a review can write anywhere the
    #: reviewer can reach.
    output: str = ""
