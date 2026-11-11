"""The HTTP layer: a small JSON API plus the single-page GUI it drives."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__, i18n
from .config import ReviewConfig
from .outcome import OUTCOMES
from .review import ReviewSession, StaleSegment
from .spectrogram import SPEC_TYPES, SpectrogramError
from .storage import LocalBackend
from .workspace import OpenError, Workspace, browse

WEB_DIR = Path(__file__).parent / "web"
TOKEN_COOKIE = "segrev_token"
TOKEN_HEADER = "x-segrev-token"


class ReviewBody(BaseModel):
    """What the reviewer heard in the clip on screen.

    No verdict is sent: whether the prediction was right follows from *labels*
    and the clip's own label, worked out on the server in one place.
    """

    relpath: str | None = None
    labels: list[str] = []
    unsure: bool = False


class NavBody(BaseModel):
    delta: int = 0
    index: int | None = None


class OpenBody(BaseModel):
    """A segments folder to open: a local path, or ssh://[user@]host[:port]/path."""

    path: str


class LabelsBody(BaseModel):
    """Either the whole list, or one label to add or drop."""

    labels: list[str] | None = None
    add: str | None = None
    remove: str | None = None


def _annotation_payload(session: ReviewSession) -> dict:
    state = session.annotations.state
    return {
        "enabled": state.enabled,
        "path": state.path,
        "rows": state.rows,
        "rows_without_recording": state.rows_without_recording,
        "have_sources": state.have_sources,
        "error": state.error,
        "no_path": bool(state.extra.get("no_path")),
        "read_error": state.extra.get("read_error", ""),
    }


def _labels_payload(session: ReviewSession) -> dict:
    store = session.labels
    return {
        "labels": store.labels,
        "path": store.path,
        "persisted": store.persisted,
        "error": store.error,
    }


def _state_payload(workspace: Workspace) -> dict:
    session = workspace.session
    if session is None:
        # No folder open yet: the GUI shows the folder box and nothing else.
        return {"folder": None, "output": None, "segment": None, "counts": {},
                "labels": [], "label_store": {}, "annotations": {}, "review_log": None}
    view = session.view()
    return {
        "folder": session.backend.display,
        "output": session.output_root,
        "segment": None if view is None else view.__dict__,
        "counts": session.counts(),
        "labels": session.label_choices(),
        "label_store": _labels_payload(session),
        "annotations": _annotation_payload(session),
        "review_log": {"path": session.log.path, "rows": session.log.rows},
    }


def parse_local(session: ReviewSession) -> bool:
    """Whether the open folder is on this machine, so the picker can start there."""
    return isinstance(session.backend, LocalBackend)


def _range_response(data: bytes, filename: str, request: Request) -> Response:
    """Serve bytes with Range support, so the audio element can seek."""
    media_type = "audio/wav"
    total = len(data)
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    range_header = request.headers.get("range")
    if not range_header or not range_header.startswith("bytes="):
        return Response(data, media_type=media_type, headers=headers)

    spec = range_header[len("bytes="):].split(",")[0].strip()
    start_s, _, end_s = spec.partition("-")
    try:
        if start_s:
            start = int(start_s)
            end = int(end_s) if end_s else total - 1
        else:  # suffix range: last N bytes
            start = max(0, total - int(end_s))
            end = total - 1
    except ValueError:
        return Response(data, media_type=media_type, headers=headers)

    start = max(0, min(start, total - 1 if total else 0))
    end = max(start, min(end, total - 1 if total else 0))
    headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return Response(data[start: end + 1], status_code=206,
                    media_type=media_type, headers=headers)


def _pattern_payload(pattern) -> dict | None:
    if pattern is None:
        return None
    matched, total, example = pattern
    return {"matched": matched, "total": total, "example": example}


