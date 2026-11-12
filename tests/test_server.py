import pytest
from conftest import make_workspace, write_wav
from fastapi.testclient import TestClient

from reviau.server import create_app


def serve(workspace, token=None):
    return TestClient(create_app(workspace, workspace.config, token=token))


@pytest.fixture
def client(segments_dir):
    (segments_dir / "labels.txt").write_text("rain\nBOAALB\nPHYLUT\n", encoding="utf-8")
    workspace = make_workspace(segments_dir)
    return serve(workspace), workspace.session


def test_bootstrap_carries_everything_the_gui_needs(client):
    api, session = client
    data = api.get("/api/bootstrap").json()
    assert data["state"]["folder"] == session.backend.display
    assert {lang["code"] for lang in data["languages"]} == {"en", "pt-BR"}
    assert data["state"]["segment"]["label"] == "BOAALB"
    assert data["state"]["segment"]["folder"] == "POCA/BOAALB"
    assert data["state"]["counts"]["pending"] == 3
    assert data["state"]["labels"] == ["rain", "BOAALB", "PHYLUT"]


def test_index_page_is_served(client):
    api, _ = client
    body = api.get("/").text
    assert "app.js" in body and "reviau" in body


def test_translations_endpoint(client):
    api, _ = client
    data = api.get("/api/i18n/pt-BR").json()
    assert data["lang"] == "pt-BR"
    assert data["bundle"]["nav"]["true"].endswith("Correto")
    # An unknown tag falls back rather than failing.
    assert api.get("/api/i18n/xx").json()["lang"] == "en"


def test_navigation(client):
    api, _ = client
    assert api.post("/api/nav", json={"delta": 1}).json()["segment"]["index"] == 1
    assert api.post("/api/nav", json={"delta": -5}).json()["segment"]["index"] == 0
    assert api.post("/api/nav", json={"index": 2}).json()["segment"]["index"] == 2


ON_SCREEN = "POCA/BOAALB/POCA_20240116_190000_40.0_45.0_det3.wav"


def test_a_review_moves_the_file_and_reports_the_outcome(client, segments_dir):
    api, _ = client
    data = api.post("/api/review", json={"relpath": ON_SCREEN, "labels": ["BOAALB"]}).json()
    assert data["outcome"] == "correct"
    assert data["counts"]["pending"] == 2
    assert data["counts"]["correct"] == 1
    assert data["moved"] == f"correct/{ON_SCREEN}"
    assert (segments_dir / data["moved"]).exists()
    assert data["review_log"]["rows"] == 1


def test_the_outcome_is_worked_out_on_the_server(client):
    """No verdict is sent: leaving the prediction out of the labels is what
    makes the clip incorrect."""
    api, _ = client
    data = api.post("/api/review", json={"relpath": ON_SCREEN, "labels": ["TURDRU"]}).json()
    assert data["outcome"] == "incorrect"
    assert data["moved"].startswith("incorrect/POCA/BOAALB/")


def test_unsure_over_http(client):
    api, _ = client
    data = api.post("/api/review", json={"relpath": ON_SCREEN, "uncertain": True}).json()
    assert data["outcome"] == "uncertain"
    assert data["counts"]["uncertain"] == 1


def test_a_review_of_a_clip_no_longer_on_screen_is_a_conflict(client, segments_dir):
    api, _ = client
    res = api.post("/api/review", json={"relpath": "PONTO_A/BOAALB/gone.wav",
                                        "labels": ["BOAALB"]})
    assert res.status_code == 409
    assert (segments_dir / ON_SCREEN).exists()


def test_audio_supports_range_requests(client):
    api, _ = client
    full = api.get("/api/audio?index=0")
    assert full.status_code == 200
    assert full.headers["accept-ranges"] == "bytes"
    part = api.get("/api/audio?index=0", headers={"Range": "bytes=0-9"})
    assert part.status_code == 206
    assert part.content == full.content[:10]
    assert part.headers["content-range"] == f"bytes 0-9/{len(full.content)}"


