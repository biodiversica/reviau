import csv

import pytest
from conftest import TEMPLATE, goto_name, make_session, write_wav

from reviau.review import StaleSegment

FIRST = "PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav"
FIRST_NAME = "PONTO_A_20240115_053000_12.0_17.0_det1.wav"


def accept(session):
    """Review the clip on screen as holding exactly what it was predicted to."""
    return session.review([session.view().label])


def nothing_reviewed(pending):
    return {"pending": pending, "correct": 0, "incorrect": 0, "uncertain": 0, "labelled": 0}


def test_collect_skips_verdict_folders(segments_dir):
    write_wav(segments_dir / "correct" / "S_20240101_000000_0.0_5.0.wav")
    write_wav(segments_dir / "incorrect" / "X" / "S_20240101_000000_0.0_5.0.wav")
    session = make_session(segments_dir)
    assert len(session.segments) == 3
    assert all("/correct/" not in p and "/incorrect/" not in p for p in session.segments)


def test_counts(session):
    assert session.counts() == nothing_reviewed(3)


def test_the_view_reports_what_the_folder_and_name_say(session):
    goto_name(session, FIRST)
    view = session.view()
    assert view.label == "BOAALB"
    assert view.label_from == "folder"
    assert view.folder == "PONTO_A/BOAALB"
    assert view.site == "PONTO A"
    assert view.recorded_at == "2024-01-15 05:30:00"
    assert (view.det_start, view.det_end) == (12.0, 17.0)
    assert view.score is None


# ── labels offered ───────────────────────────────────────────────────────────
def test_label_choices_are_the_folder_names(session):
    assert session.label_choices() == ["BOAALB", "PHYLUT"]


def test_a_shared_list_file_gives_every_folder_the_same_labels(segments_dir, tmp_path):
    """One fixed list for several collections: --labels-file with an absolute path."""
    shared = tmp_path / "classes.txt"
    shared.write_text("rain\nBOAALB\n", encoding="utf-8")
    other = tmp_path / "other"
    write_wav(other / "PHYLUT" / "S_20240101_000000_0.0_5.0.wav")
    for folder in (segments_dir, other):
        assert make_session(folder, labels_file=str(shared)).label_choices() == ["rain", "BOAALB"]


def test_site_subfolders_are_not_offered_as_labels(label_on_top_dir):
    """BOAALB/PONTO_A/clip.wav — the sites inside a class folder are not classes."""
    session = make_session(label_on_top_dir, label_depth=1)
    assert session.label_choices() == ["BOAALB", "PHYLUT"]


def test_without_the_depth_those_subfolders_would_be_taken_for_labels(label_on_top_dir):
    assert make_session(label_on_top_dir).label_choices() == ["PHYLUT", "POCA", "PONTO A"]


# ── a name shape no preset fits ──────────────────────────────────────────────
def test_a_template_fills_in_every_fact_the_gui_shows(templated_dir):
    """Without it the name half-matches and the GUI shows facts read off the
    incorrect tokens; with it every field is the one it says it is."""
    session = make_session(templated_dir, filename_pattern=TEMPLATE, label_from="filename")
    goto_name(session, "BOAALB")
    view = session.view()
    assert view.label == "BOAALB"
    assert view.site == "PONTO A"
    assert view.recorded_at == "2024-01-15 05:30:00"
    assert (view.det_start, view.det_end) == (12.0, 17.0)
    assert view.score == 0.873
    assert view.extra is None


def test_a_correction_on_a_templated_name_is_appended_to_it(templated_dir):
    """The prediction in the name is what the folder is filed under; what the
    clip really holds is added at the end, the original name kept intact."""
    session = make_session(templated_dir, filename_pattern=TEMPLATE, label_from="filename")
    goto_name(session, "BOAALB")
    session.review(["TURDRU"])
    assert (templated_dir / "incorrect" / "BOAALB"
            / "PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873_TURDRU.wav").exists()


def test_the_same_layout_read_by_its_folders_instead(templated_dir):
    """--label-from folder with --label-depth 1 labels by the top folder, and
    files the clip under that label alone: the site/day folders it was found in
    are not rebuilt, since the file name already carries both."""
    session = make_session(
        templated_dir, filename_pattern=TEMPLATE, label_from="folder", label_depth=1
    )
    assert session.label_choices() == ["BOAALB", "PHYLUT"]
    goto_name(session, "BOAALB")
    assert session.view().site == "PONTO A"      # still read from the name
    accept(session)
    moved = templated_dir / "correct" / "BOAALB"
    assert [p.name for p in moved.rglob("*.wav")] == [
        "PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav"
    ]
    assert [p.name for p in moved.iterdir()] == [
        "PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav"
    ]