def create_app(workspace: Workspace, config: ReviewConfig,
               token: str | None = None) -> FastAPI:
    """Build the app around a workspace, with or without a folder open in it."""
    app = FastAPI(title="Segment Reviewer", version=__version__, docs_url=None,
                  redoc_url=None)
    app.state.workspace = workspace
    app.state.config = config
    app.state.token = token
    #: How the open folder's names were read — worked out once when it opened.
    app.state.pattern = None

    def current() -> ReviewSession:
        """The open session; every clip-level call needs one."""
        session = workspace.session
        if session is None:
            raise HTTPException(status_code=409, detail="no segments folder is open")
        return session

    # ── access token ─────────────────────────────────────────────────────────
    def _authorized(request: Request) -> bool:
        if not token:
            return True
        given = (
            request.query_params.get("token")
            or request.headers.get(TOKEN_HEADER)
            or request.cookies.get(TOKEN_COOKIE)
        )
        return bool(given) and secrets.compare_digest(given, token)

    @app.middleware("http")
    async def _guard(request: Request, call_next):
        if request.url.path.startswith("/health") or _authorized(request):
            response = await call_next(request)
            if request.url.path.startswith("/static/"):
                # Revalidate on every load (a cheap 304 when unchanged). Without
                # it a browser keeps a heuristically "fresh" app.js for days, and
                # after an upgrade the new page runs the old script against an
                # API that no longer has the endpoints it calls.
                response.headers["Cache-Control"] = "no-cache"
            if token and request.query_params.get("token") == token:
                response.set_cookie(
                    TOKEN_COOKIE, token, httponly=True, samesite="lax", path="/"
                )
            return response
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return Response("Access token required.", status_code=401,
                        media_type="text/plain")

    # ── pages ────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def index(request: Request):
        # Drop the token from the address bar once the cookie is set, so the URL
        # can be copied around without leaking it into a browser history entry.
        if token and request.query_params.get("token") == token:
            redirect = RedirectResponse("/", status_code=303)
            redirect.set_cookie(TOKEN_COOKIE, token, httponly=True,
                                samesite="lax", path="/")
            return redirect
        return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-store"})

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"ok": True, "version": __version__}

    # ── API ──────────────────────────────────────────────────────────────────
    @app.get("/api/bootstrap")
    async def bootstrap():
        return {
            "version": __version__,
            "languages": i18n.language_names(),
            "lang": config.lang,
            "multi_label": config.multi_label,
            "outcomes": list(OUTCOMES),
            "spec_defaults": {
                "type": config.spec_type,
                "fmin": config.freq_min_hz,
                "fmax": config.freq_max_hz,
                "db": config.db_min,
            },
            "state": _state_payload(workspace),
            "pattern": _pattern_payload(app.state.pattern),
        }

    @app.get("/api/i18n/{lang}")
    async def translations(lang: str):
        code = i18n.normalize(lang)
        return {"lang": code, "bundle": i18n.bundle(code)}

    @app.get("/api/state")
    async def state():
        return _state_payload(workspace)

    @app.post("/api/open")
    async def open_folder(body: OpenBody):
        """Open another segments folder, replacing the one under review."""
        try:
            opened = workspace.open(body.path)
        except OpenError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - shown to the reviewer verbatim
            raise HTTPException(status_code=400, detail=f"could not open {body.path}: {exc}") from exc
        app.state.pattern = opened.pattern
        return {**_state_payload(workspace), "pattern": _pattern_payload(opened.pattern)}

    @app.get("/api/browse")
    async def browse_folders(path: str = ""):
        """Folders on the machine the reviewer runs on, for the folder picker."""
        session = workspace.session
        start = None
        if session is not None and parse_local(session):
            start = session.backend.root
        try:
            return browse(path, start=start)
        except OpenError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/rescan")
    async def rescan():
        current().rescan()
        return _state_payload(workspace)

    @app.post("/api/nav")
    async def nav(body: NavBody):
        session = current()
        if body.index is not None:
            session.goto(body.index)
        else:
            session.navigate(body.delta)
        return _state_payload(workspace)

    @app.get("/api/labels")
    async def labels():
        return _labels_payload(current())

    @app.post("/api/labels")
    async def edit_labels(body: LabelsBody):
        """Edit the label list from the GUI: replace it, or add/drop one label."""
        session = current()
        if body.labels is not None:
            session.labels.replace(body.labels)
        if body.add:
            session.labels.add(body.add)
        if body.remove:
            session.labels.remove(body.remove)
        return {**_labels_payload(session), "state": _state_payload(workspace)}

    @app.post("/api/review")
    async def review(body: ReviewBody):
        session = current()
        try:
            result = session.review(body.labels, unsure=body.unsure, relpath=body.relpath)
        except StaleSegment as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 - shown to the reviewer verbatim
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {**_state_payload(workspace), **result}

    @app.get("/api/spectrogram")
    async def spectrogram(
        index: int = Query(0, ge=0),
        type: str = Query("mel", pattern=f"^({'|'.join(SPEC_TYPES)})$"),
        fmin: int = Query(0, ge=0, le=96000),
        fmax: int = Query(0, ge=0, le=96000),
        db: int = Query(-80, ge=-120, le=-20),
    ):
        session = current()
        try:
            png = session.spectrogram(index, spec_type=type, fmin=fmin, fmax=fmax,
                                      db_min=db)
        except IndexError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SpectrogramError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return Response(png, media_type="image/png",
                        headers={"Cache-Control": "no-store"})

    @app.get("/api/audio")
    async def audio(request: Request, index: int = Query(0, ge=0)):
        session = current()
        try:
            data, filename = session.audio_bytes(index)
        except IndexError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _range_response(data, filename, request)

    return app
