"""Reading settings: per folder, validated, kept in reviau/settings.json, previewed."""

import json

import pytest
from conftest import TEMPLATE, make_workspace, write_text

from reviau.config import WORK_DIR
from reviau.reading import READING_FILE, Reading, ReadingError, pattern_has_label


def test_presets_and_templates_say_whether_they_carry_a_label():
    assert pattern_has_label("default") is False
    assert pattern_has_label("vector-search") is True
    assert pattern_has_label(r"^(?P<label>\w+)_(?P<site>\w+)$") is True
    assert pattern_has_label(r"^(?P<site>\w+)$") is False
    assert pattern_has_label("[site]_YYYYMMDD_HHMMSS_[label]_[score]") is True
    assert pattern_has_label("[site]_YYYYMMDD_HHMMSS_[extra]") is False


def test_automatic_label_source_follows_the_pattern():
    assert Reading().resolved_label_from == "folder"
    assert Reading(filename_pattern="vector-search").resolved_label_from == "filename"
    assert Reading(filename_pattern="vector-search", label_from="folder").resolved_label_from == "folder"


@pytest.mark.parametrize("reading, message", [
    (Reading(filename_pattern="(unclosed"), "regular expression"),
    (Reading(filename_pattern="[site]_[speceis]"), "speceis"),
    (Reading(label_from="telepathy"), "label source"),
    (Reading(label_depth=-1), "negative"),
    (Reading(label_depth="two"), "whole number"),
])
def test_unusable_settings_are_refused_with_the_reason(reading, message):
    with pytest.raises(ReadingError, match=message):
        reading.validated()


def test_blank_fields_fall_back_to_the_defaults():
    cleaned = Reading(filename_pattern="  ", datetime_format="").validated()
    assert cleaned == Reading()


def test_a_template_is_accepted():
    assert Reading(filename_pattern=TEMPLATE).validated().filename_pattern == TEMPLATE


# ── kept per folder ──────────────────────────────────────────────────────────
def test_a_folder_opens_with_the_settings_it_stores(label_on_top_dir):
    write_text(label_on_top_dir / WORK_DIR / READING_FILE, json.dumps({"label_depth": 1}))
    workspace = make_workspace(label_on_top_dir)
    assert workspace.session.config.label_depth == 1
    assert workspace.session.label_choices() == ["BOAALB", "PHYLUT"]


def test_without_a_settings_file_the_defaults_are_used(segments_dir):
    workspace = make_workspace(segments_dir)
    assert workspace.session.config.reading == Reading()
    assert not (segments_dir / WORK_DIR).exists()     # opening writes nothing


def test_applying_settings_saves_them_and_rereads_the_folder(label_on_top_dir):
    workspace = make_workspace(label_on_top_dir)
    assert workspace.session.label_choices() == ["PHYLUT", "POCA", "PONTO A"]
    workspace.apply_reading(Reading(label_depth=1))
    assert workspace.session.label_choices() == ["BOAALB", "PHYLUT"]
    stored = json.loads((label_on_top_dir / WORK_DIR / READING_FILE).read_text())
    assert stored["label_depth"] == 1
    # The next session opens the folder with them.
    assert make_workspace(label_on_top_dir).session.config.label_depth == 1


def test_each_folder_keeps_its_own_settings(label_on_top_dir, segments_dir):
    workspace = make_workspace(label_on_top_dir)
    workspace.apply_reading(Reading(label_depth=1))
    workspace.open(str(segments_dir))
    assert workspace.session.config.label_depth == 0
    workspace.open(str(label_on_top_dir))
    assert workspace.session.config.label_depth == 1


def test_a_broken_settings_file_opens_with_the_defaults_and_says_so(segments_dir):
    write_text(segments_dir / WORK_DIR / READING_FILE, "{ not json")
    workspace = make_workspace(segments_dir)
    assert workspace.session.config.reading == Reading()
    assert READING_FILE in workspace.reading_error


def test_settings_that_cannot_be_saved_still_apply(label_on_top_dir, monkeypatch):
    workspace = make_workspace(label_on_top_dir)
    monkeypatch.setattr("reviau.workspace.save_reading",
                        lambda *a: (_ for _ in ()).throw(OSError("read-only")))
    workspace.apply_reading(Reading(label_depth=1))
    assert workspace.session.config.label_depth == 1
    assert "read-only" in workspace.reading_error


def test_unusable_settings_change_nothing(segments_dir):
    workspace = make_workspace(segments_dir)
    current = workspace.session
    with pytest.raises(ReadingError):
        workspace.apply_reading(Reading(filename_pattern="(unclosed"))
    assert workspace.session is current
    assert not (segments_dir / WORK_DIR).exists()