def test_a_correction_under_label_depth_drops_the_folders_below_the_label(templated_dir):
    session = make_session(
        templated_dir, filename_pattern=TEMPLATE, label_from="folder", label_depth=1
    )
    goto_name(session, "BOAALB")
    session.review(["TURDRU"])
    assert [p.name for p in (templated_dir / "incorrect" / "BOAALB").iterdir()] == [
        "PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873_TURDRU.wav"
    ]


def test_a_pattern_that_fits_nothing_is_reported(templated_dir):
    """A incorrect pattern shows up as clips with no site, time or score; the count
    of names it actually read is what says so at start-up."""
    session = make_session(templated_dir, filename_pattern="default", label_from="folder")
    matched, total, example = session.pattern_report()
    assert (matched, total) == (0, 2)
    assert example.endswith(".wav")


def test_a_pattern_that_fits_reports_every_name(templated_dir):
    session = make_session(templated_dir, filename_pattern=TEMPLATE, label_from="filename")
    assert session.pattern_report() == (2, 2, "")


# ── where the reviewed clips are written ─────────────────────────────────────
def test_output_sends_the_verdict_folders_elsewhere(segments_dir, tmp_path):
    out = tmp_path / "reviewed"
    session = make_session(segments_dir, output=str(out))
    goto_name(session, FIRST)
    accept(session)
    assert (out / "correct" / "PONTO_A" / "BOAALB").is_dir()
    assert (out / "reviews.csv").exists()
    assert not (segments_dir / "correct").exists()
    assert not (segments_dir / "reviews.csv").exists()
    assert not (segments_dir / "PONTO_A" / "BOAALB").exists()   # emptied and pruned


def test_a_relative_output_is_read_against_the_segments_folder(segments_dir):
    session = make_session(segments_dir, output="reviewed")
    goto_name(session, FIRST)
    accept(session)
    assert (segments_dir / "reviewed" / "correct" / "PONTO_A" / "BOAALB").is_dir()


def test_an_output_inside_the_segments_folder_is_not_offered_for_review(segments_dir):
    """Its own reviewed clips must not come back as pending on the next scan."""
    session = make_session(segments_dir, output="reviewed")
    goto_name(session, FIRST)
    accept(session)
    session.rescan()
    assert session.counts() == {**nothing_reviewed(2), "correct": 1}


def test_resuming_counts_what_an_earlier_run_wrote_to_the_output(segments_dir, tmp_path):
    out = tmp_path / "reviewed"
    accept(make_session(segments_dir, output=str(out)))
    resumed = make_session(segments_dir, output=str(out))
    assert resumed.counts() == {**nothing_reviewed(2), "correct": 1}


def test_the_annotation_table_is_written_to_the_output_folder(segments_dir, tmp_path):
    out = tmp_path / "reviewed"
    session = make_session(segments_dir, output=str(out), save_annotations=True)
    goto_name(session, FIRST)
    accept(session)
    assert (out / "annotations.csv").exists()
    assert not (segments_dir / "annotations.csv").exists()


# ── where a review files a clip ──────────────────────────────────────────────
def test_a_correct_clip_keeps_its_path_under_correct(session, segments_dir):
    goto_name(session, FIRST)
    assert accept(session)["outcome"] == "correct"
    assert (segments_dir / "correct" / FIRST).exists()
    assert len(session.segments) == 2


def test_a_wrong_clip_is_filed_under_what_was_predicted(session, segments_dir):
    """incorrect/PONTO_A/BOAALB/ holds exactly the clips the model called BOAALB and
    got incorrect — whatever they really are, which is in the log."""
    goto_name(session, FIRST)
    assert session.review(["TURDRU"])["outcome"] == "incorrect"
    moved = segments_dir / "incorrect" / "PONTO_A" / "BOAALB"
    # ...and its name gains what it really is.
    assert [p.name for p in moved.glob("*.wav")] == [
        "PONTO_A_20240115_053000_12.0_17.0_det1_TURDRU.wav"
    ]