def test_audio_out_of_range_index(client):
    api, _ = client
    assert api.get("/api/audio?index=99").status_code == 404


@pytest.mark.parametrize("spec_type", ["mel", "fft", "log"])
def test_every_frequency_axis_renders_a_png(client, spec_type):
    api, _ = client
    res = api.get(f"/api/spectrogram?index=0&type={spec_type}&fmin=0&fmax=0&db=-80")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content.startswith(b"\x89PNG")


def test_the_three_axes_draw_different_pictures(client):
    api, _ = client
    drawn = {
        t: api.get(f"/api/spectrogram?index=0&type={t}&fmin=0&fmax=0&db=-80").content
        for t in ("mel", "fft", "log")
    }
    assert len(set(drawn.values())) == 3


@pytest.mark.parametrize("fmin, fmax", [(0, 0), (0, 8000), (200, 8000)])
def test_a_log_axis_accepts_any_bound(client, fmin, fmax):
    # librosa draws the log axis on a symlog scale, so 0 Hz is a valid bound too.
    api, _ = client
    res = api.get(f"/api/spectrogram?index=0&type=log&fmin={fmin}&fmax={fmax}&db=-80")
    assert res.status_code == 200, res.text


def test_spectrogram_rejects_a_bad_type(client):
    api, _ = client
    assert api.get("/api/spectrogram?index=0&type=wavelet").status_code == 422


def test_token_guards_the_api(segments_dir):
    api = serve(make_workspace(segments_dir), token="s3cret")
    assert api.get("/api/state").status_code == 401
    assert api.get("/health").status_code == 200
    assert api.get("/api/state", headers={"x-reviau-token": "s3cret"}).status_code == 200
    # The token in the query string is exchanged for a cookie, then dropped.
    landing = api.get("/?token=s3cret", follow_redirects=False)
    assert landing.status_code == 303
    assert api.get("/api/state").status_code == 200


# ── the editable label list over HTTP ────────────────────────────────────────
def test_labels_endpoint_reports_the_list_and_where_it_lives(client):
    api, _ = client
    data = api.get("/api/labels").json()
    assert data["labels"] == ["rain", "BOAALB", "PHYLUT"]
    assert data["persisted"] is True
    assert data["path"].endswith("labels.txt")


def test_adding_and_removing_labels_from_the_gui(client, segments_dir):
    api, _ = client
    assert api.post("/api/labels", json={"add": "TURDRU"}).json()["labels"][-1] == "TURDRU"
    data = api.post("/api/labels", json={"remove": "rain"}).json()
    assert data["labels"] == ["BOAALB", "PHYLUT", "TURDRU"]
    # The edit is on disk, so the next session starts from it.
    assert (segments_dir / "labels.txt").read_text().split() == ["BOAALB", "PHYLUT", "TURDRU"]
    # The reply carries the fresh state, so the buttons redraw in one round trip.
    assert data["state"]["labels"] == data["labels"]


def test_replacing_the_list_from_the_gui(client):
    api, _ = client
    data = api.post("/api/labels", json={"labels": [" chuva ", "rain", "chuva", ""]}).json()
    assert data["labels"] == ["chuva", "rain"]


def test_multi_label_is_advertised_as_on(client):
    api, _ = client
    assert api.get("/api/bootstrap").json()["multi_label"] is True


def test_two_labels_are_refused_when_multi_label_is_off(segments_dir):
    api = serve(make_workspace(segments_dir, multi_label=False))
    res = api.post("/api/review", json={"labels": ["BOAALB", "PHYLUT"]})
    assert res.status_code == 400


def test_the_client_scripts_are_revalidated_on_every_load(client):
    """A cached app.js outliving an upgrade calls endpoints that are gone."""
    api, _ = client
    for path in ("/static/app.js", "/static/lib.js", "/static/styles.css"):
        assert api.get(path).headers["cache-control"] == "no-cache", path



# ── opening a folder from the GUI ────────────────────────────────────────────
def test_the_gui_can_start_with_no_folder_open():
    api = serve(make_workspace())
    data = api.get("/api/bootstrap").json()
    assert data["state"]["folder"] is None
    assert data["state"]["segment"] is None
    assert api.get("/api/state").json()["folder"] is None


