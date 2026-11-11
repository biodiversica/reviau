"""The one rule that turns what the reviewer heard into a verdict."""

import pytest

from segment_reviewer.outcome import CORRECT, LABELLED, UNSURE, WRONG, decide


@pytest.mark.parametrize("labels, kind, added", [
    (["BOAALB"], CORRECT, ()),
    (["BOAALB", "PHYLUT"], CORRECT, ("PHYLUT",)),
    (["PHYLUT", "BOAALB"], CORRECT, ("PHYLUT",)),
    (["TURDRU"], WRONG, ("TURDRU",)),
    (["TURDRU", "PHYLUT"], WRONG, ("TURDRU", "PHYLUT")),
    ([], WRONG, ()),
])
def test_the_outcome_follows_from_the_labels(labels, kind, added):
    outcome = decide("BOAALB", labels)
    assert outcome.kind == kind
    assert outcome.predicted == "BOAALB"
    assert outcome.added == added


def test_unsure_wins_and_keeps_the_guess():
    outcome = decide("BOAALB", ["TURDRU"], unsure=True)
    assert outcome.kind == UNSURE
    assert outcome.labels == ("TURDRU",)
    assert not outcome.is_annotation


def test_with_no_prediction_there_is_nothing_to_be_right_about():
    assert decide("", ["rain"]).kind == LABELLED
    assert decide(None, []).kind == LABELLED


def test_labels_are_cleaned_and_deduplicated():
    assert decide("BOAALB", [" BOAALB ", "", "BOAALB", "PHYLUT "]).labels == (
        "BOAALB", "PHYLUT",
    )


def test_an_underscore_spelling_is_the_same_class():
    """A folder chuva_forte/ is shown as "chuva forte"; typing it with the
    underscore must not turn a correct clip into a wrong one."""
    outcome = decide("chuva forte", ["chuva_forte"])
    assert outcome.kind == CORRECT
    assert outcome.labels == ("chuva forte",)


def test_accents_spelled_either_way_are_the_same_class():
    composed, decomposed = "Poça", "Poça"
    assert decide(composed, [decomposed]).kind == CORRECT