def test_every_label_given_instead_is_appended_in_order(session, segments_dir):
    goto_name(session, FIRST)
    session.review(["TURDRU", "PHYLUT"])
    assert (segments_dir / "incorrect" / "PONTO_A" / "BOAALB"
            / "PONTO_A_20240115_053000_12.0_17.0_det1_TURDRU_PHYLUT.wav").exists()


def test_a_label_with_a_space_is_appended_as_one_token(session, segments_dir):
    goto_name(session, FIRST)
    session.review(["chuva forte"])
    assert (segments_dir / "incorrect" / "PONTO_A" / "BOAALB"
            / "PONTO_A_20240115_053000_12.0_17.0_det1_chuva_forte.wav").exists()


def test_a_clip_holding_nothing_on_the_list_is_wrong(session, segments_dir):
    goto_name(session, FIRST)
    assert session.review([])["outcome"] == "incorrect"
    assert (segments_dir / "incorrect" / FIRST).exists()


def test_a_second_species_leaves_a_correct_clip_in_correct(session, segments_dir):
    """Two labels are a fact about the clip, not a third kind of verdict."""
    goto_name(session, FIRST)
    assert session.review(["BOAALB", "PHYLUT"])["outcome"] == "correct"
    # Only the label added beyond the prediction goes on the name.
    assert (segments_dir / "correct" / "PONTO_A" / "BOAALB"
            / "PONTO_A_20240115_053000_12.0_17.0_det1_PHYLUT.wav").exists()
    assert session.counts()["correct"] == 1


def test_a_plain_correct_keeps_its_name(session, segments_dir):
    goto_name(session, FIRST)
    accept(session)
    assert (segments_dir / "correct" / FIRST).exists()


def test_unsure_keeps_its_name_whatever_was_selected(session, segments_dir):
    goto_name(session, FIRST)
    session.review(["TURDRU"], uncertain=True)
    assert (segments_dir / "uncertain" / FIRST).exists()


def test_unsure_is_filed_apart_whatever_is_selected(session, segments_dir):
    goto_name(session, FIRST)
    assert session.review(["BOAALB"], uncertain=True)["outcome"] == "uncertain"
    assert (segments_dir / "uncertain" / FIRST).exists()
    assert session.counts() == {**nothing_reviewed(2), "uncertain": 1}


def test_a_site_folder_under_the_label_is_not_rebuilt(label_on_top_dir):
    """BOAALB/PONTO_A/det1.wav rejected lands in incorrect/BOAALB/ — the site folder
    is not carried over; the clip's name already names the site."""
    session = make_session(label_on_top_dir, label_depth=1)
    goto_name(session, "det1")
    assert session.view().label == "BOAALB"
    session.review(["TURDRU"])
    moved = label_on_top_dir / "incorrect" / "BOAALB"
    assert [p.name for p in moved.iterdir()] == [
        "PONTO_A_20240115_053000_12.0_17.0_det1_TURDRU.wav"
    ]


def test_the_folders_a_clip_leaves_behind_are_removed(label_on_top_dir):
    """The last clip out of BOAALB/PONTO_A takes the empty folder with it."""
    session = make_session(label_on_top_dir, label_depth=1)
    goto_name(session, "det1")
    accept(session)
    assert not (label_on_top_dir / "BOAALB" / "PONTO_A").exists()
    assert (label_on_top_dir / "BOAALB" / "POCA").is_dir()   # still has its clip


def test_pruning_stops_at_the_segments_root(segments_dir):
    """Reviewing the last pending clip empties the tree but keeps the root."""
    session = make_session(segments_dir)
    while session.segments:
        accept(session)
    assert segments_dir.is_dir()
    assert not (segments_dir / "PONTO_A").exists()
    assert not (segments_dir / "POCA").exists()


def test_a_folder_holding_anything_else_is_left_alone(segments_dir):
    """A folder that still holds a pending clip, or any other file, stays."""
    (segments_dir / "PONTO_A" / "BOAALB" / "notes.txt").write_text("keep me")
    session = make_session(segments_dir)
    goto_name(session, FIRST)
    accept(session)
    assert (segments_dir / "PONTO_A" / "BOAALB" / "notes.txt").exists()