def test_clip_calls_need_a_folder_open():
    api = serve(make_workspace())
    assert api.post("/api/review", json={"labels": []}).status_code == 409
    assert api.post("/api/nav", json={"delta": 1}).status_code == 409
    assert api.post("/api/rescan").status_code == 409
    assert api.get("/api/audio?index=0").status_code == 409


def test_opening_a_folder_over_http(segments_dir):
    api = serve(make_workspace())
    data = api.post("/api/open", json={"path": str(segments_dir)}).json()
    assert data["folder"] == str(segments_dir)
    assert data["counts"]["pending"] == 3
    assert data["segment"]["label"] == "BOAALB"
    assert data["pattern"] == {"matched": 3, "total": 3, "example": ""}


def test_switching_folders_over_http(segments_dir, tmp_path):
    other = tmp_path / "other"
    write_wav(other / "PHYLUT" / "S_20240101_000000_0.0_5.0.wav")
    api = serve(make_workspace(segments_dir))
    data = api.post("/api/open", json={"path": str(other)}).json()
    assert data["folder"] == str(other)
    assert data["counts"]["pending"] == 1
    assert data["labels"] == ["PHYLUT"]


def test_a_bad_folder_is_refused_and_the_review_carries_on(segments_dir):
    api = serve(make_workspace(segments_dir))
    res = api.post("/api/open", json={"path": "/no/such/folder"})
    assert res.status_code == 400
    assert api.get("/api/state").json()["folder"] == str(segments_dir)


def test_browse_over_http(segments_dir):
    api = serve(make_workspace())
    data = api.get("/api/browse", params={"path": str(segments_dir)}).json()
    assert [f["name"] for f in data["folders"]] == ["POCA", "PONTO_A"]
    assert api.get("/api/browse", params={"path": "ssh://h/x"}).status_code == 400


def test_browse_starts_in_the_open_folder(segments_dir):
    api = serve(make_workspace(segments_dir))
    assert api.get("/api/browse").json()["path"] == str(segments_dir)


# ── reading settings over HTTP ───────────────────────────────────────────────
def test_the_state_carries_the_folders_reading_settings(client):
    api, _ = client
    reading = api.get("/api/state").json()["reading"]
    assert reading == {"filename_pattern": "default", "datetime_format": "%Y%m%d%H%M%S",
                       "label_from": "auto", "label_depth": 0}
    boot = api.get("/api/bootstrap").json()
    assert boot["presets"] == ["default", "vector-search"]
    assert boot["label_from_choices"] == ["auto", "folder", "filename", "none"]


def test_a_preview_reads_the_pending_names_without_applying_anything(client, segments_dir):
    api, _ = client
    data = api.post("/api/reading/preview", json={"filename_pattern": "[site]_[extra]"}).json()
    assert (data["matched"], data["total"]) == (3, 3)
    assert data["samples"][0]["name"].endswith(".wav")
    assert data["label_from"] == "folder"
    assert api.get("/api/state").json()["reading"]["filename_pattern"] == "default"
    assert not (segments_dir / "reviau.json").exists()


def test_a_preview_of_unusable_settings_says_why(client):
    api, _ = client
    res = api.post("/api/reading/preview", json={"filename_pattern": "[site]_[speceis]"})
    assert res.status_code == 400
    assert "speceis" in res.json()["detail"]


def test_applying_settings_over_http(label_on_top_dir):
    api = serve(make_workspace(label_on_top_dir))
    data = api.post("/api/reading", json={"label_depth": 1}).json()
    assert data["reading"]["label_depth"] == 1
    assert data["labels"] == ["BOAALB", "PHYLUT"]
    assert (label_on_top_dir / "reviau.json").exists()


def test_reading_settings_need_a_folder_open():
    api = serve(make_workspace())
    assert api.post("/api/reading/preview", json={}).status_code == 409
    assert api.post("/api/reading", json={}).status_code == 409
