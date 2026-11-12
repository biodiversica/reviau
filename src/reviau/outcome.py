"""What a review says about a segment, worked out from what the reviewer heard.

The reviewer answers one question — *what is in this clip?* — with a set of
labels. Whether the prediction was right follows from that set and the label the
clip arrived with, so it is derived here rather than asked for separately: two
inputs for one fact can contradict each other, one cannot.

========================  ===============  ======================================
reviewer's labels         outcome          meaning
========================  ===============  ======================================
``{P}``                   ``correct``      true positive
``{P, X, …}``             ``correct``      true positive, more species present
``{X, …}`` without P      ``incorrect``    false positive, with what it really is
``{}``                    ``incorrect``    false positive, nothing on the list
any, marked uncertain     ``uncertain``    no decision; kept out of the counts
any, clip has no P        ``labelled``     nothing was predicted to be right about
========================  ===============  ======================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .naming import nfc, slug

CORRECT = "correct"
INCORRECT = "incorrect"
UNCERTAIN = "uncertain"
LABELLED = "labelled"

#: Every outcome, in the order they are reported. Each is also the name of the
#: folder its clips are filed under — fixed, whatever the interface language,
#: so the data a review writes never depends on who reviewed it.
OUTCOMES: tuple[str, ...] = (CORRECT, INCORRECT, UNCERTAIN, LABELLED)


def clean_labels(labels) -> tuple[str, ...]:
    """Labels stripped, NFC-normalised and de-duplicated, keeping their order."""
    out: list[str] = []
    for raw in labels or ():
        label = nfc(str(raw)).strip()
        if label and label not in out:
            out.append(label)
    return tuple(out)


@dataclass(frozen=True)
class Outcome:
    """The verdict on one segment, and the labels it was settled on."""

    kind: str
    #: The label the clip arrived with — the model's prediction — or "".
    predicted: str
    #: What the reviewer says the clip contains. Empty: nothing on the list.
    labels: tuple[str, ...]

    @property
    def added(self) -> tuple[str, ...]:
        """Labels the reviewer gave besides the prediction."""
        return tuple(x for x in self.labels if x != self.predicted)

    @property
    def is_annotation(self) -> bool:
        """Whether the labels are a confident statement of what the clip holds."""
        return self.kind != UNCERTAIN


def decide(predicted: str | None, labels, *, uncertain: bool = False) -> Outcome:
    """The outcome of reviewing a clip predicted *predicted* as holding *labels*."""
    p = nfc(predicted or "").strip()
    # A label read off a folder has its underscores shown as spaces, so the
    # reviewer typing ``chuva_forte`` for a clip found in ``chuva_forte/`` means
    # the same class: anything that would be filed under the same folder name
    # as the prediction *is* the prediction.
    given = clean_labels(
        p if p and slug(nfc(x)) == slug(p) else x for x in (labels or ())
    )
    if uncertain:
        kind = UNCERTAIN
    elif not p:
        kind = LABELLED
    elif p in given:
        kind = CORRECT
    else:
        kind = INCORRECT
    return Outcome(kind=kind, predicted=p, labels=given)


__all__ = [
    "CORRECT",
    "INCORRECT",
    "LABELLED",
    "OUTCOMES",
    "UNCERTAIN",
    "Outcome",
    "clean_labels",
    "decide",
]