def test_a_clip_with_no_prediction_is_labelled_not_judged(segments_dir):
    write_wav(segments_dir / "LOOSE_20240101_000000_0.0_5.0.wav")
    session = make_session(segments_dir)
    goto_name(session, "LOOSE_")
    assert session.review(["rain"])["outcome"] == "labelled"
    # With no prediction every label given is new, so all go on the name.
    assert (segments_dir / "labelled" / "LOOSE_20240101_000000_0.0_5.0_rain.wav").exists()
    assert session.counts()["labelled"] == 1


def test_label_from_none_keeps_the_whole_path(segments_dir):
    session = make_session(segments_dir, label_from="none")
    goto_name(session, FIRST)
    assert session.view().label == ""
    session.review([])
    assert (segments_dir / "labelled" / FIRST).exists()


def test_a_collision_gets_a_suffix_instead_of_overwriting(segments_dir):
    write_wav(segments_dir / "incorrect" / FIRST)
    session = make_session(segments_dir)
    goto_name(session, FIRST)
    session.review([])
    names = sorted(p.name for p in (segments_dir / "incorrect" / "PONTO_A" / "BOAALB").glob("*.wav"))
    assert names == [FIRST_NAME, "PONTO_A_20240115_053000_12.0_17.0_det1_2.wav"]


def test_a_review_of_a_clip_no_longer_on_screen_is_refused(session, segments_dir):
    goto_name(session, FIRST)
    with pytest.raises(StaleSegment):
        session.review(["BOAALB"], relpath="POCA/BOAALB/somewhere_else.wav")
    assert (segments_dir / FIRST).exists()
    assert session.review(["BOAALB"], relpath=FIRST)["outcome"] == "correct"


def test_one_label_per_segment_when_multi_label_is_off(segments_dir):
    session = make_session(segments_dir, multi_label=False)
    goto_name(session, FIRST)
    with pytest.raises(ValueError):
        session.review(["BOAALB", "PHYLUT"])
    assert (segments_dir / FIRST).exists()


def test_a_log_that_cannot_be_written_undoes_the_move(session, segments_dir, monkeypatch):
    """A clip filed with no row in the log is a verdict nobody can read back."""
    goto_name(session, FIRST)

    def broken(_review):
        raise OSError("disk full")

    monkeypatch.setattr(session.log, "append", broken)
    with pytest.raises(OSError):
        session.review(["TURDRU"])
    assert (segments_dir / FIRST).exists()
    assert not list((segments_dir / "incorrect").rglob("*.wav"))
    assert len(session.segments) == 3
    assert session.view().relpath == FIRST


# ── the vector-search preset ─────────────────────────────────────────────────
def test_vector_search_preset_reads_the_label_from_the_name(vector_search_dir):
    session = make_session(vector_search_dir,
                           filename_pattern="vector-search", label_from="filename")
    goto_name(session, "PONTO_A_20240115_053000")
    view = session.view()
    assert (view.label, view.score, view.label_from) == ("BOAALB", 0.873, "filename")


def test_vector_search_files_flat_under_the_prediction(vector_search_dir):
    session = make_session(vector_search_dir,
                           filename_pattern="vector-search", label_from="filename")
    goto_name(session, "PONTO_A_20240115_053000")
    session.review(["TURDRU"])
    out = vector_search_dir / "incorrect" / "BOAALB"
    assert [p.name for p in out.glob("*.wav")] == [
        "PONTO_A_20240115_053000_12.0-17.0s_0.873_BOAALB_TURDRU.wav"
    ]


def test_vector_search_second_species_stays_correct(vector_search_dir):
    session = make_session(vector_search_dir,
                           filename_pattern="vector-search", label_from="filename")
    goto_name(session, "PONTO_A_20240115_053000")
    session.review(["BOAALB", "PHYLUT"])
    assert [p.name for p in (vector_search_dir / "correct" / "BOAALB").glob("*.wav")] == [
        "PONTO_A_20240115_053000_12.0-17.0s_0.873_BOAALB_PHYLUT.wav"
    ]


def test_verdict_folders_do_not_follow_the_interface_language(segments_dir):
    session = make_session(segments_dir, lang="pt-BR")
    accept(session)
    assert list((segments_dir / "correct").rglob("*.wav"))


# ── navigation ───────────────────────────────────────────────────────────────
def test_navigation_stays_in_range(session):
    session.navigate(-5)
    assert session.index == 0
    session.navigate(+99)
    assert session.index == len(session.segments) - 1


