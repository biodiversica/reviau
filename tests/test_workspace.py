"""Opening a segments folder — and another one — without restarting."""

import pytest

from conftest import make_workspace, write_wav
from segment_reviewer.workspace import OpenError, browse


def test_a_workspace_starts_with_nothing_open():
    assert make_workspace().session is None


def test_opening_a_folder_starts_a_review_of_it(segments_dir):
    workspace = make_workspace()
    opened = workspace.open(str(segments_dir))
    assert workspace.session is opened.session
    assert opened.session.counts()["pending"] == 3
    assert opened.pattern == (3, 3, "")


def test_opening_another_folder_replaces_the_first(segments_dir, tmp_path):
    other = tmp_path / "other"
    write_wav(other / "PHYLUT" / "S_20240101_000000_0.0_5.0.wav")
    workspace = make_workspace(segments_dir)
    first = workspace.session
    closed = []
    first.backend.close = lambda: closed.append(True)

    workspace.open(str(other))
    assert workspace.session is not first
    assert workspace.session.counts()["pending"] == 1
    assert workspace.session.label_choices() == ["PHYLUT"]
    assert closed == [True]                      # the old connection is let go


@pytest.mark.parametrize("bad", ["", "   ", "/no/such/folder/anywhere"])
def test_a_folder_that_cannot_be_opened_leaves_the_review_alone(segments_dir, bad):
    workspace = make_workspace(segments_dir)
    current = workspace.session
    with pytest.raises(OpenError):
        workspace.open(bad)
    assert workspace.session is current


def test_a_file_is_not_a_folder(segments_dir):
    with pytest.raises(OpenError, match="not a folder"):
        make_workspace().open(str(segments_dir / "segment_sources.csv"))


def test_every_folder_opened_gets_the_command_line_settings(label_on_top_dir):
    workspace = make_workspace(label_depth=1)
    workspace.open(str(label_on_top_dir))
    assert workspace.session.label_choices() == ["BOAALB", "PHYLUT"]


# ── the folder picker ────────────────────────────────────────────────────────
def test_browse_lists_folders_and_marks_those_holding_clips(segments_dir):
    (segments_dir / ".hidden").mkdir()
    listing = browse(str(segments_dir / "PONTO_A"))
    assert [f["name"] for f in listing["folders"]] == ["BOAALB", "PHYLUT"]
    assert all(f["has_wavs"] for f in listing["folders"])
    assert listing["parent"] == str(segments_dir)
    top = browse(str(segments_dir))
    assert ".hidden" not in [f["name"] for f in top["folders"]]
    assert not any(f["has_wavs"] for f in top["folders"])


def test_browse_counts_the_clips_directly_inside(segments_dir):
    assert browse(str(segments_dir / "PONTO_A" / "BOAALB"))["wavs"] == 1


def test_a_half_typed_path_browses_its_nearest_folder(segments_dir):
    assert browse(str(segments_dir / "PONTO_A" / "BOA"))["path"] == str(segments_dir / "PONTO_A")


def test_with_no_path_browse_starts_where_it_is_told(segments_dir):
    assert browse("", start=str(segments_dir))["path"] == str(segments_dir)


def test_remote_folders_are_typed_not_browsed():
    with pytest.raises(OpenError, match="ssh://"):
        browse("ssh://host/data")
