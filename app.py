"""WikiSTAR v2 application entry point.

Run locally:   uv run uvicorn app:app --reload
API docs:      http://localhost:8000/docs

Toolforge (classic python webservice, ~/www/python/src): uwsgi speaks
WSGI only, so point it at the `application` callable below
(uwsgi.ini: callable = application). With the build service or any
ASGI server, use `app` directly.
"""
import httpx

from contextlib import asynccontextmanager

from a2wsgi import ASGIMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import ROOT_DIR, settings
from db import Base, engine
from routers import admin, auth, campaigns, claims, reviews, submissions

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Dev convenience; production schema changes go through Alembic.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="WikiSTAR", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=settings.session_cookie_secure,
    same_site="lax",
)

for router_module in (auth, campaigns, submissions, reviews, claims, admin):
    app.include_router(router_module.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version}


# ---- serve the built SPA ---------------------------------------------------
DIST = ROOT_DIR / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (DIST / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(DIST):
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")


# WSGI entry point for Toolforge's uwsgi-based python webservice.
application = ASGIMiddleware(app)