def test_rescan_keeps_the_current_segment(session, segments_dir):
    session.navigate(+1)
    current = session.view().name
    write_wav(segments_dir / "NEW" / "AAA_20240101_000000_0.0_5.0.wav")
    session.rescan()
    assert session.view().name == current
    assert len(session.segments) == 4
    # A rescan finds the new folder's label but does not push it onto the list:
    # the list is the reviewer's to edit, so nothing is added behind their back.
    assert "NEW" in session.discovered_labels()
    assert "NEW" not in session.label_choices()


# ── the review log ───────────────────────────────────────────────────────────
def read_csv(path):
    return list(csv.DictReader(path.open(encoding="utf-8")))


def test_every_review_is_logged_with_what_was_predicted(segments_dir):
    session = make_session(segments_dir)
    goto_name(session, FIRST)
    session.review(["BOAALB", "PHYLUT"])
    goto_name(session, "POCA_20240116_190000")
    session.review(["TURDRU"])
    goto_name(session, "PHYLUT")
    session.review([], uncertain=True)

    rows = read_csv(segments_dir / "reviews.csv")
    assert [(r["predicted"], r["outcome"], r["labels"], r["added"]) for r in rows] == [
        ("BOAALB", "correct", "BOAALB;PHYLUT", "PHYLUT"),
        ("BOAALB", "incorrect", "TURDRU", "TURDRU"),
        ("PHYLUT", "uncertain", "", ""),
    ]
    first = rows[0]
    assert first["source"] == FIRST
    # The log points at the file as it was written, new label and all.
    assert first["destination"] == (
        "correct/PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1_PHYLUT.wav"
    )
    assert first["site"] == "PONTO A"
    # The manifest names the recording this clip came from.
    assert first["recording"] == "PONTO_A_20240115_053000.wav"
    assert first["reviewed_at"]
    assert float(first["end_time"]) - float(first["start_time"]) == 0.5


def test_the_log_is_written_without_the_annotation_table(segments_dir):
    session = make_session(segments_dir)
    accept(session)
    assert len(read_csv(segments_dir / "reviews.csv")) == 1
    assert not (segments_dir / "annotations.csv").exists()


def test_the_log_carries_the_score_the_name_gave(vector_search_dir):
    session = make_session(vector_search_dir,
                           filename_pattern="vector-search", label_from="filename")
    goto_name(session, "PONTO_A_20240115_053000")
    accept(session)
    assert read_csv(vector_search_dir / "reviews.csv")[0]["score"] == "0.873"


# ── annotations ──────────────────────────────────────────────────────────────
def test_annotations_record_one_row_per_label(segments_dir):
    session = make_session(segments_dir, multi_label=True, save_annotations=True)
    goto_name(session, FIRST)
    session.review(["BOAALB", "PHYLUT"])
    rows = read_csv(segments_dir / "annotations.csv")
    assert [r["label"] for r in rows] == ["BOAALB", "PHYLUT"]
    assert {r["site"] for r in rows} == {"PONTO A"}
    assert {r["file"] for r in rows} == {"PONTO_A_20240115_053000.wav"}
    # A 5 s window padded out to a 0.5 s clip: the clip is centred on the window.
    assert float(rows[0]["end_time"]) - float(rows[0]["start_time"]) == 0.5


def test_annotations_hold_what_the_clip_really_is(segments_dir):
    session = make_session(segments_dir, save_annotations=True)
    goto_name(session, FIRST)
    accept(session)
    goto_name(session, "POCA_20240116_190000")
    session.review(["TURDRU"])
    rows = read_csv(segments_dir / "annotations.csv")
    assert [r["label"] for r in rows] == ["BOAALB", "TURDRU"]
    # Only the first clip is in the manifest, so the second row names no recording.
    assert rows[1]["file"] == ""
    assert session.annotations.state.rows_without_recording == 1


def test_a_rejected_prediction_is_never_annotated(segments_dir):
    """The old bug: pressing False on an untouched clip wrote the very label the
    reviewer had just rejected into the table, as if it were confirmed."""
    session = make_session(segments_dir, save_annotations=True)
    goto_name(session, FIRST)
    session.review([])
    goto_name(session, "PHYLUT")
    session.review(["PHYLUT"], uncertain=True)
    assert not (segments_dir / "annotations.csv").exists()
    assert session.annotations.state.rows == 0
    assert len(read_csv(segments_dir / "reviews.csv")) == 2


def test_a_blank_annotations_path_falls_back_inside_the_segments_folder(segments_dir):
    session = make_session(segments_dir, save_annotations=True, annotations_path="  ")
    assert session.annotations.enabled
    assert session.annotations.state.path.endswith("annotations.csv")


# ── the editable label list ──────────────────────────────────────────────────
def test_the_list_is_seeded_from_the_collection_and_written_once_in_use(segments_dir):
    session = make_session(segments_dir)
    assert session.label_choices() == ["BOAALB", "PHYLUT"]
    assert not (segments_dir / "labels.txt").exists()      # opening writes nothing
    accept(session)
    assert (segments_dir / "labels.txt").read_text().split() == ["BOAALB", "PHYLUT"]


def test_a_stored_list_wins_over_what_the_collection_uses(segments_dir):
    (segments_dir / "labels.txt").write_text("rain\nTURDRU\n", encoding="utf-8")
    session = make_session(segments_dir)
    assert session.label_choices() == ["rain", "TURDRU"]


def test_reviewing_one_folder_never_rewrites_another_folders_list(segments_dir, tmp_path):
    """The bug --labels had once folders could be switched: every folder opened
    in the session had its own labels.txt replaced by the command-line list."""
    other = tmp_path / "other"
    write_wav(other / "PHYLUT" / "S_20240101_000000_0.0_5.0.wav")
    (other / "labels.txt").write_text("PHYLUT\nTURDRU\nrain\n", encoding="utf-8")
    accept(make_session(segments_dir))
    session = make_session(other)
    assert session.label_choices() == ["PHYLUT", "TURDRU", "rain"]
    accept(session)
    assert (other / "labels.txt").read_text().split() == ["PHYLUT", "TURDRU", "rain"]


def test_comments_and_blank_lines_are_ignored(segments_dir):
    (segments_dir / "labels.txt").write_text("# my labels\n\nrain\n  TURDRU  \n", encoding="utf-8")
    assert make_session(segments_dir).label_choices() == ["rain", "TURDRU"]


def test_editing_the_list_persists(segments_dir):
    session = make_session(segments_dir)
    session.labels.add("TURDRU")
    session.labels.remove("PHYLUT")
    assert session.label_choices() == ["BOAALB", "TURDRU"]
    assert make_session(segments_dir).label_choices() == ["BOAALB", "TURDRU"]


def test_replacing_the_list_dedupes_and_keeps_order(segments_dir):
    session = make_session(segments_dir)
    assert session.labels.replace([" b ", "a", "b", ""]) == ["b", "a"]


def test_a_removed_label_still_works_when_a_clip_carries_it(segments_dir):
    """Trimming the list must never block a verdict on a clip that uses the label."""
    session = make_session(segments_dir)
    session.labels.replace([])
    goto_name(session, FIRST)
    assert session.view().label == "BOAALB"          # from its folder, not the list
    accept(session)
    assert (segments_dir / "correct" / FIRST).exists()


def test_persistence_can_be_switched_off(segments_dir):
    session = make_session(segments_dir, labels_file="")
    session.labels.add("TURDRU")
    assert "TURDRU" in session.label_choices()
    assert not (segments_dir / "labels.txt").exists()


def test_a_folder_that_cannot_be_written_is_reported_not_fatal(segments_dir, monkeypatch):
    session = make_session(segments_dir)
    monkeypatch.setattr(session.backend, "write_bytes",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("read-only")))
    session.labels.add("TURDRU")
    assert "TURDRU" in session.label_choices()       # the session carries on
    assert "read-only" in session.labels.error
    assert session.labels.persisted is False


def test_multi_label_is_on_by_default(segments_dir):
    session = make_session(segments_dir)
    assert session.config.multi_label is True


def test_opening_a_folder_writes_nothing_to_it(segments_dir):
    """A folder opened by mistake from the GUI must be left as it was found."""
    before = sorted(p.relative_to(segments_dir) for p in segments_dir.rglob("*"))
    make_session(segments_dir, save_annotations=True)
    assert sorted(p.relative_to(segments_dir) for p in segments_dir.rglob("*")) == before


def test_the_first_review_makes_only_the_folder_it_needs(segments_dir):
    session = make_session(segments_dir)
    goto_name(session, FIRST)
    accept(session)
    assert (segments_dir / "correct").is_dir()
    for name in ("incorrect", "uncertain", "labelled", "multi"):
        assert not (segments_dir / name).exists()
